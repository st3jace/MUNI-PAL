from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .pdf_reader import IngestionResult

logger = logging.getLogger("bond_os_extractor.section_detector")


class DocumentSection(BaseModel):
    section_id: str
    heading_text: str = ""
    start_page: int = 0
    end_page: int = 0
    text: str = ""
    subsections: list[DocumentSection] = Field(default_factory=list)


class SectionPattern(BaseModel):
    section_id: str
    patterns: list[str]
    priority: int = 50
    expected_location: str = "middle"


def load_section_patterns(config_path: Path) -> list[SectionPattern]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    patterns: list[SectionPattern] = []
    for section_id, cfg in data.get("sections", {}).items():
        patterns.append(SectionPattern(
            section_id=section_id,
            patterns=cfg.get("patterns", []),
            priority=cfg.get("priority", 50),
            expected_location=cfg.get("expected_location", "middle"),
        ))
    return sorted(patterns, key=lambda p: -p.priority)


def _is_heading_line(line: str) -> bool:
    """Heuristic: heading lines are typically short, uppercase, or centered."""
    stripped = line.strip()
    if not stripped or len(stripped) > 200:
        return False
    # All caps (at least 4 alpha chars)
    alpha_chars = [c for c in stripped if c.isalpha()]
    if len(alpha_chars) >= 4 and stripped == stripped.upper():
        return True
    return False


def _find_section_matches(
    pages: list[dict[str, Any]],
    patterns: list[SectionPattern],
) -> list[dict[str, Any]]:
    """Scan page text for section heading matches."""
    matches: list[dict[str, Any]] = []
    seen_sections: set[str] = set()

    for page_info in pages:
        page_num = page_info["page_number"]
        text = page_info["text"]
        lines = text.split("\n")

        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            for sp in patterns:
                if sp.section_id in seen_sections:
                    continue
                for pattern in sp.patterns:
                    if re.search(pattern, stripped):
                        matches.append({
                            "section_id": sp.section_id,
                            "heading_text": stripped,
                            "page_number": page_num,
                            "line_index": line_idx,
                            "priority": sp.priority,
                        })
                        seen_sections.add(sp.section_id)
                        break
                if sp.section_id in seen_sections:
                    break

    # Sort by page number, then line index
    matches.sort(key=lambda m: (m["page_number"], m["line_index"]))
    return matches


def _extract_section_text(
    pages: list[dict[str, Any]],
    start_page: int,
    end_page: int,
) -> str:
    """Get combined text from start_page to end_page (inclusive)."""
    parts: list[str] = []
    for page_info in pages:
        pn = page_info["page_number"]
        if start_page <= pn <= end_page:
            parts.append(page_info["text"])
    return "\n\n".join(parts)


def detect_sections(
    ingestion_result: IngestionResult,
    config_path: Path | None = None,
) -> list[DocumentSection]:
    """
    Detect OS document sections from extracted page text.
    Returns a list of DocumentSection objects ordered by appearance.
    """
    if config_path is None:
        from ..config import get_settings
        config_path = get_settings().configs_dir / "section_patterns.yaml"

    patterns = load_section_patterns(config_path)
    pages = [
        {"page_number": p.page_number, "text": p.text}
        for p in ingestion_result.pages
    ]

    if not pages:
        logger.warning("No pages to analyze for sections")
        return []

    matches = _find_section_matches(pages, patterns)
    if not matches:
        logger.warning("No section headings detected in %s", ingestion_result.source_file)
        # Return entire document as a single section
        return [DocumentSection(
            section_id="FULL_DOCUMENT",
            heading_text="(no sections detected)",
            start_page=1,
            end_page=ingestion_result.page_count,
            text=_extract_section_text(pages, 1, ingestion_result.page_count),
        )]

    # Build sections with start/end pages
    total_pages = ingestion_result.page_count
    sections: list[DocumentSection] = []

    for i, match in enumerate(matches):
        start_page = match["page_number"]
        if i + 1 < len(matches):
            # End page is the page before the next section starts
            next_start = matches[i + 1]["page_number"]
            next_line = matches[i + 1]["line_index"]
            # If next section starts on same page, share the page
            if next_start == start_page:
                end_page = start_page
            else:
                end_page = next_start - 1 if next_line == 0 else next_start
        else:
            end_page = total_pages

        section_text = _extract_section_text(pages, start_page, end_page)

        sections.append(DocumentSection(
            section_id=match["section_id"],
            heading_text=match["heading_text"],
            start_page=start_page,
            end_page=end_page,
            text=section_text,
        ))

    logger.info(
        "Detected %d sections in %s: %s",
        len(sections),
        ingestion_result.source_file,
        [s.section_id for s in sections],
    )
    return sections
