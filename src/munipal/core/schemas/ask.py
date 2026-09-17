"""Stable Ask API contract. Evidence is data, never generated instructions."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AskDocument(BaseModel):
    id: str
    name: str


class AskScope(AskDocument):
    documents: list[AskDocument]


class AskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: UUID
    artifact_id: UUID | None = None


class AskConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    artifact_id: str | None
    title: str
    created_at: datetime
    updated_at: datetime


class AskHistory(AskConversationRead):
    messages: list["AskMessageRead"]


class AskQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)


class AskCitation(BaseModel):
    chunk_id: str
    artifact_id: str
    document_name: str
    locator: str
    excerpt: str
    source_url: str


class AskMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    sequence: int
    role: Literal["user", "assistant"]
    kind: Literal["question", "evidence", "refusal", "no_hits"]
    content: str
    citations: list[AskCitation]
    created_at: datetime
    updated_at: datetime
