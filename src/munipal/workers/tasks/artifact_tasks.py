"""
Artifact processing tasks.

Per spec (WP2): Artifact Vault & Ingestion
- Accept messy inputs
- Normalize into immutable chunks
- Preserve provenance
"""

import logging
from pathlib import Path

from munipal.config import get_settings
from munipal.core.models import Artifact, Chunk
from munipal.db.session import get_sync_session
from munipal.services.chunking.base import ChunkData
from munipal.services.chunking.excel_chunker import CSVChunker, ExcelChunker
from munipal.services.chunking.pdf_chunker import PDFChunker
from munipal.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, name="munipal.workers.tasks.artifact_tasks.process_artifact")
def process_artifact(self, artifact_id: str) -> dict:
    """
    Process an uploaded artifact into chunks.

    This task:
    1. Reads the artifact file from storage
    2. Determines the file type and appropriate chunker
    3. Extracts content into immutable chunks
    4. Saves chunks to database with content hashes

    Per spec: Chunks are page-based for PDFs, sheet-based for Excel.
    """
    logger.info(f"Processing artifact: {artifact_id}")

    session = get_sync_session()
    try:
        # Get artifact from database
        artifact = session.get(Artifact, artifact_id)
        if not artifact:
            logger.error(f"Artifact not found: {artifact_id}")
            return {
                "artifact_id": artifact_id,
                "status": "error",
                "error": "Artifact not found",
                "chunks_created": 0,
            }

        # Build full storage path
        storage_base = Path(settings.artifact_storage_path)
        file_path = storage_base / artifact.storage_path

        if not file_path.exists():
            logger.error(f"Artifact file not found: {file_path}")
            artifact.processing_error = "File not found in storage"
            session.commit()
            return {
                "artifact_id": artifact_id,
                "status": "error",
                "error": "File not found",
                "chunks_created": 0,
            }

        # Select appropriate chunker based on artifact type
        artifact_type = artifact.artifact_type.lower()
        chunker = get_chunker_for_type(artifact_type)

        if not chunker:
            logger.warning(f"No chunker available for type: {artifact_type}")
            artifact.is_processed = True
            artifact.processing_error = f"No chunker for type: {artifact_type}"
            session.commit()
            return {
                "artifact_id": artifact_id,
                "status": "skipped",
                "error": f"Unsupported type: {artifact_type}",
                "chunks_created": 0,
            }

        # Extract chunks
        try:
            chunk_data_list = chunker.chunk(file_path)
        except Exception as e:
            logger.error(f"Chunking failed for {artifact_id}: {e}")
            artifact.processing_error = str(e)
            session.commit()
            return {
                "artifact_id": artifact_id,
                "status": "error",
                "error": str(e),
                "chunks_created": 0,
            }

        # Save chunks to database
        chunks_created = 0
        for chunk_data in chunk_data_list:
            chunk = create_chunk_from_data(artifact_id, chunk_data)
            session.add(chunk)
            chunks_created += 1

        # Mark artifact as processed
        artifact.is_processed = True
        artifact.processing_error = None
        session.commit()

        logger.info(f"Successfully processed artifact {artifact_id}: {chunks_created} chunks")

        return {
            "artifact_id": artifact_id,
            "status": "success",
            "chunks_created": chunks_created,
        }

    except Exception as e:
        logger.error(f"Unexpected error processing artifact {artifact_id}: {e}")
        session.rollback()
        return {
            "artifact_id": artifact_id,
            "status": "error",
            "error": str(e),
            "chunks_created": 0,
        }
    finally:
        session.close()


def get_chunker_for_type(artifact_type: str):
    """Get the appropriate chunker for an artifact type."""
    chunkers = {
        "pdf": PDFChunker(),
        "xlsx": ExcelChunker(),
        "xls": ExcelChunker(),
        "csv": CSVChunker(),
        # DOCX and TXT could be added here
        # "docx": DocxChunker(),
        # "txt": TextChunker(),
    }
    return chunkers.get(artifact_type)


def create_chunk_from_data(artifact_id: str, chunk_data: ChunkData) -> Chunk:
    """Create a Chunk model instance from ChunkData."""
    return Chunk(
        artifact_id=artifact_id,
        chunk_type=chunk_data.chunk_type,
        sequence_number=chunk_data.sequence_number,
        page_number=chunk_data.page_number,
        sheet_name=chunk_data.sheet_name,
        section_title=chunk_data.section_title,
        text_content=chunk_data.text_content,
        content_hash=chunk_data.content_hash,
        has_image=chunk_data.has_image,
    )


@celery_app.task(bind=True, name="munipal.workers.tasks.artifact_tasks.reprocess_artifact")
def reprocess_artifact(self, artifact_id: str) -> dict:
    """
    Reprocess an artifact, deleting existing chunks first.

    Useful for re-running chunking after updates to chunker logic.
    """
    logger.info(f"Reprocessing artifact: {artifact_id}")

    session = get_sync_session()
    try:
        # Delete existing chunks
        artifact = session.get(Artifact, artifact_id)
        if artifact:
            # Delete existing chunks for this artifact
            session.query(Chunk).filter(Chunk.artifact_id == artifact_id).delete()
            artifact.is_processed = False
            session.commit()

        # Close session before calling process_artifact
        session.close()

        # Process fresh
        return process_artifact(artifact_id)

    except Exception as e:
        logger.error(f"Error reprocessing artifact {artifact_id}: {e}")
        session.rollback()
        session.close()
        return {
            "artifact_id": artifact_id,
            "status": "error",
            "error": str(e),
            "chunks_created": 0,
        }
