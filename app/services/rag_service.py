from app.vector_store.retriever import search_memory
from app.vector_store.embedder import embed_query
from app.vector_store.indexer import index_message
from app.vector_store.document_builder import build_chat_index_doc
from app.integrations.llm_client import (
    ask_llm,
    detect_mood,
    CHAT_TEMPERATURE,
    CHAT_MAX_TOKENS,
)
from app.repositories.chat_repository import (
    get_or_create_open_thread,
    save_chat_message,
)
from app.repositories.mood_repository import get_mood_id_by_name


def _format_memory(memory: list[dict]) -> str:
    if not memory:
        return "No relevant past conversations."

    lines = []
    for m in memory:
        created_at = m.get("created_at", "unknown_time")
        role = m.get("role", "unknown_role")
        content = m.get("content", "")
        mood = m.get("mood")
        mood_text = f", mood={mood}" if mood else ""
        lines.append(f"[{created_at}] ({role}{mood_text}): {content}")

    return "\n".join(lines)


async def generate_answer(elder_id: int, question: str):
    thread_id = await get_or_create_open_thread(elder_id)

    # 1. detect mood for elder message
    detected_mood_name = await detect_mood(question)
    detected_mood_id = await get_mood_id_by_name(detected_mood_name)

    # 2. save elder message with mood
    elder_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="elder",
        content=question,
        detected_mood_id=detected_mood_id
    )

    # 3. retrieve memory
    memory = await search_memory(elder_id, question, top_k=5)
    memory_text = _format_memory(memory)

    context = f"""
    Relevant past conversations:
    {memory_text}
    """

    prompt = f"""
    Use the following context to answer the elder's question.

    Rules:
    - Be supportive and easy to understand.
    - Keep the answer concise and natural.
    - Use the past conversation context only when relevant.
    - Do not mention raw database or retrieval details.
    - Do not invent medical facts.

    Context:
    {context}

    Question:
    {question}
    """

    # 4. generate assistant answer
    answer = await ask_llm(
        prompt=prompt,
        temperature=CHAT_TEMPERATURE,
        max_tokens=CHAT_MAX_TOKENS
    )

    # 5. save assistant answer (no mood)
    assistant_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="assistant",
        content=answer,
        detected_mood_id=None
    )

    # 6. index elder message with mood
    elder_vector = await embed_query(question)
    elder_doc = build_chat_index_doc(
        message_id=elder_message_id,
        elder_id=elder_id,
        thread_id=thread_id,
        role="elder",
        content=question,
        mood=detected_mood_name,
        vector=elder_vector
    )
    await index_message(elder_doc)

    # 7. index assistant answer without mood
    assistant_vector = await embed_query(answer)
    assistant_doc = build_chat_index_doc(
        message_id=assistant_message_id,
        elder_id=elder_id,
        thread_id=thread_id,
        role="assistant",
        content=answer,
        mood=None,
        vector=assistant_vector
    )
    await index_message(assistant_doc)

    return {
        "elder_id": elder_id,
        "thread_id": thread_id,
        "question": question,
        "detected_mood": detected_mood_name,
        "answer": answer,
        "memory_count": len(memory),
        "saved_messages": {
            "elder_message_id": elder_message_id,
            "assistant_message_id": assistant_message_id
        }
    }