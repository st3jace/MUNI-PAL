from __future__ import annotations

import argparse
import os
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

os.chdir(PROJECT_ROOT)


def _with_pythonpath(env: dict[str, str]) -> dict[str, str]:
    pythonpath = env.get("PYTHONPATH", "").strip()
    src_path = str(SRC_ROOT)
    if pythonpath:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{pythonpath}"
    else:
        env["PYTHONPATH"] = src_path
    return env


def _probe_tcp(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _resolve_sqlite_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def _describe_sqlite(sqlite_path: Path) -> None:
    if not sqlite_path.exists():
        print(
            f"[munipal] SQLite file does not exist yet: {sqlite_path}",
            file=sys.stderr,
            flush=True,
        )
        return

    try:
        with sqlite3.connect(sqlite_path) as conn:
            project_count = conn.execute("select count(*) from projects").fetchone()[0]
            playbook_count = conn.execute("select count(*) from playbooks").fetchone()[0]
    except sqlite3.Error as exc:
        print(f"[munipal] Could not inspect SQLite database: {exc}", file=sys.stderr, flush=True)
        return

    print(
        f"[munipal] SQLite workspace summary: {project_count} project(s), "
        f"{playbook_count} playbook(s)",
        flush=True,
    )
    if project_count == 0:
        print(
            "[munipal] WARNING: SQLite currently has no projects. "
            "If your working data lives in PostgreSQL, keep USE_SQLITE=false.",
            file=sys.stderr,
            flush=True,
        )


def _run_migrations(skip_migrations: bool) -> int:
    if skip_migrations:
        print("[munipal] Skipping Alembic migrations", flush=True)
        return 0

    print("[munipal] Applying Alembic migrations", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        env=_with_pythonpath(os.environ.copy()),
        check=False,
    )
    if result.returncode != 0:
        print(
            "[munipal] Alembic migration step failed. Backend startup aborted.",
            file=sys.stderr,
            flush=True,
        )
    return result.returncode


def _probe_redis(redis_url: str) -> tuple[bool, str]:
    try:
        from redis import Redis

        client = Redis.from_url(
            redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=False,
        )
        client.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the Muni-Pal backend.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--skip-migrations", action="store_true")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        print(
            "[munipal] Python 3.11 or newer is required to run the backend.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    if sys.version_info >= (3, 14):
        print(
            "[munipal] WARNING: Python 3.14 is outside the project baseline. "
            "A pinned 3.11 environment is recommended for the most stable dev runtime.",
            file=sys.stderr,
            flush=True,
        )

    from munipal.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    print(f"[munipal] Python executable: {sys.executable}", flush=True)
    print(f"[munipal] Starting backend on http://{args.host}:{args.port}", flush=True)

    if settings.use_sqlite:
        sqlite_path = _resolve_sqlite_path(settings.sqlite_path)
        print(f"[munipal] Database mode: SQLite ({sqlite_path})", flush=True)
        _describe_sqlite(sqlite_path)
    else:
        print(
            "[munipal] Database mode: PostgreSQL "
            f"({settings.postgres_user}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db})",
            flush=True,
        )
        if not _probe_tcp(settings.postgres_host, settings.postgres_port):
            print(
                "[munipal] PostgreSQL is not reachable. Start the Muni-Pal Docker stack "
                "or the shared Visibility Dashboard infrastructure before launching.",
                file=sys.stderr,
                flush=True,
            )
            return 1

        migration_exit = _run_migrations(skip_migrations=args.skip_migrations)
        if migration_exit != 0:
            return migration_exit

    try:
        redis_target = urlparse(settings.redis_connection_url)
        if redis_target.hostname:
            ok, detail = _probe_redis(settings.redis_connection_url)
            if ok:
                print(
                    f"[munipal] Redis ready: {redis_target.scheme}://{redis_target.hostname}:{redis_target.port or 'default'}",
                    flush=True,
                )
            else:
                print(
                    "[munipal] WARNING: Redis check failed. Background workers and async task flows "
                    f"may remain unavailable until Redis is configured correctly. ({detail})",
                    file=sys.stderr,
                    flush=True,
                )
    except Exception:
        pass

    import uvicorn

    uvicorn.run(
        "munipal.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(SRC_ROOT),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
