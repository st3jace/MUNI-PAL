"""Municipal Advisor Agent — agentic loop using Claude API tool_use.

The agent accepts natural language, decides which Muni-Pal tools to invoke,
executes them, feeds results back, and iterates until it has a final answer.
Expensive operations pause for user confirmation.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Generator

import anthropic

from munipal.config import get_settings
from .executor import execute_tool
from .prompts import SYSTEM_PROMPT
from .session import AdvisorSession
from .tools import ADVISOR_TOOLS, EXPENSIVE_TOOLS

logger = logging.getLogger(__name__)

AGENT_MODEL = "claude-opus-4-6-20250616"
MAX_ITERATIONS = 12


class AdvisorAgent:
    """Conversational municipal bond advisor backed by Claude tool_use."""

    def __init__(
        self,
        session: AdvisorSession | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.model = model or AGENT_MODEL
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.session = session or AdvisorSession()

    # ── Synchronous Query ──────────────────────────────────────────────

    def query(self, user_message: str) -> str:
        """Send a user message and run the agentic loop to completion.

        Returns the final assistant text response.
        """
        # Handle pending confirmation
        pending = self.session.pending_confirmation
        if pending and user_message.strip().lower() in ("yes", "y", "proceed", "go", "confirm"):
            self.session.clear_pending_confirmation()
            result = execute_tool(pending["tool_name"], pending["tool_input"])
            # Inject the tool result into history
            self.session.messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": pending.get("tool_use_id", "confirmed"),
                        "content": result,
                    }
                ],
            })
        else:
            self.session.add_user_message(user_message)

        return self._run_loop()

    def _run_loop(self) -> str:
        """Core agentic loop: call Claude, execute tools, repeat."""
        for iteration in range(MAX_ITERATIONS):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=ADVISOR_TOOLS,
                messages=self.session.messages,
            )

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                self.session.add_assistant_message(text)
                self.session.save()
                return text

            if response.stop_reason == "tool_use":
                # Add assistant message (contains tool_use blocks)
                self.session.messages.append({
                    "role": "assistant",
                    "content": [self._block_to_dict(b) for b in response.content],
                })

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    # Check if expensive tool needs confirmation
                    if block.name in EXPENSIVE_TOOLS:
                        self.session.set_pending_confirmation(block.name, block.input)
                        self.session.data["pending_confirmation"]["tool_use_id"] = block.id

                        # Return a confirmation request as the response
                        confirm_text = (
                            f"I'd like to run **{block.name}** "
                            f"with the following parameters:\n\n"
                            f"```json\n{json.dumps(block.input, indent=2)}\n```\n\n"
                            f"This is a heavier operation. Shall I proceed? "
                            f"(Reply **yes** to confirm)"
                        )
                        self.session.add_assistant_message(confirm_text)
                        self.session.save()
                        return confirm_text

                    # Execute lightweight tool
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

                # Feed results back
                self.session.messages.append({
                    "role": "user",
                    "content": tool_results,
                })
            else:
                # Unexpected stop reason
                text = self._extract_text(response)
                self.session.add_assistant_message(text or "(No response)")
                self.session.save()
                return text or "(No response)"

        final = "I've reached the maximum number of analysis steps. Here's what I have so far."
        self.session.add_assistant_message(final)
        self.session.save()
        return final

    # ── Streaming Query ────────────────────────────────────────────────

    def query_stream(self, user_message: str) -> Generator[dict[str, Any], None, None]:
        """Stream the agent's response, yielding events for the frontend.

        Event types:
          - {"type": "text_delta", "text": "..."}
          - {"type": "tool_call", "name": "...", "input": {...}}
          - {"type": "tool_result", "name": "...", "summary": "..."}
          - {"type": "confirmation_required", "tool": "...", "input": {...}}
          - {"type": "done", "text": "..."}
          - {"type": "error", "message": "..."}
        """
        # Handle pending confirmation
        pending = self.session.pending_confirmation
        if pending and user_message.strip().lower() in ("yes", "y", "proceed", "go", "confirm"):
            self.session.clear_pending_confirmation()
            yield {"type": "tool_call", "name": pending["tool_name"], "input": pending["tool_input"]}
            result = execute_tool(pending["tool_name"], pending["tool_input"])
            yield {"type": "tool_result", "name": pending["tool_name"], "summary": f"Completed {pending['tool_name']}"}

            self.session.messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": pending.get("tool_use_id", "confirmed"),
                        "content": result,
                    }
                ],
            })
        else:
            self.session.add_user_message(user_message)

        yield from self._run_loop_stream()

    def _run_loop_stream(self) -> Generator[dict[str, Any], None, None]:
        """Streaming agentic loop."""
        for iteration in range(MAX_ITERATIONS):
            try:
                full_text = ""
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=ADVISOR_TOOLS,
                    messages=self.session.messages,
                ) as stream:
                    for text in stream.text_stream:
                        full_text += text
                        yield {"type": "text_delta", "text": text}

                    response = stream.get_final_message()
            except anthropic.APIError as e:
                yield {"type": "error", "message": f"API error: {e}"}
                return

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                self.session.add_assistant_message(text)
                self.session.save()
                yield {"type": "done", "text": text}
                return

            if response.stop_reason == "tool_use":
                self.session.messages.append({
                    "role": "assistant",
                    "content": [self._block_to_dict(b) for b in response.content],
                })

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    if block.name in EXPENSIVE_TOOLS:
                        self.session.set_pending_confirmation(block.name, block.input)
                        self.session.data["pending_confirmation"]["tool_use_id"] = block.id

                        confirm_text = (
                            f"I'd like to run **{block.name}** "
                            f"with the following parameters:\n\n"
                            f"```json\n{json.dumps(block.input, indent=2)}\n```\n\n"
                            f"This is a heavier operation. Shall I proceed? "
                            f"(Reply **yes** to confirm)"
                        )
                        self.session.add_assistant_message(confirm_text)
                        self.session.save()
                        yield {"type": "confirmation_required", "tool": block.name, "input": block.input}
                        yield {"type": "done", "text": confirm_text}
                        return

                    yield {"type": "tool_call", "name": block.name, "input": block.input}
                    result = execute_tool(block.name, block.input)
                    yield {"type": "tool_result", "name": block.name, "summary": f"Got {block.name} results"}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

                self.session.messages.append({
                    "role": "user",
                    "content": tool_results,
                })
            else:
                text = self._extract_text(response) or "(No response)"
                self.session.add_assistant_message(text)
                self.session.save()
                yield {"type": "done", "text": text}
                return

        yield {"type": "done", "text": "Reached maximum analysis steps."}

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _extract_text(response) -> str:
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    @staticmethod
    def _block_to_dict(block) -> dict:
        if block.type == "text":
            return {"type": "text", "text": block.text}
        if block.type == "tool_use":
            return {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            }
        return {"type": block.type}
