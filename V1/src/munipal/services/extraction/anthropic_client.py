"""
Anthropic Claude API client.

Handles communication with the Claude API for fact extraction.
"""

import json
import logging
from typing import Any

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from munipal.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnthropicClient:
    """
    Client for Anthropic Claude API.

    Provides structured extraction with retry logic and error handling.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key (defaults to settings)
            model: Model to use (defaults to settings)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    def extract(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """
        Run extraction with Claude.

        Args:
            system_prompt: System context for the extraction
            user_prompt: User prompt with document content
            temperature: Sampling temperature (0 for deterministic)

        Returns:
            Parsed JSON response from Claude
        """
        logger.debug(f"Calling Claude API with model {self.model}")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )

            # Extract text content from response
            response_text = ""
            for block in message.content:
                if block.type == "text":
                    response_text += block.text

            # Parse JSON response
            return self._parse_json_response(response_text)

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse JSON from Claude's response.

        Handles cases where JSON is wrapped in markdown code blocks.
        """
        text = response_text.strip()

        # Try to extract JSON from markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                text = text[start:end].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return raw text wrapped in a dict
            return {
                "raw_response": response_text,
                "parse_error": str(e),
                "facts": [],
            }

    def extract_with_schema(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_paths: list[str],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """
        Extract facts constrained to specific schema paths.

        Adds schema constraint instructions to the prompt.
        """
        schema_instruction = f"""
You must extract ONLY the following schema paths:
{json.dumps(schema_paths, indent=2)}

Return a JSON object with this structure:
{{
    "facts": [
        {{
            "schema_path": "path.from.above",
            "value": "extracted value",
            "value_type": "string|number|date|boolean|currency|percentage",
            "unit": "unit if applicable or null",
            "confidence": 0.0-1.0,
            "confidence_rationale": "why this confidence level",
            "source_quote": "exact text from document supporting this fact"
        }}
    ],
    "unfound_paths": ["paths.not.found.in.document"],
    "extraction_notes": "any relevant notes about the extraction"
}}

IMPORTANT: Only extract facts that are explicitly stated in the document.
Never infer or estimate values. If a value is not found, include its path in unfound_paths.
"""

        enhanced_system = system_prompt + "\n\n" + schema_instruction

        return self.extract(
            system_prompt=enhanced_system,
            user_prompt=user_prompt,
            temperature=temperature,
        )
