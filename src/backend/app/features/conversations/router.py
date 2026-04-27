from fastapi import APIRouter, Depends, HTTPException

from app.features.conversations.schemas import ConversationCommand, ConversationResponse
from app.features.conversations.service import append_message, create_conversation, get_conversation
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation_endpoint(
    command: ConversationCommand,
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationResponse:
    return create_conversation(store, command)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def read_conversation(
    conversation_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationResponse:
    conversation = get_conversation(store, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/{conversation_id}/messages", response_model=ConversationResponse)
def append_message_endpoint(
    conversation_id: str,
    command: ConversationCommand,
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationResponse:
    conversation = append_message(store, conversation_id, command)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
