from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("bond_os_extractor.ingestion")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PageExtraction(BaseModel):
    page_number: int
    text: str = ""
    tables: list[list[list[str]]] = Field(default_factory=list)
    extraction_method: str = "none"
    confidence: float = 1.0


class PDFMetadata(BaseModel):
    title: str | None = None
    author: str | None = None
    creation_date: str | None = None
    is_locked: bool = False
    encryption_type: str | None = None


class IngestionResult(BaseModel):
    source_file: str
    source_hash: str
    extraction_method: str = "none"
    page_count: int = 0
    pages: list[PageExtraction] = Field(default_factory=list)
    metadata: PDFMetadata = Field(default_factory=PDFMetadata)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _page_has_text(text: str, min_chars: int = 50) -> bool:
    return len(text.strip()) >= min_chars


# ---------------------------------------------------------------------------
# Attempt 1 — pdfplumber
# ---------------------------------------------------------------------------

def _extract_with_pdfplumber(filepath: Path) -> IngestionResult | None:
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber not installed, skipping")
        return None

    pages: list[PageExtraction] = []
    try:
        with pdfplumber.open(filepath) as pdf:
            metadata = PDFMetadata(
                title=pdf.metadata.get("Title"),
                author=pdf.metadata.get("Author"),
                creation_date=pdf.metadata.get("CreationDate"),
                is_locked=getattr(pdf, "is_encrypted", False),
            )
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                tables_raw: list[list[list[str]]] = []
                try:
                    for tbl in (page.extract_tables() or []):
                        cleaned = [
                            [str(cell) if cell is not None else "" for cell in row]
                            for row in tbl
                        ]
                        tables_raw.append(cleaned)
                except Exception:
                    pass
                pages.append(PageExtraction(
                    page_number=i + 1,
                    text=text,
                    tables=tables_raw,
                    extraction_method="pdfplumber",
                    confidence=1.0,
                ))
    except Exception as exc:
        logger.debug("pdfplumber failed on %s: %s", filepath.name, exc)
        return None

    # Check if we got meaningful text
    total_text = sum(len(p.text.strip()) for p in pages)
    if total_text < 100:
        logger.debug("pdfplumber returned very little text (%d chars)", total_text)
        return None

    return IngestionResult(
        source_file=filepath.name,
        source_hash="",  # filled by caller
        extraction_method="pdfplumber",
        page_count=len(pages),
        pages=pages,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Attempt 2 — pymupdf (fitz)
# ---------------------------------------------------------------------------

def _extract_with_pymupdf(filepath: Path) -> IngestionResult | None:
    try:
        import fitz  # pymupdf
    except ImportError:
        logger.warning("pymupdf not installed, skipping")
        return None

    pages: list[PageExtraction] = []
    try:
        doc = fitz.open(filepath)
        metadata = PDFMetadata(
            title=doc.metadata.get("title"),
            author=doc.metadata.get("author"),
            creation_date=doc.metadata.get("creationDate"),
            is_locked=doc.is_encrypted,
            encryption_type=doc.metadata.get("encryption") if doc.is_encrypted else None,
        )
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text("text") or ""
            pages.append(PageExtraction(
                page_number=i + 1,
                text=text,
                tables=[],
                extraction_method="pymupdf",
                confidence=1.0,
            ))
        doc.close()
    except Exception as exc:
        logger.debug("pymupdf failed on %s: %s", filepath.name, exc)
        return None

    total_text = sum(len(p.text.strip()) for p in pages)
    if total_text < 100:
        logger.debug("pymupdf returned very little text (%d chars)", total_text)
        return None

    return IngestionResult(
        source_file=filepath.name,
        source_hash="",
        extraction_method="pymupdf",
        page_count=len(pages),
        pages=pages,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Attempt 3 — OCR fallback
# ---------------------------------------------------------------------------

def _ocr_page_image(page_pixmap_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(page_pixmap_bytes))
        return pytesseract.image_to_string(img) or ""
    except ImportError:
        logger.warning("pytesseract/Pillow not installed, OCR unavailable")
        return ""
    except Exception as exc:
        logger.debug("OCR failed: %s", exc)
        return ""


def _extract_with_ocr(filepath: Path) -> IngestionResult | None:
    try:
        import fitz
    except ImportError:
        logger.warning("pymupdf needed for OCR fallback image conversion")
        return None

    pages: list[PageExtraction] = []
    try:
        doc = fitz.open(filepath)
        metadata = PDFMetadata(
            title=doc.metadata.get("title"),
            author=doc.metadata.get("author"),
            is_locked=doc.is_encrypted,
        )
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            text = _ocr_page_image(img_bytes)
            pages.append(PageExtraction(
                page_number=i + 1,
                text=text,
                tables=[],
                extraction_method="ocr",
                confidence=0.75,
            ))
        doc.close()
    except Exception as exc:
        logger.debug("OCR extraction failed on %s: %s", filepath.name, exc)
        return None

    total_text = sum(len(p.text.strip()) for p in pages)
    if total_text < 50:
        return None

    return IngestionResult(
        source_file=filepath.name,
        source_hash="",
        extraction_method="ocr",
        page_count=len(pages),
        pages=pages,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Attempt 4 — Hybrid (text + OCR per page)
# ---------------------------------------------------------------------------

def _extract_hybrid(filepath: Path) -> IngestionResult | None:
    """Use text extraction where possible, OCR only for weak pages."""
    try:
        import fitz
    except ImportError:
        return None

    pages: list[PageExtraction] = []
    methods_used: set[str] = set()
    min_chars = 50

    try:
        doc = fitz.open(filepath)
        metadata = PDFMetadata(
            title=doc.metadata.get("title"),
            author=doc.metadata.get("author"),
            is_locked=doc.is_encrypted,
        )
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text("text") or ""

            if _page_has_text(text, min_chars):
                pages.append(PageExtraction(
                    page_number=i + 1,
                    text=text,
                    tables=[],
                    extraction_method="pymupdf",
                    confidence=1.0,
                ))
                methods_used.add("pymupdf")
            else:
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                ocr_text = _ocr_page_image(img_bytes)
                pages.append(PageExtraction(
                    page_number=i + 1,
                    text=ocr_text,
                    tables=[],
                    extraction_method="ocr",
                    confidence=0.75,
                ))
                methods_used.add("ocr")
        doc.close()
    except Exception as exc:
        logger.debug("Hybrid extraction failed on %s: %s", filepath.name, exc)
        return None

    method = "hybrid" if len(methods_used) > 1 else methods_used.pop() if methods_used else "none"
    return IngestionResult(
        source_file=filepath.name,
        source_hash="",
        extraction_method=method,
        page_count=len(pages),
        pages=pages,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def extract_pdf(filepath: Path) -> IngestionResult:
    """
    Cascading PDF extraction: pdfplumber -> pymupdf -> OCR -> hybrid.
    Verifies file integrity with SHA256 before and after.
    """
    filepath = Path(filepath).resolve()
    if not filepath.exists():
        raise FileNotFoundError(f"PDF not found: {filepath}")

    # SHA256 before processing
    hash_before = compute_sha256(filepath)
    logger.info("Ingesting %s (sha256: %s)", filepath.name, hash_before[:16])

    result: IngestionResult | None = None

    # Attempt 1 — pdfplumber
    result = _extract_with_pdfplumber(filepath)
    if result is not None:
        logger.info("pdfplumber succeeded for %s (%d pages)", filepath.name, result.page_count)

    # Attempt 2 — pymupdf
    if result is None:
        result = _extract_with_pymupdf(filepath)
        if result is not None:
            logger.info("pymupdf succeeded for %s (%d pages)", filepath.name, result.page_count)

    # Attempt 3 — hybrid (text + per-page OCR)
    if result is None:
        result = _extract_hybrid(filepath)
        if result is not None:
            logger.info("Hybrid extraction succeeded for %s (%d pages)", filepath.name, result.page_count)

    # Attempt 4 — full OCR
    if result is None:
        result = _extract_with_ocr(filepath)
        if result is not None:
            logger.info("OCR fallback succeeded for %s (%d pages)", filepath.name, result.page_count)

    # Final fallback
    if result is None:
        logger.error("All extraction methods failed for %s", filepath.name)
        result = IngestionResult(
            source_file=filepath.name,
            source_hash=hash_before,
            extraction_method="failed",
            page_count=0,
        )

    # SHA256 after processing — verify no modification
    hash_after = compute_sha256(filepath)
    assert hash_before == hash_after, (
        f"INTEGRITY VIOLATION: {filepath.name} was modified during extraction! "
        f"Before: {hash_before}, After: {hash_after}"
    )
    logger.info("Integrity verified for %s (file unchanged)", filepath.name)

    result.source_hash = hash_before
    return result
