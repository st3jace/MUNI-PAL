"""
PDF chunking service.

Per spec: PDF chunks are page-based with preserved page numbers.
"""

import logging
from pathlib import Path

from pypdf import PdfReader

from munipal.services.chunking.base import BaseChunker, ChunkData

logger = logging.getLogger(__name__)


class PDFChunker(BaseChunker):
    """
    Extracts chunks from PDF documents.

    Each page becomes one chunk with:
    - page_number preserved
    - text_content extracted
    - content_hash computed for deduplication
    """

    def chunk(self, file_path: Path) -> list[ChunkData]:
        """
        Extract page-based chunks from a PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of ChunkData, one per page
        """
        chunks: list[ChunkData] = []

        try:
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)

            logger.info(f"Processing PDF with {total_pages} pages: {file_path.name}")

            for page_num, page in enumerate(reader.pages, start=1):
                # Extract text from page
                try:
                    raw_text = page.extract_text()
                    text_content = self.clean_text(raw_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    text_content = None

                # Check if page has images
                has_image = self._page_has_images(page)

                # Generate content hash
                hash_content = text_content or f"page_{page_num}_no_text"
                content_hash = self.compute_hash(hash_content)

                chunk = ChunkData(
                    chunk_type="page",
                    sequence_number=page_num - 1,  # 0-indexed sequence
                    text_content=text_content,
                    content_hash=content_hash,
                    page_number=page_num,
                    has_image=has_image,
                    metadata={
                        "total_pages": total_pages,
                        "has_text": text_content is not None,
                        "text_length": len(text_content) if text_content else 0,
                    },
                )
                chunks.append(chunk)

            logger.info(f"Extracted {len(chunks)} chunks from PDF")

        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            raise ValueError(f"PDF processing failed: {e}")

        return chunks

    def _page_has_images(self, page) -> bool:
        """Check if a PDF page contains images."""
        try:
            # Check for XObject images
            if "/XObject" in page["/Resources"]:
                xobject = page["/Resources"]["/XObject"].get_object()
                for obj in xobject:
                    if xobject[obj]["/Subtype"] == "/Image":
                        return True
        except Exception:
            # If we can't determine, assume no images
            pass
        return False


class PDFChunkerWithOCR(PDFChunker):
    """
    PDF chunker with OCR fallback for scanned documents.

    TODO: Implement OCR using pytesseract or similar
    when text extraction yields empty results.
    """

    def chunk(self, file_path: Path) -> list[ChunkData]:
        """Extract chunks, falling back to OCR for image-heavy pages."""
        chunks = super().chunk(file_path)

        # TODO: For chunks with no text but has_image=True,
        # run OCR to extract text from images
        # This would use pytesseract or pdf2image + OCR

        return chunks
