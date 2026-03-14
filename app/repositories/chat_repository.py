from sqlalchemy import text
from app.core.db import engine


async def get_or_create_open_thread(elder_id: int) -> int:
    find_sql = text("""
        SELECT TOP 1 ThreadID
        FROM ChatThreads
        WHERE ElderID = :elder_id
          AND ClosedAt IS NULL
          AND RelatedRunID IS NULL
        ORDER BY StartedAt DESC
    """)

    insert_sql = text("""
        INSERT INTO ChatThreads (ElderID)
        OUTPUT INSERTED.ThreadID
        VALUES (:elder_id)
    """)

    with engine.begin() as conn:
        row = conn.execute(find_sql, {"elder_id": elder_id}).fetchone()

        if row:
            return int(row[0])

        thread_id = conn.execute(insert_sql, {"elder_id": elder_id}).scalar_one()
        return int(thread_id)


async def create_checkin_thread(elder_id: int, related_run_id: int) -> int:
    sql = text("""
        INSERT INTO ChatThreads (ElderID, RelatedRunID)
        OUTPUT INSERTED.ThreadID
        VALUES (:elder_id, :related_run_id)
    """)
    with engine.begin() as conn:
        thread_id = conn.execute(sql, {
            "elder_id": elder_id,
            "related_run_id": related_run_id
        }).scalar_one()
    return int(thread_id)


async def get_thread_by_run_id(run_id: int) -> int | None:
    sql = text("""
        SELECT TOP 1 ThreadID
        FROM ChatThreads
        WHERE RelatedRunID = :run_id
        ORDER BY StartedAt DESC
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"run_id": run_id}).fetchone()
    return int(row[0]) if row else None


async def save_chat_message(
    thread_id: int,
    elder_id: int,
    role: str,
    content: str,
    detected_mood_id: int | None = None,
    safety_flag: str | None = None
) -> int:
    sql = text("""
        INSERT INTO ChatMessages (
            ThreadID,
            ElderID,
            Role,
            Content,
            DetectedMoodID,
            SafetyFlag
        )
        OUTPUT INSERTED.MessageID
        VALUES (
            :thread_id,
            :elder_id,
            :role,
            :content,
            :detected_mood_id,
            :safety_flag
        )
    """)
    with engine.begin() as conn:
        message_id = conn.execute(sql, {
            "thread_id": thread_id,
            "elder_id": elder_id,
            "role": role,
            "content": content,
            "detected_mood_id": detected_mood_id,
            "safety_flag": safety_flag
        }).scalar_one()
    return int(message_id)