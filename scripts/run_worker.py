from __future__ import annotations

import argparse
import os
import socket
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


def _probe_redis(redis_url: str) -> tuple[bool, str]:
    try:
        from redis import Redis

        client = Redis.from_url(
            redis_url,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=False,
        )
        client.ping()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the Muni-Pal Celery worker.")
    parser.add_argument("--loglevel", default="info")
    parser.add_argument("--queues", default="default,artifacts,deliverables,extraction")
    parser.add_argument("--pool", default=None)
    parser.add_argument("--hostname", default=None)
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        print(
            "[munipal] Python 3.11 or newer is required to run the worker.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    from munipal.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    if not settings.use_sqlite and not _probe_tcp(settings.postgres_host, settings.postgres_port):
        print(
            "[munipal] PostgreSQL is not reachable. Start the database before the Celery worker.",
            file=sys.stderr,
            flush=True,
        )
        return 1

    ok, detail = _probe_redis(settings.redis_connection_url)
    if not ok:
        print(
            f"[munipal] Redis is not ready for Celery: {detail}",
            file=sys.stderr,
            flush=True,
        )
        return 1

    redis_target = urlparse(settings.redis_connection_url)
    worker_pool = args.pool or ("solo" if os.name == "nt" else "prefork")

    print(f"[munipal] Python executable: {sys.executable}", flush=True)
    print(
        f"[munipal] Redis ready: {redis_target.scheme}://{redis_target.hostname}:{redis_target.port or 'default'}",
        flush=True,
    )
    if os.name == "nt" and worker_pool == "solo":
        print(
            "[munipal] Windows detected. Using Celery's solo pool for local stability.",
            flush=True,
        )

    command = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "munipal.workers.celery_app",
        "worker",
        "--loglevel",
        args.loglevel,
        "--queues",
        args.queues,
        "--pool",
        worker_pool,
    ]
    if args.hostname:
        command.extend(["--hostname", args.hostname])

    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=_with_pythonpath(os.environ.copy()),
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
