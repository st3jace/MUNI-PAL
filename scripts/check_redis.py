from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

os.chdir(PROJECT_ROOT)


def main() -> int:
    from redis import Redis

    from munipal.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    parsed = urlparse(settings.redis_connection_url)

    target = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 'default'}"
    print(f"[munipal] Checking Redis connection: {target}", flush=True)

    try:
        client = Redis.from_url(
            settings.redis_connection_url,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=False,
        )
        response = client.ping()
    except Exception as exc:
        print(f"[munipal] Redis connection failed: {exc}", file=sys.stderr, flush=True)
        return 1

    print(f"[munipal] Redis ping successful: {response}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
