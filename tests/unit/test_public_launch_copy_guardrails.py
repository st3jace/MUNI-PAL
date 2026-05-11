"""Static guardrails for public launch copy built into Vercel healthcare/pricing surfaces."""

from pathlib import Path

PUBLIC_COPY_PATHS = [
    Path("frontend/index.healthcare.html"),
    *Path("frontend/src/pages/tools").rglob("*.tsx"),
]

BLOCKED_PUBLIC_PHRASES = [
    "what your advisors won't tell you",
    "document your way to a better rating",
    "ongoing advisory access",
    "COI optimization",
    "active deal coordination",
    "TIC estimates",
    "what it costs",
    "rating pays",
    "achieving and maintaining an A or better",
]

REQUIRED_BOUNDARY_PHRASES = [
    "registered advisor",
    "not municipal advisory advice",
]


def _public_copy_text() -> str:
    return chr(10).join(path.read_text(encoding="utf-8") for path in PUBLIC_COPY_PATHS).lower()


def test_public_launch_copy_avoids_advisor_replacement_and_rating_improvement_language() -> None:
    public_copy = _public_copy_text()

    for phrase in BLOCKED_PUBLIC_PHRASES:
        assert phrase.lower() not in public_copy


def test_public_launch_copy_keeps_registered_advisor_boundary_visible() -> None:
    public_copy = _public_copy_text()

    for phrase in REQUIRED_BOUNDARY_PHRASES:
        assert phrase.lower() in public_copy
