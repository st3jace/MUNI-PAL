"""Deterministic record lookup, adapted from fulfillment/demo/ask.py.

No filesystem corpus, model provider, instruction execution, or interpreted conclusions.
"""

import re

from sqlalchemy import select

from munipal.core.models import Artifact, Chunk, Project
from munipal.services.authorization_service import AuthorizationService

JUDGMENT = re.compile(
    r"\b(material|materiality|should|do (we|i) (need|have) to|must|compliant|compliance|"
    r"appl(y|ies|icable|icability)|controls?|which clause|reportable|are we (ok|fine|late)|"
    r"advice|advise|recommend\w*|calculate|calculation|required|satisf\w*|"
    r"what date|how many days|when (is|are).*(due|deadline)|\d+ days (after|from)|"
    r"what.*(deadline|due date)|when (do|can|should|must) (we|i)|"
    r"have (we|i) (met|fulfilled|satisfied)|can (we|i)|legally|sufficient|in (breach|default)|"
    r"is (this|that|it) legal|(?:has|have)\b.{0,80}\bdefaulted|did\b.{0,80}\bdefault|"
    r"municipal advis(?:or|er)(?:'s)?\b.{0,80}\b(?:approv\w*|opinion|recommend\w*|advice))\b",
    re.I,
)
SAFE_RECORD_LOOKUP = re.compile(
    r"^\s*(?:where is|find|locate|show me)\s+(?:the\s+)?"
    r"(?:legal opinion|default provision|municipal advis(?:or|er) agreement)\s*[?.!]*\s*$",
    re.I,
)
FAIL_CLOSED_JUDGMENT = re.compile(
    r"\b(?:default\w*|legal(?:ly|ity)?|lawful|permissib\w*|permitted|allowed|"
    r"illegal|noncompliant|prohibit\w*|(?:un)?authoriz\w*|municipal[ -]+advis(?:or|er)|"
    r"compl(?:y|ies|ied|iance|iant)|violat\w*|breach\w*)\b",
    re.I,
)
CONCLUSION_QUESTION = re.compile(
    r"^\s*(?:is|are|am|was|were|do|does|did|can|could|should|would|will|may|might|"
    r"must|has|have|had|what|when|why|how|which)\b",
    re.I,
)
CONCLUSION_REQUEST = re.compile(
    r"^\s*(?:please\s+)?(?:determine|assess|evaluate|decide|confirm|interpret|explain|"
    r"advise|recommend)\b",
    re.I,
)
STOP = set(
    "the a an of in to is my our where what when does do for and or on by it this that are be with".split()
)
REFUSAL = (
    "That is a call for your bond counsel or dissemination agent. "
    "The question is recorded in this conversation for you to share with them. "
    "No judgment or deadline calculation has been provided."
)
NO_HITS = (
    "No matching excerpts found in the searched scope. This does not establish that a "
    "record or obligation is absent. Try a document term or check the source documents."
)
MAX_CANDIDATES = 1000
MAX_EXCERPT = 1600


def is_judgment(question: str) -> bool:
    if SAFE_RECORD_LOOKUP.search(question):
        return False
    return bool(
        JUDGMENT.search(question)
        or FAIL_CLOSED_JUDGMENT.search(question)
        or CONCLUSION_QUESTION.search(question)
        or CONCLUSION_REQUEST.search(question)
    )


def question_terms(question: str) -> list[str]:
    return list(
        dict.fromkeys(
            t
            for t in re.findall(r"[a-z0-9()\-]+", question.lower())
            if t not in STOP and len(t) > 2
        )
    )[:32]


def lexical_score(terms: list[str], heading: str, body: str) -> int:
    hay = (heading + " " + body).lower()
    return sum(
        3 + min(hay.count(t), 5) + (4 if t in heading.lower() else 0) for t in terms if t in hay
    )


def citation(chunk, artifact, terms=()):
    text = chunk.text_content or ""
    # Return a contiguous verbatim window, including the first lexical match.
    positions = [text.lower().find(t) for t in terms if t in text.lower()]
    start = max(0, min(positions) - 200) if positions else 0
    locator = chunk.section_title or (
        f"Page {chunk.page_number}"
        if chunk.page_number is not None
        else f"Sheet {chunk.sheet_name}"
        if chunk.sheet_name
        else f"Chunk {chunk.sequence_number}"
    )
    return {
        "chunk_id": chunk.id,
        "artifact_id": artifact.id,
        "document_name": artifact.display_name or artifact.filename,
        "locator": locator,
        "excerpt": text[start : start + MAX_EXCERPT],
        "source_url": f"/api/v1/ask/sources/{chunk.id}",
    }


def source_query(user, project_id=None, artifact_id=None):
    query = (
        select(Chunk, Artifact)
        .join(Artifact)
        .join(Project)
        .where(
            *AuthorizationService.owned_project_scope(user),
        )
    )
    if project_id:
        query = query.where(Project.id == project_id)
    if artifact_id:
        query = query.where(Artifact.id == artifact_id)
    return query


async def answer(db, user, conversation, question):
    if is_judgment(question):
        return "refusal", REFUSAL, []
    terms = question_terms(question)
    if not terms:
        return "no_hits", NO_HITS, []
    # All SQL candidates already belong to the authorized owner, tenant, project and document.
    query = (
        source_query(user, conversation.project_id, conversation.artifact_id)
        .where(
            Chunk.text_content.is_not(None),
        )
        .order_by(Artifact.id, Chunk.sequence_number, Chunk.id)
        .limit(MAX_CANDIDATES + 1)
    )
    rows = (await db.execute(query)).all()
    truncated = len(rows) > MAX_CANDIDATES
    ranked = sorted(
        (
            (
                lexical_score(terms, chunk.section_title or "", chunk.text_content or ""),
                chunk,
                artifact,
            )
            for chunk, artifact in rows[:MAX_CANDIDATES]
        ),
        key=lambda hit: (-hit[0], hit[2].id, hit[1].sequence_number, hit[1].id),
    )
    citations = [citation(chunk, artifact, terms) for score, chunk, artifact in ranked if score][:4]
    content = (
        "Matching source excerpts. These are records, not determinations of status, applicability or compliance."
        if citations
        else NO_HITS
    )
    if truncated:
        content += " Search limited to the first 1,000 chunks; narrow the document scope."
    return ("evidence" if citations else "no_hits"), content, citations
