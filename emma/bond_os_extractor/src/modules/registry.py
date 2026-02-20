"""Module registry and document router."""
from __future__ import annotations

import fnmatch
import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any

from .base import DocumentModule

logger = logging.getLogger("bond_os_extractor.modules.registry")


class ModuleRegistry:
    """Discovers and routes documents to the appropriate extraction module."""

    def __init__(self) -> None:
        self._modules: list[DocumentModule] = []

    @property
    def modules(self) -> list[DocumentModule]:
        return list(self._modules)

    def register(self, module: DocumentModule) -> None:
        """Register a document module."""
        if any(m.name == module.name for m in self._modules):
            logger.warning("Module %r already registered, skipping", module.name)
            return
        self._modules.append(module)
        logger.info("Registered module: %s", module.name)

    def auto_discover(self) -> None:
        """Discover and register all modules in the modules/ subpackages.

        Each subpackage must expose a `module` attribute (a DocumentModule
        instance) in its __init__.py to be auto-registered.
        """
        modules_dir = Path(__file__).parent
        for info in pkgutil.iter_modules([str(modules_dir)]):
            if not info.ispkg:
                continue
            try:
                pkg = importlib.import_module(f".{info.name}", package=__package__)
                mod_instance = getattr(pkg, "module", None)
                if mod_instance and isinstance(mod_instance, DocumentModule):
                    self.register(mod_instance)
                else:
                    logger.debug(
                        "Subpackage %s has no 'module' attribute, skipping", info.name
                    )
            except Exception as exc:
                logger.warning("Failed to import module %s: %s", info.name, exc)

    # Filenames containing these keywords are Official Statement documents
    # and should ALWAYS fall through to the OS extractor (return None).
    _OS_PRIORITY_KEYWORDS = [
        "official_statement",
        "remarketing_supplement",
        "supplement_to_official",
        "preliminary_official",
        "final_official",
    ]

    def route(
        self, filename: str, first_page_text: str = ""
    ) -> DocumentModule | None:
        """Route a document to the best matching module.

        Strategy:
        0. If filename indicates Official Statement, always return None (OS default)
        1. Check filename patterns (fast, handles 90%+ of EMMA docs)
        2. Use content-based matching via each module's matches() method
        3. Return the highest-confidence match above threshold, or None

        Args:
            filename: The PDF filename.
            first_page_text: Text from the first page (for content matching).

        Returns:
            The best matching module, or None if no module matches.
        """
        # OS-priority exclusion: these always go to the OS extractor
        fn_lower = filename.lower()
        if any(kw in fn_lower for kw in self._OS_PRIORITY_KEYWORDS):
            logger.debug("OS-priority file, skipping module routing: %s", filename)
            return None

        best_module: DocumentModule | None = None
        best_score: float = 0.0

        for mod in self._modules:
            # Quick filename pattern check
            pattern_score = 0.0
            for pattern in mod.file_patterns:
                if fnmatch.fnmatch(filename, pattern):
                    pattern_score = 0.9
                    break

            # Content-based check
            content_score = mod.matches(filename, first_page_text)

            # Take the higher of the two
            score = max(pattern_score, content_score)

            if score > best_score:
                best_score = score
                best_module = mod

        if best_score < 0.3:
            logger.debug("No module matched %s (best score: %.2f)", filename, best_score)
            return None

        logger.debug(
            "Routed %s -> %s (score: %.2f)", filename, best_module.name, best_score
        )
        return best_module

    def get_module(self, name: str) -> DocumentModule | None:
        """Get a module by name."""
        for mod in self._modules:
            if mod.name == name:
                return mod
        return None

    def list_modules(self) -> list[dict[str, Any]]:
        """List all registered modules."""
        return [
            {
                "name": m.name,
                "display_name": m.display_name,
                "patterns": m.file_patterns,
            }
            for m in self._modules
        ]


# Singleton registry
_registry: ModuleRegistry | None = None


def get_registry() -> ModuleRegistry:
    """Get the global module registry, auto-discovering modules on first call."""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
        _registry.auto_discover()
    return _registry
