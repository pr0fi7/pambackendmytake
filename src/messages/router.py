import datetime
import logging
import uuid
from typing import Iterable

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.params import Query
from fastapi.responses import StreamingResponse

from src import constants
from src.auth import auth_dependencies
from src.auth.auth_dependencies import require_user
from src.auth.models.user import User
from src.common.db.database_connector import DatabaseConnector
from src.common.dependencies import get_database_connector_dependency
from src.common.utils.handle_and_raise_generic_exception import handle_and_raise_generic_exception
from src.messages import service
from src.messages.schemas.conversation_dto import ConversationDto
from src.messages.schemas.request_schemas import SendMessageRequest, PatchConversationRequest
from src.messages.schemas.response_schemas import GetMessagesResponseSchema

router = APIRouter()

# Single shared client for connection pooling
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        # Long timeouts for streaming; no decompression to keep SSE frames intact
        _client = httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=None, write=60, pool=60),
                                    headers={"Accept-Encoding": "identity"})
    return _client


# ---- Helpers to copy headers/body safely ----
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade",
}


def filter_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    out = {}
    for k, v in headers:
        lk = k.lower()
        if lk in HOP_BY_HOP:
            continue
        # Optionally drop Host from pass-through; httpx sets it appropriately
        if lk == "host":
            continue
        out[k] = v
    return out


@router.get(
    "/messages",
    dependencies=[Depends(auth_dependencies.require_harmix_api_key_auth)]
)
@handle_and_raise_generic_exception
def get_messages(
        conversation_id: uuid.UUID,
        limit: int = 10,
        cursor: datetime.datetime | None = None,
        user: User = Depends(require_user),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
) -> GetMessagesResponseSchema:
    return service.get_messages(user, conversation_id, limit, cursor, db_connector)


@router.post(
    "/messages",
    dependencies=[Depends(auth_dependencies.require_harmix_api_key_auth)],
)
@handle_and_raise_generic_exception
async def send_messages(
        body: SendMessageRequest,
        request: Request,
        user: User = Depends(require_user),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
):
    logging.info(f"Received send message request, user_id={user.id}, prompt: {body.prompt}")

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # tell Nginx not to buffer
        "Connection": "keep-alive",
    }

    if constants.env_config.AGENT_API or user.id in constants.env_config.CENTRAL_API_USER_ID:
        logging.info("Streaming response from local Claude code.")
        return await service.send_streaming_response(db_connector, user, body, headers)

    logging.info("Proxying streaming response from another API backend.")

    # backend = pick_backend(user)
    backend = user.server_host
    target = f"{backend}/messages"

    if not backend:
        raise HTTPException(503, "No backend assigned")

    logging.info(f"Proxying request to {target}")

    in_headers = filter_headers(request.headers.items())

    # Force event-stream upstream & avoid compression
    in_headers.setdefault("Accept", "text/event-stream")
    in_headers.setdefault("Accept-Encoding", "identity")

    client = get_client()
    raw_body = await request.body()

    async def gen():
        async with client.stream("POST", target, headers=in_headers, content=raw_body) as resp:
            if resp.status_code >= 400:
                err = await resp.aread()
                yield f"event: error\ndata: {err.decode('utf-8', 'ignore')}\n\n"
                return
            async for chunk in resp.aiter_bytes():
                yield chunk

    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)


@router.get('/conversations')
@handle_and_raise_generic_exception
async def get_user_conversations(
        conversation_type: str | None = Query(None, alias='type'),
        user: User = Depends(require_user),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
) -> list[ConversationDto]:
    return await service.get_user_conversations(db_connector, user, conversation_type)


@router.delete('/conversations/{conversation_id}')
@handle_and_raise_generic_exception
async def delete_conversation(
        conversation_id: uuid.UUID,
        user: User = Depends(require_user),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
):
    await service.delete_conversation(db_connector, user, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch('/conversations/{conversation_id}')
@handle_and_raise_generic_exception
async def patch_conversation(
        conversation_id: uuid.UUID,
        body: PatchConversationRequest,
        user: User = Depends(require_user),
        db_connector: DatabaseConnector = Depends(get_database_connector_dependency),
):
    await service.patch_conversation(db_connector, user, conversation_id, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
