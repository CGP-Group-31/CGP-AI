from app.core.timezone_utils import local_now_from_timezone_text, get_checkin_window
from app.integrations.llm_client import (ask_llm, detect_mood,
    CHECKIN_TEMPERATURE,
    CHECKIN_MAX_TOKENS,
)
from app.integrations.crud_client import get_elder_profile
from app.api.routes.user import get_user_basic_internal

from app.repositories.checkin_repository import close_run, close_thread_by_run_id
from app.repositories.user_repository import get_user_timezone
from app.repositories.checkin_repository import (
    get_run_by_id,
    get_run_for_window,
    create_checkin_run,
    get_current_checkin_for_elder,
    get_first_assistant_message,
)
from app.repositories.chat_repository import (
    create_checkin_thread,
    get_thread_by_run_id,
    save_chat_message,
)
from app.repositories.mood_repository import get_mood_id_by_name
from app.vector_store.retriever import search_memory
from app.vector_store.report_retriever import search_report_memory
from app.vector_store.embedder import embed_query
from app.vector_store.indexer import index_message
from app.vector_store.document_builder import build_chat_index_doc


def _build_opening_message(window_type: str) -> str:
    if window_type == "Morning":
        return "Good morning. How are you feeling today? Did you sleep well, and how is your energy this morning?"
    if window_type == "Night":
        return "Good evening. How was your day today? How are you feeling now before resting for the night?"
    return "Hello. How are you feeling right now?"


def _format_user_basic(user_basic: dict | None) -> str:
    if not user_basic:
        return "No basic user information available."

    return f"""Basic user information:
    Name: {user_basic.get("name")}
    Age: {user_basic.get("age")}
    Gender: {user_basic.get("gender")}

    The user is an elderly person receiving care support.
    Use a respectful, calm and supportive tone."""

def _format_chat_memory(memory: list[dict]) -> str:
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

def _format_report_memory(reports: list[dict]) -> str:
    if not reports:
        return "No relevant care reports."

    lines = []
    for r in reports:
        report_type = r.get("report_type", "unknown_report")
        period_start = r.get("period_start", "unknown_start")
        period_end = r.get("period_end", "unknown_end")
        created_at = r.get("created_at", "unknown_created")
        content = r.get("content", "")
        lines.append(
            f"[{created_at}] ({report_type}, {period_start} to {period_end}): {content}"
        )

    return "\n".join(lines)

def _format_structured_context(
    user_basic=None,
    elder_profile=None,) -> str:
    parts = []

    parts.append(_format_user_basic(user_basic))

    if elder_profile:
        caregiver = elder_profile.get("caregiver") or {}
        parts.append(f"""User profile:
Name: {elder_profile.get("ElderFullName")}
Email: {elder_profile.get("Email")}
Phone: {elder_profile.get("Phone")}
Date of birth: {elder_profile.get("DateOfBirth")}
Address: {elder_profile.get("Address")}
Gender: {elder_profile.get("Gender")}
Caregiver name: {caregiver.get("CaregiverFullName")}
Relationship for caregiver {caregiver.get("RelationshipType")}
Primary caregiver: {caregiver.get("IsPrimary")}
""")

    return "\n\n".join(parts)


async def _load_full_checkin_context(elder_id: int, query_text: str) -> dict:
    """ Uses only:
    - basic user info
    - user profile
    - chat memory
    - report memory"""
    user_basic = get_user_basic_internal(elder_id)
    elder_profile = await get_elder_profile(elder_id)

    chat_memory = await search_memory(elder_id, query_text, top_k=3)
    report_memory = await search_report_memory(elder_id, query_text, top_k=4)

    structured_context = _format_structured_context(
        user_basic=user_basic,
        elder_profile=elder_profile,
    )

    chat_memory_text = _format_chat_memory(chat_memory)
    report_memory_text = _format_report_memory(report_memory)

    return {
        "user_basic": user_basic,
        "elder_profile": elder_profile,
        "chat_memory": chat_memory,
        "report_memory": report_memory,
        "structured_context": structured_context,
        "chat_memory_text": chat_memory_text,
        "report_memory_text": report_memory_text,
    }


