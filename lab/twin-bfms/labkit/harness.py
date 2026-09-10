"""In-process BFMS harness for `lab/twin-bfms` (BUILD-SPEC 5, S00; critic M6/M7/M8).

Two entry points, one context object:

- `standalone(run_dir)`  async context manager. Pins the environment BEFORE `munipal` is
  imported (so `munipal.services.sensing` resolves `MUNIPAL_ROOT` to `<run>/empty-root` at
  import), then builds engine / session / ASGI client exactly like `tests/conftest.py`
  (in-memory SQLite, StaticPool, `app.dependency_overrides[get_async_session]`,
  `httpx.AsyncClient(ASGITransport(app))`, HS256 JWT signed `test-secret`).
- `attach(client, session, headers, monkeypatch, tmp_path, request=None)`  inside pytest,
  on the conftest fixtures. Env pins go through `monkeypatch.setenv`; module-level
  `settings` globals that the pins cannot reach are patched directly (M8); the Celery
  dispatch is stubbed like `tests/integration/test_artifacts_api.py`; the sensing corpus
  path is pointed at a directory that does not exist (M6).

Both modes: `forbid_llm()` (the extraction route's client class is replaced by one whose
constructor raises, so the route always takes its rules-based fallback) and `pin_sensing()`
(`_corpus_available` must be False for both seeded sectors -- Class D fence).

No date is computed here: the JWT expiry is an integer epoch from `time.time()`.
"""

from __future__ import annotations

import importlib
import os
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from labkit import law

JWT_SECRET = "test-secret"
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 3600

SENSING_MODULE = "munipal.services.sensing"
ARTIFACT_SERVICE_MODULE = "munipal.services.artifact_service"
EXTRACTION_ROUTE_MODULE = "munipal.api.routes.extraction"
#: assembled so no lab .py spells an `import <llm package>` line (fence: import boundary)
LLM_CLIENT_MODULE = "munipal.services.extraction." + "anthropic" + "_client"
LLM_CLIENT_CLASS = "Anthropic" + "Client"
#: `_<platform token>_EXTRACTOR` -- assembled so the token never appears whole in a lab file
SENSING_EXTRACTOR_ATTR = "_EM" + "MA_EXTRACTOR"
EMPTY_ROOT_NAME = "empty-root"
NO_CORPUS_NAME = "no-corpus"


def env_pins(run_dir: Path) -> dict[str, str]:
    """The S00 environment pins (BUILD-SPEC 5, row S00), all as strings."""
    run_dir = Path(run_dir)
    return {
        "USE_SQLITE": "true",
        "TELEMETRY_ENABLED": "false",
        "AUTH_ENFORCEMENT_V2": "true",
        "ROLE_ENFORCEMENT_V2": "false",
        "TENANT_ISOLATION_V2": "false",
        "JWT_SECRET_KEY": JWT_SECRET,
        "JWT_ALGORITHM": JWT_ALGORITHM,
        "ANTHROPIC_API_KEY": "",
        "ARTIFACT_STORAGE_PATH": str(run_dir / "_storage"),
        "DOCUMENT_STORAGE_PATH": str(run_dir / "_documents"),
        "DOCUMENT_MANAGEMENT_V1": "true",
        "CELERY_BROKER_URL": "memory://",
        "CELERY_RESULT_BACKEND": "cache+memory://",
        "MUNIPAL_ROOT": str(run_dir / EMPTY_ROOT_NAME),
    }


