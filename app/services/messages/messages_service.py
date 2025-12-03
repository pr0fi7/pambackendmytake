import datetime
import json
import logging
import uuid

from fastapi.responses import StreamingResponse

from app.api.schemas.messages.requests import (
    PatchConversationRequest,
    SendMessageRequest,
)
from app.api.schemas.messages.responses import GetMessagesResponseSchema, TurnSchema
from app.core.exceptions.messages.conversations import ConversationNotFoundError
from app.entities.auth.user import User
from app.entities.messages.conversation import Conversation
from app.entities.messages.message import Message
from app.models.auth.user import ReadUserModel
from app.models.messages.conversation import ConversationDto, CreateConversation
from app.models.messages.message import CreateMessage, MessageDto
from app.repositories.messages.conversation import ConversationRepository
from app.repositories.messages.messages import MessageRepository
from app.services.messages.claude_cli import AsyncClaudeCLI


class MessagesService:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        message_repository: MessageRepository,
    ) -> None:
        self._claude_cli = AsyncClaudeCLI(model="sonnet")
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository

    def get_messages(
        self,
        user_id: int,
        conversation_id: uuid.UUID,
        limit: int,
        cursor: datetime.datetime | None,
    ) -> GetMessagesResponseSchema:
        conversation = self._conversation_repository.get_conversation_by_id(
            conversation_id,
        )

        if conversation is None or conversation.user_id != user_id:
            raise ConversationNotFoundError()

        root_user_messages = MessageDto.validate_list_model(
            self._message_repository.get_root_user_messages(
                user_id,
                conversation_id,
                limit,
                cursor,
            )
        )

        root_message_ids = [m.id for m in root_user_messages]

        children_messages = self._message_repository.get_messages_for_parent_message_id(
            root_message_ids,
        )

        grouped_messages = {rid: [] for rid in root_message_ids}
        for msg in children_messages:
            grouped_messages[msg.parent_message_id].append(msg)

        if root_user_messages:
            has_older = self._message_repository.get_has_older_messages(
                user_id,
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
                    user_message=MessageDto.map(root_msg),  # type: ignore
                    assistant_messages=[  # type: ignore
                        MessageDto.map(m) for m in grouped_messages[root_msg.id]
                    ],
                )
                for root_msg in root_user_messages
            ],
            next_cursor=next_cursor,
        )

    def get_or_create_conversation(
        self,
        user: ReadUserModel,
        conversation_id: uuid.UUID | None,
    ):
        if conversation_id is None:
            conversation = CreateConversation(
                user_id=user.id,
                title="New Conversation",
                type="chat",
                created_date=datetime.datetime.now(),
            )

            return ConversationDto.model_validate(
                self._conversation_repository.create(**conversation.model_dump())
            )

        conversation = ConversationDto.model_validate(
            self._conversation_repository.get_conversation_by_id(
                conversation_id,
            )
        )

        if conversation is None or conversation.user_id != user.id:
            raise ConversationNotFoundError()

        return conversation

    async def send_streaming_response(
        self,
        user: ReadUserModel,
        request: SendMessageRequest,
        headers: dict[str, str],
    ):
        conversation = self.get_or_create_conversation(
            user,
            request.conversation_id,
        )

        user_prompt = request.prompt.strip()

        user_message = CreateMessage(
            user_id=user.id,
            conversation_id=conversation.id,
            role="user",
            content=user_prompt,
            content_new={"type": "text", "text": user_prompt},
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        conversation.updated_date = user_message.timestamp
        self._conversation_repository.update(
            conversation.model_dump(),
            id=request.conversation_id,
        )
        user_message = MessageDto.model_validate(
            self._message_repository.create(**user_message.model_dump())
        )

        return StreamingResponse(
            content=self.stream_message(
                user,
                user_prompt,
                user_message,
                conversation,
            ),
            media_type="text/event-stream",
            headers=headers,
        )

    @staticmethod
    def generate_message_id() -> str:
        return str(uuid.uuid4())

    async def stream_message(
        self,
        user: User,
        user_prompt: str,
        user_message: Message,
        conversation: Conversation,
    ):
        response = {
            "user_id": user.id,
            "conversation_id": str(conversation.id),
            "type": "resume_conversation",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        yield f"data: {json.dumps(response)}\n\n"

        async for response_data in self._claude_cli.send_prompt_stream(user_prompt):
            if response_data.get("type") == "raw":
                logging.info(f"Raw output: {response_data.get('text')}")
                continue
            logging.info(f"Response data: {response_data}")

            message_content = response_data.get("message", {}).get("content", {})

            if response_data.get("type") == "assistant":
                for content in message_content:
                    if content.get("type") == "tool_use":
                        role = "tool_use"
                    else:
                        role = "assistant"

                    response_message = CreateMessage(
                        user_id=user.id,
                        parent_message_id=user_message.id,
                        conversation_id=conversation.id,
                        role=role,
                        content=content.get("text", "").strip(),
                        content_new=content,
                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                    )
                    conversation.updated_date = response_message.timestamp
                    self._conversation_repository.update(
                        conversation.model_dump(),
                        id=conversation.id,
                    )
                    response_message = MessageDto.model_validate(
                        self._message_repository.create(**response_message.model_dump())
                    )

                    response = {
                        "user_id": response_message.user_id,
                        "conversation_id": str(conversation.id),
                        "message_id": str(response_message.id),
                        "role": response_message.role,
                        "content": response_message.content_new,
                        "timestamp": response_message.timestamp.isoformat(),
                    }
                    yield f"data: {json.dumps(response)}\n\n"
            elif response_data.get("type") == "user":
                for content in message_content:
                    if content.get("type") == "tool_result":
                        role = "tool_result"
                    else:
                        role = "assistant"

                    response_message = CreateMessage(
                        user_id=user.id,
                        parent_message_id=user_message.id,
                        conversation_id=conversation.id,
                        role=role,
                        content=content.get("text", "").strip(),
                        content_new=content,
                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                    )
                    conversation.updated_date = response_message.timestamp
                    self._conversation_repository.update(
                        conversation.model_dump(),
                        id=conversation.id,
                    )
                    response_message = MessageDto.model_validate(
                        self._message_repository.create(**response_message.model_dump())
                    )

                    response = {
                        "user_id": response_message.user_id,
                        "conversation_id": str(conversation.id),
                        "message_id": str(response_message.id),
                        "role": response_message.role,
                        "content": response_message.content_new,
                        "timestamp": response_message.timestamp.isoformat(),
                    }
                    yield f"data: {json.dumps(response)}\n\n"
            elif response_data.get("type") == "result":
                logging.info("Finished.")
                response = {
                    "user_id": user.id,
                    "conversation_id": str(conversation.id),
                    "message_id": self.generate_message_id(),
                    "role": "result",
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                }

                yield f"data: {json.dumps(response)}\n\n"
                return

    async def get_user_conversations(
        self,
        user: ReadUserModel,
        conversation_type: str | None = None,
    ) -> list[ConversationDto]:
        conversations = self._conversation_repository.get_conversations_by_user_id(
            user.id,
            conversation_type,
        )
        return [ConversationDto.map(c) for c in conversations]

    async def delete_conversation(
        self,
        user: ReadUserModel,
        conversation_id: uuid.UUID,
    ):
        conversation = ConversationDto.model_validate(
            self._conversation_repository.get_conversation_by_id(
                conversation_id,
            )
        )

        if conversation is None or conversation.user_id != user.id:
            raise ConversationNotFoundError()

        conversation.deleted_date = datetime.datetime.now(datetime.timezone.utc)
        self._conversation_repository.update(
            **conversation.model_dump(),
            id=conversation_id,
        )

    async def patch_conversation(
        self,
        user: ReadUserModel,
        conversation_id: uuid.UUID,
        body: PatchConversationRequest,
    ):
        conversation = ConversationDto.model_validate(
            self._conversation_repository.get_conversation_by_id(
                conversation_id,
            )
        )

        if conversation is None or conversation.user_id != user.id:
            raise ConversationNotFoundError()

        if body.title is not None:
            conversation.title = body.title

        if body.is_pinned is not None:
            conversation.is_pinned = body.is_pinned

        if body.type is not None:
            if body.type in ("chat", "project") and conversation.type in (
                "chat",
                "project",
            ):
                conversation.type = body.type

        return ConversationDto.model_validate(
            self._conversation_repository.update(
                conversation.model_dump(),
                id=conversation_id,
            )
        )
