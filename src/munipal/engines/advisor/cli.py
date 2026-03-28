"""Municipal Advisor CLI — interactive terminal chat.

Usage:
    python -m munipal.engines.advisor chat
    python -m munipal.engines.advisor chat --session <id>
    python -m munipal.engines.advisor sessions
"""

from __future__ import annotations

import io
import sys
import click

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


@click.group()
def cli():
    """Muni-Pal Municipal Advisor — conversational bond analysis."""
    pass


@cli.command()
@click.option("--session", "session_id", default=None, help="Resume session by ID")
@click.option("--model", default=None, help="Override Claude model")
def chat(session_id: str | None, model: str | None):
    """Start an interactive advisor chat session."""
    from .agent import AdvisorAgent
    from .session import AdvisorSession

    if session_id:
        session = AdvisorSession.resume(session_id)
        click.echo(f"Resumed session {session_id} ({len(session.messages)} messages)")
    else:
        session = AdvisorSession()
        click.echo(f"New session: {session.session_id}")

    agent = AdvisorAgent(session=session, model=model)

    click.echo("")
    click.echo("=" * 60)
    click.echo("  Muni-Pal Municipal Advisor")
    click.echo("  Type your questions. Commands: /quit /sessions /clear")
    click.echo("=" * 60)
    click.echo("")

    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\nGoodbye.")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "/q"):
            click.echo("Session saved. Goodbye.")
            break

        if user_input.lower() == "/sessions":
            sessions = AdvisorSession.list_sessions()
            if not sessions:
                click.echo("No saved sessions.")
            else:
                click.echo(f"\n{'ID':<40} {'Messages':>8}  {'Updated'}")
                click.echo("-" * 70)
                for s in sessions[:10]:
                    click.echo(
                        f"{s['session_id']:<40} {s['message_count']:>8}  "
                        f"{s.get('updated_at', 'N/A')}"
                    )
            click.echo("")
            continue

        if user_input.lower() == "/clear":
            session = AdvisorSession()
            agent = AdvisorAgent(session=session, model=model)
            click.echo(f"New session: {session.session_id}\n")
            continue

        # Stream response
        click.echo("")
        try:
            for event in agent.query_stream(user_input):
                if event["type"] == "text_delta":
                    click.echo(event["text"], nl=False)
                elif event["type"] == "tool_call":
                    click.echo(f"\n  [calling {event['name']}...]", nl=False)
                elif event["type"] == "tool_result":
                    click.echo(f" done", nl=False)
                elif event["type"] == "confirmation_required":
                    click.echo("")  # newline after tool indicator
                elif event["type"] == "done":
                    pass
                elif event["type"] == "error":
                    click.echo(f"\n  ERROR: {event['message']}")
        except Exception as e:
            click.echo(f"\nError: {e}")

        click.echo("\n")


@cli.command()
def sessions():
    """List saved advisor sessions."""
    from .session import AdvisorSession

    sessions_list = AdvisorSession.list_sessions()
    if not sessions_list:
        click.echo("No saved sessions.")
        return

    click.echo(f"\n{'ID':<40} {'Messages':>8}  {'Updated'}")
    click.echo("-" * 70)
    for s in sessions_list:
        click.echo(
            f"{s['session_id']:<40} {s['message_count']:>8}  "
            f"{s.get('updated_at', 'N/A')}"
        )
    click.echo(f"\nTotal: {len(sessions_list)} sessions")


@cli.command()
@click.argument("session_id")
def delete(session_id: str):
    """Delete a saved session."""
    from .session import AdvisorSession

    if AdvisorSession.delete(session_id):
        click.echo(f"Deleted session {session_id}")
    else:
        click.echo(f"Session {session_id} not found")


if __name__ == "__main__":
    cli()
