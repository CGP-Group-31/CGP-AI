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
    intent: str,
    elder_profile=None,
    medical_profile=None,
    appointments=None,
    additional_info=None,
    meals=None,
) -> str:
    """
    Keep this very focused.
    Only one primary intent should usually contribute structured data.
    """
    if intent == "profile" and elder_profile:
        caregiver = elder_profile.get("caregiver") or {}
        return f"""Elder profile:
Name: {elder_profile.get("ElderFullName")}
Email: {elder_profile.get("Email")}
Phone: {elder_profile.get("Phone")}
Date of birth: {elder_profile.get("DateOfBirth")}
Address: {elder_profile.get("Address")}
Gender: {elder_profile.get("Gender")}
Caregiver name: {caregiver.get("CaregiverFullName")}
Relationship type: {caregiver.get("RelationshipType")}
Primary caregiver: {caregiver.get("IsPrimary")}
"""

    if intent == "medical" and medical_profile:
        return f"""Medical profile:
Blood type: {medical_profile.get("BloodType")}
Allergies: {medical_profile.get("Allergies")}
Chronic conditions: {medical_profile.get("ChronicConditions")}
Emergency notes: {medical_profile.get("EmergencyNotes")}
Past surgeries: {medical_profile.get("PastSurgeries")}
"""

    if intent == "appointments" and appointments:
        lines = []
        for a in appointments:
            lines.append(
                f'{a.get("AppointmentDate")} {a.get("AppointmentTime")} - '
                f'{a.get("Title")} at {a.get("Location")} with {a.get("DoctorName")}'
            )
        return "Upcoming appointments:\n" + "\n".join(lines)

    if intent == "additional_info" and additional_info:
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
        return "Latest caregiver notes:\n" + "\n".join(lines)

    if intent == "meals" and meals:
        lines = []
        for item in meals:
            lines.append(
                f'{item.get("MealTime")} - '
                f'Status: {item.get("Status")}, '
                f'Diet: {item.get("Diet")}, '
                f'ScheduledFor: {item.get("ScheduledFor")}'
            )
        return "Today's meals:\n" + "\n".join(lines)

    return "No structured data retrieved."


async def generate_answer(elder_id: int, question: str):
    # 1) Get or create normal chat thread
    thread_id = await get_or_create_open_thread(elder_id)

    # 2) Detect mood for elder message
    try:
        detected_mood_name = await detect_mood(question)
    except Exception:
        detected_mood_name = "Neutral"

    detected_mood_id = await get_mood_id_by_name(detected_mood_name)

    # 3) Save elder message first
    elder_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="elder",
        content=question,
        detected_mood_id=detected_mood_id,
    )

    # 4) Detect one primary intent only
    intent = detect_primary_intent(question)

    # 5) Fetch only the needed structured truth
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

    # 6) Build structured context
    structured_context = _format_structured_context(
        intent=intent,
        elder_profile=elder_profile,
        medical_profile=medical_profile,
        appointments=appointments,
        additional_info=additional_info,
        meals=meals,
    )

    # 7) Retrieve memory
    # Keep this small and stable for now
    chat_memory = await search_memory(elder_id, question, top_k=3)
    report_memory = await search_report_memory(elder_id, question, top_k=1)

    chat_memory_text = _format_chat_memory(chat_memory)
    report_memory_text = _format_report_memory(report_memory)

    # 8) Build final prompt
    prompt = f"""
You are an elderly-care AI assistant.

Answer the elder's question using:
1. structured data first, if available
2. past chat memory only if relevant
3. care report memory only if helpful

Rules:
- Be supportive and easy to understand.
- Keep the answer concise and natural.
- If structured data already answers the question, use it directly.
- Do not invent facts.
- Do not mention retrieval, APIs, databases, or system internals.
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

    # 9) Ask LLM
    answer = await ask_llm(
        prompt=prompt,
        temperature=CHAT_TEMPERATURE,
        max_tokens=CHAT_MAX_TOKENS,
    )

    # 10) Save assistant message
    assistant_message_id = await save_chat_message(
        thread_id=thread_id,
        elder_id=elder_id,
        role="assistant",
        content=answer,
    )

    # 11) Index elder message into chat memory index
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

    # 12) Index assistant message into chat memory index
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

    # 13) Return debug-friendly response for now
    return {
        "elder_id": elder_id,
        "thread_id": thread_id,
        "question": question,
        "intent": intent,
        "detected_mood": detected_mood_name,
        "answer": answer,
        "structured_context_used": structured_context,
        "chat_memory_count": len(chat_memory),
        "report_memory_count": len(report_memory),
        "saved_messages": {
            "elder_message_id": elder_message_id,
            "assistant_message_id": assistant_message_id,
        },
    }