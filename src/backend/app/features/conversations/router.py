from fastapi import APIRouter, Depends, HTTPException

from app.features.analysis.live_provider import LlmAnalysisProvider
from app.features.conversations.schemas import (
    ConversationCommand,
    ConversationDeleteResponse,
    ConversationListResponse,
    ConversationResponse,
)
from app.features.conversations.service import (
    append_message,
    clear_conversations,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
)
from app.shared.credential_crypto import CredentialCipher
from app.shared.dependencies import (
    get_credential_cipher,
    get_llm_analysis_provider,
    get_local_store,
)
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation_endpoint(
    command: ConversationCommand,
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
    provider: LlmAnalysisProvider = Depends(get_llm_analysis_provider),
) -> ConversationResponse:
    return create_conversation(store, cipher, provider, command)


@router.get("", response_model=ConversationListResponse)
def list_conversations_endpoint(
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationListResponse:
    return list_conversations(store)


@router.delete("", response_model=ConversationDeleteResponse)
def clear_conversations_endpoint(
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationDeleteResponse:
    return ConversationDeleteResponse(deleted_count=clear_conversations(store))


@router.get("/{conversation_id}", response_model=ConversationResponse)
def read_conversation(
    conversation_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationResponse:
    conversation = get_conversation(store, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", response_model=ConversationDeleteResponse)
def delete_conversation_endpoint(
    conversation_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> ConversationDeleteResponse:
    if not delete_conversation(store, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDeleteResponse(deleted_count=1)


@router.post("/{conversation_id}/messages", response_model=ConversationResponse)
def append_message_endpoint(
    conversation_id: str,
    command: ConversationCommand,
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
    provider: LlmAnalysisProvider = Depends(get_llm_analysis_provider),
) -> ConversationResponse:
    conversation = append_message(store, cipher, provider, conversation_id, command)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
