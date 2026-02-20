from __future__ import annotations

from typing import Any

from .results import go_to_page
from .search import execute_search
from .utils import is_session_healthy, logger


async def recover_results_session(page: Any, config: dict[str, Any], target_page: int) -> bool:
    try:
        await execute_search(page, config)
        await go_to_page(page, target_page)
        healthy, page_type = await is_session_healthy(page)
        ok = healthy and page_type in {"results_page", "unknown"}
        if ok:
            logger.info("Recovered session and returned to results page %s", target_page)
        return ok
    except Exception as exc:
        logger.error("Failed to recover results session for page %s: %s", target_page, exc)
        return False
