import datetime
import logging
import uuid
from typing import Annotated, Iterable

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)
from fastapi.params import Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies.auth import AuthDependencies
from app.api.schemas.messages.requests import (
    PatchConversationRequest,
    SendMessageRequest,
)
from app.api.schemas.messages.responses import GetMessagesResponseSchema
from app.config import settings
from app.models.messages.conversation import ConversationDto
from app.services.auth.auth_service import AuthService
from app.services.messages.messages_service import MessagesService

router = APIRouter(prefix="/messages")
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10, read=None, write=60, pool=60),
            headers={"Accept-Encoding": "identity"},
        )
    return _client


HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    out = {}
    for k, v in headers:
        lk = k.lower()
        if lk in HOP_BY_HOP or lk == "host":
            continue
        out[k] = v
    return out


@router.get("/messages")
@inject
def get_messages(
    conversation_id: uuid.UUID,
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    message_service: Annotated[MessagesService, Depends(Provide["message_service"])],
    token: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
    limit: int = 10,
    cursor: datetime.datetime | None = None,
) -> GetMessagesResponseSchema:
    user_id = deps.require_access_token_user_id(token)
    return message_service.get_messages(user_id, conversation_id, limit, cursor)


@router.post("/messages")
@inject
async def send_messages(
    body: SendMessageRequest,
    request: Request,
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    message_service: Annotated[MessagesService, Depends(Provide["message_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
    token: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
):
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    logging.info(
        f"Received send message request, user_id={user_id}, prompt: {body.prompt}"
    )

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }

    if settings.AGENT_API or user_id in settings.CENTRAL_API_USER_ID:
        logging.info("Streaming response from local Claude code.")
        return await message_service.send_streaming_response(user, body, headers)

    backend = user.server_host
    if not backend:
        raise HTTPException(503, "No backend assigned")

    target = f"{backend}/v1/messages/messages"
    logging.info(f"Proxying request to {target}")

    in_headers = filter_headers(request.headers.items())
    in_headers.setdefault("Accept", "text/event-stream")
    in_headers.setdefault("Accept-Encoding", "identity")

    client = get_client()
    raw_body = await request.body()

    async def gen():
        async with client.stream(
            "POST", target, headers=in_headers, content=raw_body
        ) as resp:
            if resp.status_code >= 400:
                err = await resp.aread()
                yield f"event: error\ndata: {err.decode('utf-8', 'ignore')}\n\n"
                return
            async for chunk in resp.aiter_bytes():
                yield chunk

    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)


@router.get("/conversations")
@inject
async def get_user_conversations(
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    message_service: Annotated[MessagesService, Depends(Provide["message_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
    conversation_type: str | None = Query(None, alias="type"),
    token: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
) -> list[ConversationDto]:
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    return await message_service.get_user_conversations(user, conversation_type)


@router.delete("/conversations/{conversation_id}")
@inject
async def delete_conversation(
    conversation_id: uuid.UUID,
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    message_service: Annotated[MessagesService, Depends(Provide["message_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
    token: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
):
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    await message_service.delete_conversation(user, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/conversations/{conversation_id}")
@inject
async def patch_conversation(
    conversation_id: uuid.UUID,
    body: PatchConversationRequest,
    deps: Annotated[AuthDependencies, Depends(Provide["auth_deps"])],
    message_service: Annotated[MessagesService, Depends(Provide["message_service"])],
    auth_service: Annotated[AuthService, Depends(Provide["auth_service"])],
    token: HTTPAuthorizationCredentials | None = Security(HTTPBearer()),
):
    user_id = deps.require_access_token_user_id(token)
    user = auth_service.get_user_by_id(user_id)
    return await message_service.patch_conversation(user, conversation_id, body)

