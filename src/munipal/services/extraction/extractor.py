"""
Fact extractor service.

Orchestrates the extraction of facts from document chunks
using Claude and playbook-defined extractors.
"""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from munipal.services.extraction.anthropic_client import AnthropicClient
from munipal.services.extraction.response_parser import ExtractionResponseParser, ParsedFact

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of an extraction operation."""

    extractor_id: str
    chunk_id: str
    facts: list[ParsedFact]
    unfound_paths: list[str]
    warnings: list[dict]
    extraction_notes: str | None
    success: bool
    error: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "extractor_id": self.extractor_id,
            "chunk_id": self.chunk_id,
            "facts": [f.to_dict() for f in self.facts],
            "unfound_paths": self.unfound_paths,
            "warnings": self.warnings,
            "extraction_notes": self.extraction_notes,
            "success": self.success,
            "error": self.error,
        }


class FactExtractor:
    """
    Extracts structured facts from document chunks.

    Uses playbook-defined extractors with Claude to extract
    facts that map to canonical schema paths.
    """

    def __init__(
        self,
        client: AnthropicClient | None = None,
        parser: ExtractionResponseParser | None = None,
    ):
        """
        Initialize fact extractor.

        Args:
            client: Anthropic client (creates new if not provided)
            parser: Response parser (creates new if not provided)
        """
        self.client = client or AnthropicClient()
        self.parser = parser or ExtractionResponseParser()

    def extract_from_chunk(
        self,
        chunk_id: str,
        chunk_content: str,
        extractor_config: dict,
        schema_paths: list[dict] | None = None,
    ) -> ExtractionResult:
        """
        Extract facts from a single chunk using an extractor configuration.

        Args:
            chunk_id: ID of the chunk being processed
            chunk_content: Text content of the chunk
            extractor_config: Extractor definition from playbook
            schema_paths: Optional schema path definitions for validation

        Returns:
            ExtractionResult with parsed facts
        """
        extractor_id = extractor_config.get("extractor_id", "unknown")
        target_paths = extractor_config.get("target_schema_paths", [])

        logger.info(f"Running extractor {extractor_id} on chunk {chunk_id}")

        # Skip empty content
        if not chunk_content or not chunk_content.strip():
            logger.debug(f"Chunk {chunk_id} has no content, skipping")
            return ExtractionResult(
                extractor_id=extractor_id,
                chunk_id=chunk_id,
                facts=[],
                unfound_paths=target_paths,
                warnings=[],
                extraction_notes="Chunk has no text content",
                success=True,
            )

        try:
            # Build prompts
            system_prompt = extractor_config.get("system_prompt", self._default_system_prompt())
            prompt_template = extractor_config.get(
                "extraction_prompt_template",
                "Extract facts from the following content:\n\n{content}"
            )
            user_prompt = prompt_template.format(content=chunk_content)

            # Call Claude
            response = self.client.extract_with_schema(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_paths=target_paths,
            )

            # Parse response
            facts, unfound_paths, notes = self.parser.parse(response)

            # Validate against schema if provided
            warnings = []
            if schema_paths:
                facts, warnings = self.parser.validate_against_schema(facts, schema_paths)

            logger.info(f"Extracted {len(facts)} facts from chunk {chunk_id}")

            return ExtractionResult(
                extractor_id=extractor_id,
                chunk_id=chunk_id,
                facts=facts,
                unfound_paths=unfound_paths,
                warnings=warnings,
                extraction_notes=notes,
                success=True,
            )

        except Exception as e:
            logger.error(f"Extraction failed for chunk {chunk_id}: {e}")
            return ExtractionResult(
                extractor_id=extractor_id,
                chunk_id=chunk_id,
                facts=[],
                unfound_paths=target_paths,
                warnings=[],
                extraction_notes=None,
                success=False,
                error=str(e),
            )

    def extract_from_chunks(
        self,
        chunks: list[dict],
        extractor_config: dict,
        schema_paths: list[dict] | None = None,
    ) -> list[ExtractionResult]:
        """
        Extract facts from multiple chunks.

        Args:
            chunks: List of chunk dicts with 'id' and 'text_content'
            extractor_config: Extractor definition from playbook
            schema_paths: Optional schema path definitions

        Returns:
            List of ExtractionResults, one per chunk
        """
        results = []

        for chunk in chunks:
            chunk_id = chunk.get("id", "unknown")
            content = chunk.get("text_content", "")

            result = self.extract_from_chunk(
                chunk_id=str(chunk_id),
                chunk_content=content,
                extractor_config=extractor_config,
                schema_paths=schema_paths,
            )
            results.append(result)

        return results

    def run_all_extractors(
        self,
        chunks: list[dict],
        extractors: list[dict],
        schema_paths: list[dict] | None = None,
    ) -> dict[str, list[ExtractionResult]]:
        """
        Run all applicable extractors on chunks.

        Args:
            chunks: List of chunk dicts
            extractors: List of extractor configurations
            schema_paths: Schema path definitions

        Returns:
            Dict mapping extractor_id to list of results
        """
        all_results: dict[str, list[ExtractionResult]] = {}

        for extractor in extractors:
            extractor_id = extractor.get("extractor_id", "unknown")

            # Check if extractor requires full document
            if extractor.get("requires_full_document", False):
                # Concatenate all chunk content
                full_content = "\n\n---PAGE BREAK---\n\n".join(
                    c.get("text_content", "") for c in chunks if c.get("text_content")
                )
                combined_chunk = {
                    "id": "combined",
                    "text_content": full_content,
                }
                results = self.extract_from_chunks(
                    chunks=[combined_chunk],
                    extractor_config=extractor,
                    schema_paths=schema_paths,
                )
            else:
                results = self.extract_from_chunks(
                    chunks=chunks,
                    extractor_config=extractor,
                    schema_paths=schema_paths,
                )

            all_results[extractor_id] = results

        return all_results

    def _default_system_prompt(self) -> str:
        """Default system prompt for extraction."""
        return """You are an expert municipal bond analyst extracting structured information from project documents.

