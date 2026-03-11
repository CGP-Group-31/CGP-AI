from datetime import datetime, timezone


def build_chat_index_doc(
    message_id: int,
    elder_id: int,
    thread_id: int,
    role: str,
    content: str,
    mood: str | None = None,
    source_type: str = "chat_message",
    created_at: str | None = None,
    vector: list[float] | None = None
) -> dict:
    return {
        "id": f"chat-{message_id}",
        "elder_id": elder_id,
        "thread_id": thread_id,
        "source_type": source_type,
        "role": role,
        "mood": mood,
        "content": content,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "content_vector": vector or []
    }