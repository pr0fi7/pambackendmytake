import datetime
import json
import logging
import uuid

from fastapi.responses import StreamingResponse

from src.auth.models.conversations import Conversation
from src.auth.models.messages import Message
from src.auth.models.user import User
from src.common.db.database_connector import DatabaseConnector
from src.messages import utils
from src.messages.claude_cli import AsyncClaudeCLI
from src.messages.db import messages_repository, conversations_repository
from src.messages.exceptions import ConversationNotFoundError
from src.messages.schemas.conversation_dto import ConversationDto
from src.messages.schemas.message_dto import MessageDto
from src.messages.schemas.request_schemas import SendMessageRequest, PatchConversationRequest
from src.messages.schemas.response_schemas import GetMessagesResponseSchema, TurnSchema

claude_cli = AsyncClaudeCLI(model="sonnet")


def get_messages(
        user: User,
        conversation_id: uuid.UUID,
        limit: int,
        cursor: datetime.datetime | None,
        db_connector: DatabaseConnector,
) -> GetMessagesResponseSchema:
    conversation = conversations_repository.get_conversation_by_id(db_connector, conversation_id)

    if conversation is None or conversation.user_id != user.id:
        raise ConversationNotFoundError()

    root_user_messages = messages_repository.get_root_user_messages(
        db_connector,
        user.id,
        conversation_id,
        limit,
        cursor,
    )

    root_message_ids = [m.id for m in root_user_messages]

    children_messages = messages_repository.get_messages_for_parent_message_id(db_connector, root_message_ids)

    grouped_messages = {rid: [] for rid in root_message_ids}
    for msg in children_messages:
        grouped_messages[msg.parent_message_id].append(msg)

    if root_user_messages:
        has_older = messages_repository.get_has_older_messages(
            db_connector,
            user.id,
            conversation_id,
            root_user_messages[-1].timestamp,
        )
    else:
        has_older = False

    next_cursor = root_user_messages[-1].timestamp if has_older else None

    return GetMessagesResponseSchema(
        conversation_id=conversation_id,
        conversation_type=conversation.type,
        turns=[
            TurnSchema(
                turn_id=str(root_msg.id),
                user_message=MessageDto.map(root_msg),
                assistant_messages=[MessageDto.map(m) for m in grouped_messages[root_msg.id]],
            )
            for root_msg in root_user_messages
        ],
        next_cursor=next_cursor,
    )


def get_or_create_conversation(db_connector: DatabaseConnector, user: User, conversation_id: uuid.UUID | None):
    if conversation_id is None:
        conversation = Conversation(
            user_id=user.id,
            title="New Conversation",
            type='chat',
        )
        db_connector.save_instances([conversation])
        return conversation

    conversation = conversations_repository.get_conversation_by_id(db_connector, conversation_id)

    if conversation is None or conversation.user_id != user.id:
        raise ConversationNotFoundError()

    return conversation


async def send_streaming_response(
        db_connector: DatabaseConnector,
        user: User,
        request: SendMessageRequest,
        headers: dict[str, str],
):
    conversation = get_or_create_conversation(db_connector, user, request.conversation_id)

    user_prompt = request.prompt.strip()

    user_message = Message(
        user_id=user.id,
        conversation_id=conversation.id,
        role='user',
        content=user_prompt,
        content_new={"type": "text", "text": user_prompt},
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    conversation.last_modified_date = user_message.timestamp
    db_connector.save_instances([user_message, conversation])

    return StreamingResponse(
        content=stream_message(db_connector, user, user_prompt, user_message, conversation),
        media_type="text/event-stream",
        headers=headers,
    )


async def stream_message(
        db_connector: DatabaseConnector,
        user: User,
        user_prompt: str,
        user_message: Message,
        conversation: Conversation,
):
    response = {
        'user_id': user.id,
        'conversation_id': str(conversation.id),
        'type': 'resume_conversation',
        'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    yield f"data: {json.dumps(response)}\n\n"

    async for response_data in claude_cli.send_prompt_stream(user_prompt):
        if response_data.get('type') == 'raw':
            logging.info(f"Raw output: {response_data.get('text')}")
            continue
        logging.info(f"Response data: {response_data}")

        message_content = response_data.get('message', {}).get('content', {})

        if response_data.get('type') == 'assistant':
            for content in message_content:
                if content.get('type') == 'tool_use':
                    role = 'tool_use'
                else:
                    role = 'assistant'

                response_message = Message(
                    user_id=user.id,
                    parent_message_id=user_message.id,
                    conversation_id=conversation.id,
                    role=role,
                    content=content.get('text', '').strip(),
                    content_new=content,
                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                )
                conversation.last_modified_date = response_message.timestamp
                db_connector.save_instances([response_message, conversation])

                response = {
                    'user_id': response_message.user_id,
                    'conversation_id': str(conversation.id),
                    'message_id': str(response_message.id),
                    'role': response_message.role,
                    'content': response_message.content_new,
                    'timestamp': response_message.timestamp.isoformat(),
                }
                yield f"data: {json.dumps(response)}\n\n"
        elif response_data.get('type') == 'user':
            for content in message_content:
                if content.get('type') == 'tool_result':
                    role = 'tool_result'
                else:
                    role = 'assistant'

                response_message = Message(
                    user_id=user.id,
                    parent_message_id=user_message.id,
                    conversation_id=conversation.id,
                    role=role,
                    content=content.get('text', '').strip(),
                    content_new=content,
                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                )
                conversation.last_modified_date = response_message.timestamp
                db_connector.save_instances([response_message, conversation])

                response = {
                    'user_id': response_message.user_id,
                    'conversation_id': str(conversation.id),
                    'message_id': str(response_message.id),
                    'role': response_message.role,
                    'content': response_message.content_new,
                    'timestamp': response_message.timestamp.isoformat(),
                }
                yield f"data: {json.dumps(response)}\n\n"
        elif response_data.get('type') == 'result':
            logging.info('Finished.')
            response = {
                'user_id': user.id,
                'conversation_id': str(conversation.id),
                'message_id': utils.generate_message_id(),
                'role': 'result',
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

            yield f"data: {json.dumps(response)}\n\n"
            return


async def get_user_conversations(
        db_connector: DatabaseConnector,
        user: User,
        conversation_type: str | None = None,
) -> list[ConversationDto]:
    conversations = conversations_repository.get_conversations_by_user_id(
        db_connector,
        user.id,
        conversation_type,
    )
    return [ConversationDto.map(c) for c in conversations]


async def delete_conversation(
        db_connector: DatabaseConnector,
        user: User,
        conversation_id: uuid.UUID,
):
    conversation = conversations_repository.get_conversation_by_id(db_connector, conversation_id)

    if conversation is None or conversation.user_id != user.id:
        raise ConversationNotFoundError()

    conversation.deleted_date = datetime.datetime.now(datetime.timezone.utc)
    db_connector.save_instances([conversation])


async def patch_conversation(
        db_connector: DatabaseConnector,
        user: User,
        conversation_id: uuid.UUID,
        body: PatchConversationRequest
):
    conversation = conversations_repository.get_conversation_by_id(db_connector, conversation_id)

    if conversation is None or conversation.user_id != user.id:
        raise ConversationNotFoundError()

    if body.title is not None:
        conversation.title = body.title

    if body.type is not None:
        if body.type in ('chat', 'project') and conversation.type in ('chat', 'project'):
            conversation.type = body.type

    db_connector.save_instances([conversation])
