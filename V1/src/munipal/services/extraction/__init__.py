"""
AI extraction services.

Per spec (WP3): AI Pipelines & Review
- Propose facts via schema-driven extraction
- Enable human review & approval
- Maintain confidence scores and provenance
"""

from munipal.services.extraction.anthropic_client import AnthropicClient
from munipal.services.extraction.extractor import FactExtractor
from munipal.services.extraction.response_parser import ExtractionResponseParser

__all__ = [
    "AnthropicClient",
    "FactExtractor",
    "ExtractionResponseParser",
]