async def get_checkin_availability(elder_id: int) -> dict:
    tz_text = await get_user_timezone(elder_id)
    local_dt = local_now_from_timezone_text(tz_text or "")
    local_date = local_dt.date().isoformat()
    local_time = local_dt.strftime("%H:%M")
    window_type = get_checkin_window(local_dt)

    if not window_type:
        return {
            "elder_id": elder_id,
            "available": False,
            "window_type": None,
            "local_date": local_date,
            "local_time": local_time,
            "message": "No check-in window is active now."
        }

    existing_run = await get_run_for_window(elder_id, window_type, local_date)

    if existing_run:
        return {
            "elder_id": elder_id,
            "available": False,
            "window_type": window_type,
            "local_date": local_date,
            "local_time": local_time,
            "message": f"{window_type} check-in already started or completed."
        }

    return {
        "elder_id": elder_id,
        "available": True,
        "window_type": window_type,
        "local_date": local_date,
        "local_time": local_time,
        "message": f"{window_type} check-in is available."
    }


async def start_checkin(elder_id: int) -> dict:
    availability = await get_checkin_availability(elder_id)
    if not availability["available"]:
        raise ValueError(availability["message"])

    window_type = availability["window_type"]
    local_date = availability["local_date"]

    run_id = await create_checkin_run(
        elder_id=elder_id,
        window_type=window_type,
        local_date=local_date
    )

    thread_id = await create_checkin_thread(
        elder_id=elder_id,
        related_run_id=run_id
    )

    base_opening_message = _build_opening_message(window_type)

    context_data = await _load_full_checkin_context(
        elder_id=elder_id,
        query_text=f"{window_type} daily check-in"
    )

    prompt = f"""
You are the TrustCare elderly-care AI assistant.
Below is the default check-in opening message:
{base_opening_message}

Generate a natural opening message for a daily {window_type.lower()} check-in.
Rules:
- Keep the same meaning as the default message.
- Be warm, calm, and supportive.
- Keep it short and natural.
- Ask how the User is feeling.
- Sound conversational, not robotic.
- You may gently personalize using the context below.
- Do not mention databases, reports, APIs, retrieval, or technical details.

Structured data:
{context_data["structured_context"]}

Past chat memory:
{context_data["chat_memory_text"]}

Care report memory:
{context_data["report_memory_text"]}
"""

    opening_message = await ask_llm(
        prompt=prompt,
        temperature=CHECKIN_TEMPERATURE,
        max_tokens=CHECKIN_MAX_TOKENS
    )

    if not opening_message or not opening_message.strip():
        opening_message = base_opening_message

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

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "elder_id": elder_id,
        "window_type": window_type,
        "local_date": local_date,
        "message": opening_message,
        "default_message": base_opening_message,
        "chat_memory_count": len(context_data["chat_memory"]),
        "report_memory_count": len(context_data["report_memory"]),
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
        "window_type": run["WindowType"],
        "local_date": run["LocalDate"],
        "triggered_at": run["TriggeredAt"],
        "message": opening_message["Content"] if opening_message else None,
        "message_created_at": opening_message["CreatedAt"] if opening_message else None,
    }


async def respond_checkin(run_id: int, elder_id: int, message: str) -> dict:
    run = await get_run_by_id(run_id)
    if not run:
        raise ValueError("Check-in run not found.")

    if int(run["ElderID"]) != elder_id:
        raise ValueError("This run does not belong to the user.")

    if run["Status"] != "WaitingUser":
        raise ValueError("This check-in is not active.")

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

    context_data = await _load_full_checkin_context(
        elder_id=elder_id,
        query_text=message
    )

    prompt = f"""
You are responding to a TrustCare elderly user's daily check-in conversation.

Rules:
- Be warm, calm, and supportive.
- Keep the reply natural and conversational.
- Acknowledge the user's emotional state when relevant.
- Use structured data if helpful.
- Use memory if helpful.
- Do not mention databases, APIs, reports, retrieval, or technical details.

Structured data:
{context_data["structured_context"]}

Past chat memory:
{context_data["chat_memory_text"]}

Care report memory:
{context_data["report_memory_text"]}

Current user message:
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

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "elder_id": elder_id,
        "detected_mood": detected_mood,
        "answer": answer,
        "chat_memory_count": len(context_data["chat_memory"]),
        "report_memory_count": len(context_data["report_memory"]),
        "checkin_active": True
    }


async def close_checkin(run_id: int, elder_id: int) -> dict:
    run = await get_run_by_id(run_id)
    if not run:
        raise ValueError("Check-in run not found.")

    if int(run["ElderID"]) != elder_id:
        raise ValueError("This check-in does not belong to the user.")

    if run["Status"] == "Completed":
        return {
            "run_id": run_id,
            "elder_id": elder_id,
            "status": "Completed",
            "message": "Check-in already completed."
        }

    await close_run(run_id, note="Closed by elder")
    await close_thread_by_run_id(run_id)

    return {
        "run_id": run_id,
        "elder_id": elder_id,
        "status": "Completed",
        "message": "Check-in completed successfully."
    }