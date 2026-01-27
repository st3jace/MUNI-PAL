"""
Base chunker interface.

Per spec: Chunks are immutable evidence units with provenance.
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChunkData:
    """Data structure for a chunk before database insertion."""

    chunk_type: str  # page, sheet, section, image
    sequence_number: int
    text_content: str | None
    content_hash: str
    page_number: int | None = None
    sheet_name: str | None = None
    section_title: str | None = None
    has_image: bool = False
    metadata: dict | None = None


class BaseChunker(ABC):
    """
    Base class for document chunkers.

    All chunkers must:
    1. Extract content into immutable chunks
    2. Preserve provenance (page numbers, sheet names, etc.)
    3. Generate content hashes for deduplication
    """

    @abstractmethod
    def chunk(self, file_path: Path) -> list[ChunkData]:
        """
        Extract chunks from a file.

        Args:
            file_path: Path to the file to chunk

        Returns:
            List of ChunkData objects
        """
        pass

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def clean_text(text: str | None) -> str | None:
        """Clean and normalize extracted text."""
        if text is None:
            return None

        # Remove excessive whitespace
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Strip trailing whitespace but preserve leading for structure
            line = line.rstrip()
            # Skip completely empty lines in sequence
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)

        result = "\n".join(cleaned_lines).strip()
        return result if result else None