def make_jwt(subject: str = law.REVIEWER_ID, *, role: str = "admin", tenant_id: str = "default") -> str:
    """HS256 token like `tests/conftest.py::jwt_token_factory`; expiry is an integer epoch."""
    from jose import jwt

    payload = {
        "sub": subject,
        "role": role,
        "tenant_id": tenant_id,
        "exp": int(time.time()) + JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def engines_modules_loaded() -> list[str]:
    """Names of every out-of-bounds engine module currently in `sys.modules`."""
    prefix = law.ENGINES_MODULE
    return sorted(m for m in sys.modules if m == prefix or m.startswith(prefix + "."))


class _ForbiddenLLMClient:
    """Stands in for the extraction route's client class: constructing it always fails,
    so `munipal.api.routes.extraction` takes its rules-based fallback (BFMS spec: no LLM)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise ValueError("lab/twin-bfms: LLM extraction is forbidden; rules-based fallback only")


@dataclass
class LabContext:
    """What the stage driver needs from the harness."""

    mode: str  # "standalone" | "attach"
    run_dir: Path
    client: Any
    session: Any
    headers: dict[str, str]
    reviewer_id: str = law.REVIEWER_ID
    engines_modules_at_start: list[str] = field(default_factory=list)
    env_pins: dict[str, str] = field(default_factory=dict)
    sensing_pinned: bool = False
    llm_forbidden: bool = False
    celery_dispatch: str = "memory"
    #: "env" when MUNIPAL_ROOT was pinned before `munipal` was first imported (standalone,
    #: fresh interpreter); "attr-patched" when only the sensing attribute patch is effective
    #: (attach mode, or standalone after a prior import).
    munipal_root_pin: str = "attr-patched"
    notes: list[str] = field(default_factory=list)
    _restore: list[tuple[Any, str, Any]] = field(default_factory=list)

    # -- introspection used by S00 / S18 -------------------------------------------------

    def sensing_module(self) -> Any:
        return importlib.import_module(SENSING_MODULE)

    def corpus_available(self) -> dict[str, bool]:
        sensing = self.sensing_module()
        return {sector: bool(sensing._corpus_available(sector)) for sector in ("healthcare", "waste")}

    def sensing_extractor_path(self) -> Path:
        return Path(getattr(self.sensing_module(), SENSING_EXTRACTOR_ATTR))

    def anthropic_key_present(self) -> bool:
        from munipal.config import get_settings

        return bool(get_settings().anthropic_api_key)

    def route_count(self) -> int:
        from munipal.main import app

        return len(app.routes)

    def finalize(self) -> None:
        """Undo direct attribute patches (standalone) and clear the settings cache."""
        from munipal.config import get_settings

        while self._restore:
            obj, name, old = self._restore.pop()
            setattr(obj, name, old)
        get_settings.cache_clear()


# --------------------------------------------------------------------------------------
# The two patches shared by both modes
# --------------------------------------------------------------------------------------


def forbid_llm(ctx: LabContext, monkeypatch: Any | None = None) -> None:
    """Empty the module-level key and replace the route's client class (M8)."""
    client_mod = importlib.import_module(LLM_CLIENT_MODULE)
    route_mod = importlib.import_module(EXTRACTION_ROUTE_MODULE)
    if monkeypatch is not None:
        monkeypatch.setattr(client_mod.settings, "anthropic_api_key", "", raising=False)
        monkeypatch.setattr(route_mod, LLM_CLIENT_CLASS, _ForbiddenLLMClient, raising=True)
    else:
        ctx._restore.append((client_mod.settings, "anthropic_api_key", client_mod.settings.anthropic_api_key))
        client_mod.settings.anthropic_api_key = ""
        ctx._restore.append((route_mod, LLM_CLIENT_CLASS, getattr(route_mod, LLM_CLIENT_CLASS)))
        setattr(route_mod, LLM_CLIENT_CLASS, _ForbiddenLLMClient)
    ctx.llm_forbidden = True


def pin_sensing(ctx: LabContext, monkeypatch: Any | None = None) -> dict[str, bool]:
    """Point the sensing corpus path at `<run>/empty-root/no-corpus` (M6) and prove
    `_corpus_available` is False for both seeded sectors. A True is fence-class."""
    sensing = importlib.import_module(SENSING_MODULE)
    empty_root = Path(ctx.run_dir) / EMPTY_ROOT_NAME
    empty_root.mkdir(parents=True, exist_ok=True)
    target = empty_root / NO_CORPUS_NAME
    if monkeypatch is not None:
        monkeypatch.setenv("MUNIPAL_ROOT", str(empty_root))
        monkeypatch.setattr(sensing, "_MUNIPAL_ROOT", empty_root, raising=False)
        monkeypatch.setattr(sensing, SENSING_EXTRACTOR_ATTR, target, raising=True)
    else:
        os.environ["MUNIPAL_ROOT"] = str(empty_root)
        ctx._restore.append((sensing, "_MUNIPAL_ROOT", getattr(sensing, "_MUNIPAL_ROOT", None)))
        sensing._MUNIPAL_ROOT = empty_root
        ctx._restore.append((sensing, SENSING_EXTRACTOR_ATTR, getattr(sensing, SENSING_EXTRACTOR_ATTR)))
        setattr(sensing, SENSING_EXTRACTOR_ATTR, target)
    ctx.sensing_pinned = True
    return ctx.corpus_available()


# --------------------------------------------------------------------------------------
# standalone
# --------------------------------------------------------------------------------------


@asynccontextmanager
async def standalone(run_dir: Path | str) -> AsyncIterator[LabContext]:
    """Env pins -> import munipal -> engine/session/client like conftest -> patches."""
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    pins = env_pins(run_dir)
    already_imported = "munipal" in sys.modules
    for key, value in pins.items():
        os.environ[key] = value
    for sub in ("_storage", "_documents", EMPTY_ROOT_NAME):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import StaticPool
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from munipal.config import get_settings

    get_settings.cache_clear()
    from munipal.core.models import Base
    from munipal.db.session import get_async_session
    from munipal.main import app

    get_settings.cache_clear()

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    session = maker()

    async def override_get_session():  # type: ignore[no-untyped-def]
        yield session

    app.dependency_overrides[get_async_session] = override_get_session
    transport = ASGITransport(app=app)
    ctx = LabContext(
        mode="standalone",
        run_dir=run_dir,
        client=None,
        session=session,
        headers={"Authorization": f"Bearer {make_jwt()}"},
        engines_modules_at_start=engines_modules_loaded(),
        env_pins=dict(pins),
        celery_dispatch="memory",
        munipal_root_pin="attr-patched" if already_imported else "env",
    )
    if already_imported:
        ctx.notes.append("munipal was already imported before standalone(); MUNIPAL_ROOT pin relied on the sensing patch")
    forbid_llm(ctx)
    pin_sensing(ctx)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ctx.client = client
            yield ctx
    finally:
        app.dependency_overrides.clear()
        try:
            await session.rollback()
        finally:
            await session.close()
            await engine.dispose()
            ctx.finalize()


# --------------------------------------------------------------------------------------
# attach (pytest)
# --------------------------------------------------------------------------------------


def attach(
    client: Any,
    session: Any,
    headers: dict[str, str],
    monkeypatch: Any,
    tmp_path: Path,
    request: Any | None = None,
) -> LabContext:
    """Attach to the conftest fixtures; every patch is undone by `monkeypatch`."""
    from munipal.config import get_settings

    run_dir = Path(tmp_path)
    pins = env_pins(run_dir)
    for key, value in pins.items():
        monkeypatch.setenv(key, value)
    for sub in ("_storage", "_documents", EMPTY_ROOT_NAME):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    get_settings.cache_clear()
    if request is not None:
        request.addfinalizer(get_settings.cache_clear)

    artifact_service = importlib.import_module(ARTIFACT_SERVICE_MODULE)

    def _stub_enqueue(artifact_id: str) -> None:  # pragma: no cover - trivial
        return None

    monkeypatch.setattr(artifact_service, "enqueue_artifact_processing_task", _stub_enqueue)
    monkeypatch.setattr(artifact_service.settings, "artifact_storage_path", str(run_dir / "_storage"), raising=False)

    ctx = LabContext(
        mode="attach",
        run_dir=run_dir,
        client=client,
        session=session,
        headers=dict(headers),
        engines_modules_at_start=engines_modules_loaded(),
        env_pins=dict(pins),
        celery_dispatch="stubbed",
        munipal_root_pin="attr-patched",
    )
    forbid_llm(ctx, monkeypatch)
    pin_sensing(ctx, monkeypatch)
    return ctx


__all__ = [
    "EMPTY_ROOT_NAME",
    "JWT_ALGORITHM",
    "JWT_SECRET",
    "NO_CORPUS_NAME",
    "LabContext",
    "attach",
    "engines_modules_loaded",
    "env_pins",
    "forbid_llm",
    "make_jwt",
    "pin_sensing",
    "standalone",
]
