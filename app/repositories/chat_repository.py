# 
from sqlalchemy import text
from app.core.db import engine


async def get_or_create_open_thread(elder_id: int) -> int:
    """
    Get latest open thread for elder.
    If no open thread exists, create one.
    """
    find_sql = text("""SELECT TOP 1 ThreadID
        FROM ChatThreads
        WHERE ElderID = :elder_id
          AND ClosedAt IS NULL
        ORDER BY StartedAt DESC""")

    insert_sql = text("""INSERT INTO ChatThreads (ElderID)
        OUTPUT INSERTED.ThreadID
        VALUES (:elder_id)""")

    with engine.begin() as conn:
        row = conn.execute(find_sql, {"elder_id": elder_id}).fetchone()

        if row:
            return int(row[0])

        thread_id = conn.execute(insert_sql, {"elder_id": elder_id}).scalar_one()
        return int(thread_id)



async def save_chat_message(
    thread_id: int,
    elder_id: int,
    role: str,
    content: str,
    detected_mood_id: int | None = None,
    safety_flag: str | None = None
) -> int:
    sql = text("""INSERT INTO ChatMessages (
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
            :safety_flag)""")

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