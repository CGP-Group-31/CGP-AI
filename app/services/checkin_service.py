from app.integrations.llm_client import ask_llm, detect_mood, CHECKIN_TEMPERATURE, CHECKIN_MAX_TOKENS
from app.repositories.chat_repository import create_checkin_thread, get_thread_by_run_id, save_chat_message
from app.repositories.mood_repository import get_mood_id_by_name
from app.repositories.checkin_repository import (
    get_run_by_id,
    get_current_checkin_for_elder,
    get_first_assistant_message,
    update_run_to_waiting_user,
    complete_run,
)
from app.vector_store.retriever import search_memory
from app.vector_store.embedder import embed_query
from app.vector_store.indexer import index_message
from app.vector_store.document_builder import build_chat_index_doc


def _build_opening_message(schedule_name: str) -> str:
    s = (schedule_name or "").lower()

    if s == "morning":
        return "Good morning. How are you feeling today? Did you sleep well, and how is your energy this morning?"
    if s == "night":
        return "Good evening. How was your day today? How are you feeling now before resting for the night?"

    return "Hello. How are you feeling right now?"


def _format_memory(memory: list[dict]) -> str:
    if not memory:
        return "No relevant past conversations."

    lines = []
    for m in memory:
        created_at = m.get("created_at", "unknown_time")
        role = m.get("role", "unknown_role")
        mood = m.get("mood")
        content = m.get("content", "")
        mood_text = f", mood={mood}" if mood else ""
        lines.append(f"[{created_at}] ({role}{mood_text}): {content}")
    return "\n".join(lines)


async def start_checkin(run_id: int, elder_id: int, schedule_name: str) -> dict:
    existing_run = await get_run_by_id(run_id)
    if not existing_run:
        raise ValueError("CheckInRun not found.")

    thread_id = await get_thread_by_run_id(run_id)
    if not thread_id:
        thread_id = await create_checkin_thread(elder_id=elder_id, related_run_id=run_id)

    opening_message = _build_opening_message(schedule_name)

    assistant_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="assistant",
        content=opening_message
    )

    vector = await embed_query(opening_message)
    doc = build_chat_index_doc(
        message_id=assistant_message_id,
        elder_id=elder_id,
        thread_id=thread_id,
        role="assistant",
        content=opening_message,
        mood=None,
        source_type="checkin_message",
        vector=vector
    )
    await index_message(doc)

    await update_run_to_waiting_user(run_id, note=f"AI started. ThreadID={thread_id}")

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "elder_id": elder_id,
        "message": opening_message
    }


async def get_current_checkin(elder_id: int) -> dict:
    run = await get_current_checkin_for_elder(elder_id)
    if not run:
        return {
            "has_active_checkin": False,
            "elder_id": elder_id
        }

    thread_id = run.get("ThreadID")
    opening_message = await get_first_assistant_message(thread_id) if thread_id else None

    return {
        "has_active_checkin": True,
        "run_id": run["RunID"],
        "thread_id": thread_id,
        "elder_id": run["ElderID"],
        "status": run["Status"],
        "triggered_at": run["TriggeredAt"],
        "planned_at": run["PlannedAt"],
        "message": opening_message["Content"] if opening_message else None,
        "message_created_at": opening_message["CreatedAt"] if opening_message else None,
    }


async def respond_checkin(run_id: int, elder_id: int, message: str) -> dict:
    run = await get_run_by_id(run_id)
    if not run:
        raise ValueError("Check-in run not found.")

    if int(run["ElderID"]) != elder_id:
        raise ValueError("This run does not belong to the elder.")

    thread_id = await get_thread_by_run_id(run_id)
    if not thread_id:
        raise ValueError("No thread found for this check-in run.")

    detected_mood = await detect_mood(message)
    detected_mood_id = await get_mood_id_by_name(detected_mood)

    elder_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="elder",
        content=message,
        detected_mood_id=detected_mood_id
    )

    memory = await search_memory(elder_id, message, top_k=5)
    memory_text = _format_memory(memory)

    prompt = f"""
You are responding to an elderly user's daily check-in message.

Rules:
- Be warm, calm, and supportive.
- Keep the reply short and natural.
- Acknowledge the user's emotional state when relevant.
- If something sounds serious, suggest contacting a caregiver or doctor.

Relevant past conversations:
{memory_text}

Current elder message:
{message}
"""

    answer = await ask_llm(
        prompt=prompt,
        temperature=CHECKIN_TEMPERATURE,
        max_tokens=CHECKIN_MAX_TOKENS
    )

    assistant_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="assistant",
        content=answer
    )

    elder_vector = await embed_query(message)
    elder_doc = build_chat_index_doc(
        message_id=elder_message_id,
        elder_id=elder_id,
        thread_id=thread_id,
        role="elder",
        content=message,
        mood=detected_mood,
        source_type="checkin_message",
        vector=elder_vector
    )
    await index_message(elder_doc)

    assistant_vector = await embed_query(answer)
    assistant_doc = build_chat_index_doc(
        message_id=assistant_message_id,
        elder_id=elder_id,
        thread_id=thread_id,
        role="assistant",
        content=answer,
        mood=None,
        source_type="checkin_message",
        vector=assistant_vector
    )
    await index_message(assistant_doc)

    await complete_run(
        run_id=run_id,
        user_response=message,
        detected_mood_id=detected_mood_id
    )

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "elder_id": elder_id,
        "detected_mood": detected_mood,
        "answer": answer,
        "memory_count": len(memory)
    }