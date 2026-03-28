"""Allow running as: python -m munipal.engines.bank_analyzer [api|cli ...]"""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "api":
    sys.argv.pop(1)  # Remove "api" from args before uvicorn parses them
    from .api import main
    main()
else:
    from .cli import main
    main()
