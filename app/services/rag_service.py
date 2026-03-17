# app/services/rag_service.py

from app.vector_store.retriever import search_memory
from app.vector_store.report_retriever import search_report_memory
from app.vector_store.embedder import embed_query
from app.vector_store.indexer import index_message
from app.vector_store.document_builder import build_chat_index_doc

from app.integrations.llm_client import (
    ask_llm,
    detect_mood,
    CHAT_TEMPERATURE,
    CHAT_MAX_TOKENS,
)

from app.integrations.crud_client import (
    get_elder_profile,
    get_medical_profile,
    get_upcoming_appointments,
    get_latest_additional_info,
    get_today_meals,
)

from app.services.question_router import detect_primary_intent

from app.repositories.chat_repository import (
    get_or_create_open_thread,
    save_chat_message,
)

from app.repositories.mood_repository import get_mood_id_by_name

from app.api.routes.user import get_user_basic_internal


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


def _format_user_basic_as_structured(user_basic: dict | None) -> str:
    if not user_basic:
        return "Basic user info not available."

    return f"""Basic user information:
Name: {user_basic.get("name")}
Age: {user_basic.get("age")}
Gender: {user_basic.get("gender")}
"""


def _format_structured_context(
    intent: str,
    user_basic=None,
    elder_profile=None,
    medical_profile=None,
    appointments=None,
    additional_info=None,
    meals=None,
) -> str:
    parts = []

    # Always include basic user info if available
    parts.append(_format_user_basic_as_structured(user_basic))

    if intent == "profile" and elder_profile:
        caregiver = elder_profile.get("caregiver") or {}
        parts.append(f"""User profile:
Name: {elder_profile.get("ElderFullName")}
Email: {elder_profile.get("Email")}
Phone: {elder_profile.get("Phone")}
Date of birth: {elder_profile.get("DateOfBirth")}
Address: {elder_profile.get("Address")}
Gender: {elder_profile.get("Gender")}
Caregiver name: {caregiver.get("CaregiverFullName")}
Relationship type: {caregiver.get("RelationshipType")}
Primary caregiver: {caregiver.get("IsPrimary")}
""")

    elif intent == "medical" and medical_profile:
        parts.append(f"""Medical profile:
Blood type: {medical_profile.get("BloodType")}
Allergies: {medical_profile.get("Allergies")}
Chronic conditions: {medical_profile.get("ChronicConditions")}
Emergency notes: {medical_profile.get("EmergencyNotes")}
Past surgeries: {medical_profile.get("PastSurgeries")}
""")

    elif intent == "appointments" and appointments:
        lines = []
        for a in appointments:
            lines.append(
                f'{a.get("AppointmentDate")} {a.get("AppointmentTime")} - '
                f'{a.get("Title")} at {a.get("Location")} with {a.get("DoctorName")}'
            )
        parts.append("Upcoming appointments:\n" + "\n".join(lines))

    elif intent == "additional_info" and additional_info:
        lines = []
        for item in additional_info:
            lines.append(
                f'Recorded at {item.get("recorded_at")}: '
                f'Cognitive notes: {item.get("cognitive_behavior_notes")}; '
                f'Preferences: {item.get("preferences")}; '
                f'Social/emotional notes: {item.get("social_emotional_behavior_notes")}; '
                f'Health goals: {item.get("health_goals")}; '
                f'Observations: {item.get("special_notes_observations")}'
            )
        parts.append("Latest caregiver notes:\n" + "\n".join(lines))

    elif intent == "meals" and meals:
        lines = []
        for item in meals:
            lines.append(
                f'{item.get("MealTime")} - '
                f'Status: {item.get("Status")}, '
                f'Diet: {item.get("Diet")}, '
                f'ScheduledFor: {item.get("ScheduledFor")}'
            )
        parts.append("Today's meals:\n" + "\n".join(lines))

    return "\n\n".join(parts)


async def generate_answer(elder_id: int, question: str):
    thread_id = await get_or_create_open_thread(elder_id)

    try:
        detected_mood_name = await detect_mood(question)
    except Exception:
        detected_mood_name = "Neutral"

    detected_mood_id = await get_mood_id_by_name(detected_mood_name)

    elder_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="elder",
        content=question,
        detected_mood_id=detected_mood_id,
    )

    # Basic info from same AI DB
    user_basic = get_user_basic_internal(elder_id)

    intent = detect_primary_intent(question)

    elder_profile = None
    medical_profile = None
    appointments = []
    additional_info = []
    meals = []

    if intent == "profile":
        elder_profile = await get_elder_profile(elder_id)

    elif intent == "medical":
        medical_profile = await get_medical_profile(elder_id)

    elif intent == "appointments":
        appointments = await get_upcoming_appointments(elder_id)

    elif intent == "additional_info":
        additional_info = await get_latest_additional_info(elder_id)

    elif intent == "meals":
        meals = await get_today_meals(elder_id)

    structured_context = _format_structured_context(
        intent=intent,
        user_basic=user_basic,
        elder_profile=elder_profile,
        medical_profile=medical_profile,
        appointments=appointments,
        additional_info=additional_info,
        meals=meals,
    )

    chat_memory = await search_memory(elder_id, question, top_k=3)
    report_memory = await search_report_memory(elder_id, question, top_k=1)

    chat_memory_text = _format_chat_memory(chat_memory)
    report_memory_text = _format_report_memory(report_memory)

    prompt = f"""
You are a helpful elderly-care AI companion of TrustCare system that was deveoped by Group 31. 
The following structured data about the current user is reliable.
If the user's question asks about age, gender, name, profile or similar details,
answer directly from the structured data below.

Rules:
- Be supportive and easy to understand.
- Keep the answer concise and natural.
- Prefer structured data over memory.
- Do not invent facts.
- Do not mention databases, APIs, or retrieval systems.
- If data is missing, say so simply.

Primary intent:
{intent}

Structured data:
{structured_context}

Past chat memory:
{chat_memory_text}

Care report memory:
{report_memory_text}

Question:
{question}
"""

    answer = await ask_llm(
        prompt=prompt,
        temperature=CHAT_TEMPERATURE,
        max_tokens=CHAT_MAX_TOKENS,
    )

    assistant_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="assistant",
        content=answer,
    )

    elder_vector = await embed_query(question)
    elder_doc = build_chat_index_doc(
        message_id=elder_message_id,
        elder_id=elder_id,
        thread_id=thread_id,
        role="elder",
        content=question,
        mood=detected_mood_name,
        vector=elder_vector,
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
        vector=assistant_vector,
    )
    await index_message(assistant_doc)

    return {
        "elder_id": elder_id,
        "thread_id": thread_id,
        "question": question,
        "intent": intent,
        "detected_mood": detected_mood_name,
        "answer": answer,
        "user_basic_used": user_basic,
        "structured_context_used": structured_context,
        "chat_memory_count": len(chat_memory),
        "report_memory_count": len(report_memory),
        "saved_messages": {
            "elder_message_id": elder_message_id,
            "assistant_message_id": assistant_message_id,
        },
    }