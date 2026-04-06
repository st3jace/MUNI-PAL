"""Make the ``src`` package importable from the project root.

Tests use ``from src.main import …`` which requires ``emma/emma_crawler``
on ``sys.path``.  This conftest ensures that regardless of the working
directory pytest is invoked from.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CRAWLER_ROOT = Path(__file__).resolve().parent
if str(_CRAWLER_ROOT) not in sys.path:
    sys.path.insert(0, str(_CRAWLER_ROOT))
