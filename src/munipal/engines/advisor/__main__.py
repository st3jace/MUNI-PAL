"""Entry point for the Municipal Advisor engine.

    python -m munipal.engines.advisor          # starts API server
    python -m munipal.engines.advisor chat     # interactive CLI
    python -m munipal.engines.advisor sessions # list sessions
"""

import sys

if len(sys.argv) > 1 and sys.argv[1] in ("chat", "sessions", "delete"):
    from .cli import cli
    cli()
else:
    from .api import main
    main()
