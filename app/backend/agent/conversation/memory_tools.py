from conversation.models import Conversation, ConversationMetadata


def save_memory(conversation_id: int, key: str, value: str) -> str:
    if not Conversation.objects.filter(id=conversation_id, is_deleted=False).exists():
        return f"error: conversation {conversation_id} not found"
    ConversationMetadata.objects.update_or_create(
        conversation_id=conversation_id,
        key=key,
        defaults={"value": value, "is_deleted": False, "deleted_at": None},
    )
    return f"saved: {key}"


def list_memory(conversation_id: int) -> list[dict]:
    return [
        {"key": key, "value": value}
        for key, value in ConversationMetadata.objects.filter(
            conversation_id=conversation_id, is_deleted=False
        )
        .order_by("created_at")
        .values_list("key", "value")
    ]


def delete_memory(conversation_id: int, key: str) -> str:
    try:
        memory = ConversationMetadata.objects.get(
            conversation_id=conversation_id, key=key, is_deleted=False
        )
    except ConversationMetadata.DoesNotExist:
        return f"error: memory '{key}' not found"
    memory.delete()
    return f"deleted: {key}"
