"""Paid, strictly scoped evidence lookup and durable conversations."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy import delete, select, update

from munipal.api.dependencies import DbSession, PaidUser
from munipal.core.models import Artifact, AskConversation, AskMessage, Chunk, Project
from munipal.core.schemas.ask import (
    AskCitation,
    AskConversationRead,
    AskCreate,
    AskDocument,
    AskHistory,
    AskMessageRead,
    AskQuestion,
    AskScope,
)
from munipal.services.ask_service import answer, citation, source_query
from munipal.services.authorization_service import AuthorizationService


class PrivateAskRoute(APIRoute):
    """Bound streamed bodies before parsing and never echo input/exception details."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def private_handler(request):
            try:
                body = bytearray()
                async for part in request.stream():
                    body.extend(part)
                    if len(body) > 16384:
                        raise HTTPException(413, detail="Request too large")
                request._body = bytes(body)
                response = await handler(request)
                response.headers["Cache-Control"] = "no-store"
                return response
            except RequestValidationError:
                raise HTTPException(
                    422, detail="Invalid Ask request", headers={"Cache-Control": "no-store"}
                ) from None
            except HTTPException as exc:
                exc.headers = {**(exc.headers or {}), "Cache-Control": "no-store"}
                raise
            except Exception:
                raise HTTPException(
                    500,
                    detail="Ask is temporarily unavailable",
                    headers={"Cache-Control": "no-store"},
                ) from None

        return private_handler


router = APIRouter(
    route_class=PrivateAskRoute,
    responses={
        401: {"description": "Valid access token required"},
        403: {"description": "Inactive account or subscription_required; upgrade_url: /pricing"},
        404: {"description": "Not found or inaccessible"},
        413: {"description": "Request body exceeds 16 KiB"},
    },
)


@router.get("/scopes", response_model=list[AskScope])
async def list_scopes(user: PaidUser, db: DbSession):
    projects = (
        await db.scalars(
            select(Project)
            .where(
                *AuthorizationService.owned_project_scope(user),
            )
            .order_by(Project.name, Project.id)
            .limit(100)
        )
    ).all()
    scopes = []
    for project in projects:
        artifacts = (
            await db.scalars(
                select(Artifact)
                .where(
                    Artifact.project_id == project.id,
                )
                .order_by(Artifact.filename, Artifact.id)
                .limit(200)
            )
        ).all()
        scopes.append(
            AskScope(
                id=project.id,
                name=project.name,
                documents=[
                    AskDocument(id=a.id, name=a.display_name or a.filename) for a in artifacts
                ],
            )
        )
    return scopes


async def check_scope(db, user, project_id, artifact_id=None):
    await AuthorizationService(db).require_owned_project(user, project_id)
    if artifact_id and not await db.scalar(
        select(Artifact.id).where(
            Artifact.id == artifact_id,
            Artifact.project_id == project_id,
        )
    ):
        raise HTTPException(404, detail="Not found")


async def conversation_for(db, user, conversation_id):
    conversation = await db.scalar(
        select(AskConversation).where(
            AskConversation.id == str(conversation_id),
            AskConversation.owner_id == user.id,
        )
    )
    if conversation is None:
        raise HTTPException(404, detail="Not found")
    await check_scope(db, user, conversation.project_id, conversation.artifact_id)
    return conversation


@router.post("/conversations", response_model=AskConversationRead, status_code=201)
async def create_conversation(payload: AskCreate, user: PaidUser, db: DbSession):
    project_id = str(payload.project_id)
    artifact_id = str(payload.artifact_id) if payload.artifact_id else None
    await check_scope(db, user, project_id, artifact_id)
    conversation = AskConversation(owner_id=user.id, project_id=project_id, artifact_id=artifact_id)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[AskConversationRead])
async def list_conversations(user: PaidUser, db: DbSession, offset: int = Query(0, ge=0)):
    return (
        await db.scalars(
            select(AskConversation)
            .join(Project)
            .where(
                AskConversation.owner_id == user.id,
                *AuthorizationService.owned_project_scope(user),
            )
            .order_by(AskConversation.updated_at.desc(), AskConversation.id)
            .offset(offset)
            .limit(50)
        )
    ).all()


@router.get("/conversations/{conversation_id}", response_model=AskHistory)
async def read_conversation(conversation_id: UUID, user: PaidUser, db: DbSession):
    conversation = await conversation_for(db, user, conversation_id)
    return await history_for(db, user, conversation)


async def history_for(db, user, conversation):
    messages = (
        await db.scalars(
            select(AskMessage)
            .where(
                AskMessage.conversation_id == conversation.id,
            )
            .order_by(AskMessage.sequence)
        )
    ).all()
    # Revalidate saved evidence before returning snapshots after document moves/deletions.
    cited_ids = {c["chunk_id"] for m in messages for c in m.citations}
    if cited_ids:
        rows = (
            await db.execute(
                source_query(user, conversation.project_id, conversation.artifact_id).where(
                    Chunk.id.in_(cited_ids)
                )
            )
        ).all()
        if {chunk.id for chunk, _ in rows} != cited_ids:
            raise HTTPException(404, detail="Not found")
    return AskHistory(
        **AskConversationRead.model_validate(conversation).model_dump(),
        messages=[AskMessageRead.model_validate(m) for m in messages],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=AskHistory)
async def send_message(conversation_id: UUID, payload: AskQuestion, user: PaidUser, db: DbSession):
    conversation = await conversation_for(db, user, conversation_id)
    # Atomic counter reserves a pair and serializes concurrent requests across workers.
    sequence = await db.scalar(
        update(AskConversation)
        .where(
            AskConversation.id == conversation.id,
            AskConversation.next_sequence <= 199,
        )
        .values(next_sequence=AskConversation.next_sequence + 2, updated_at=datetime.now(UTC))
        .returning(AskConversation.next_sequence)
    )
    if sequence is None:
        raise HTTPException(409, detail="Conversation limit reached. Start a new chat.")
    kind, content, citations = await answer(db, user, conversation, payload.question)
    if sequence == 3:
        conversation.title = payload.question[:120]
    db.add_all(
        [
            AskMessage(
                conversation_id=conversation.id,
                sequence=sequence - 2,
                role="user",
                kind="question",
                content=payload.question,
                citations=[],
            ),
            AskMessage(
                conversation_id=conversation.id,
                sequence=sequence - 1,
                role="assistant",
                kind=kind,
                content=content,
                citations=citations,
            ),
        ]
    )
    await db.flush()
    await db.refresh(conversation)
    history = await history_for(db, user, conversation)
    await db.commit()
    return history


@router.get("/sources/{chunk_id}", response_model=AskCitation)
async def read_source(chunk_id: UUID, user: PaidUser, db: DbSession):
    row = (await db.execute(source_query(user).where(Chunk.id == str(chunk_id)))).first()
    if row is None:
        raise HTTPException(404, detail="Not found")
    return citation(*row)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: UUID, user: PaidUser, db: DbSession):
    conversation = await conversation_for(db, user, conversation_id)
    await db.execute(delete(AskMessage).where(AskMessage.conversation_id == conversation.id))
    await db.delete(conversation)
    await db.commit()
    return Response(status_code=204)