Your task is to extract specific facts from the provided document content.

CRITICAL RULES:
1. Only extract facts that are EXPLICITLY stated in the document
2. Never infer, estimate, or make assumptions about missing values
3. For each fact, provide the exact quote from the document as evidence
4. Assign confidence scores based on how clearly the information is stated:
   - 0.90-1.00: Explicitly stated with clear, unambiguous language
   - 0.75-0.89: Stated but may require minor interpretation
   - 0.60-0.74: Implied or requires context to understand
   - Below 0.60: Uncertain, flag for human review
5. If a value cannot be found, do not fabricate it

Return your response as valid JSON."""


class BatchExtractor:
    """
    Handles batch extraction jobs across multiple artifacts.

    Coordinates extraction, deduplication, and conflict detection.
    """

    def __init__(self, extractor: FactExtractor | None = None):
        """Initialize batch extractor."""
        self.extractor = extractor or FactExtractor()

    def extract_from_artifact(
        self,
        artifact_chunks: list[dict],
        playbook_config: dict,
    ) -> dict[str, Any]:
        """
        Extract all facts from an artifact's chunks.

        Args:
            artifact_chunks: List of chunks from an artifact
            playbook_config: Playbook configuration with extractors and schema

        Returns:
            Dict with extraction results and summary
        """
        extractors = playbook_config.get("extractors", [])
        schema_paths = playbook_config.get("schema_paths", [])

        # Run all extractors
        results = self.extractor.run_all_extractors(
            chunks=artifact_chunks,
            extractors=extractors,
            schema_paths=schema_paths,
        )

        # Aggregate facts and detect duplicates
        all_facts = []
        duplicates = []
        seen_paths: dict[str, ParsedFact] = {}

        for extractor_id, extractor_results in results.items():
            for result in extractor_results:
                for fact in result.facts:
                    # Check for duplicates
                    if fact.schema_path in seen_paths:
                        existing = seen_paths[fact.schema_path]
                        # Keep higher confidence
                        if fact.confidence > existing.confidence:
                            duplicates.append({
                                "path": fact.schema_path,
                                "kept": "new",
                                "new_confidence": fact.confidence,
                                "old_confidence": existing.confidence,
                            })
                            seen_paths[fact.schema_path] = fact
                        else:
                            duplicates.append({
                                "path": fact.schema_path,
                                "kept": "existing",
                                "new_confidence": fact.confidence,
                                "old_confidence": existing.confidence,
                            })
                    else:
                        seen_paths[fact.schema_path] = fact

        all_facts = list(seen_paths.values())

        # Calculate summary
        total_chunks = len(artifact_chunks)
        total_facts = len(all_facts)
        high_confidence = len([f for f in all_facts if f.confidence >= 0.85])
        low_confidence = len([f for f in all_facts if f.confidence < 0.65])

        return {
            "facts": [f.to_dict() for f in all_facts],
            "duplicates_resolved": duplicates,
            "summary": {
                "total_chunks": total_chunks,
                "total_facts": total_facts,
                "high_confidence_facts": high_confidence,
                "low_confidence_facts": low_confidence,
                "extractors_run": len(extractors),
            },
            "results_by_extractor": {
                eid: [r.to_dict() for r in results]
                for eid, results in results.items()
            },
        }
