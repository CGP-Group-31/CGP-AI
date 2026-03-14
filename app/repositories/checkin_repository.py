from sqlalchemy import text
from app.core.db import engine


async def get_run_by_id(run_id: int) -> dict | None:
    sql = text("""
        SELECT TOP 1
            RunID,
            ScheduleID,
            ElderID,
            PlannedAt,
            TriggeredAt,
            CompletedAt,
            Status,
            UserResponse,
            DetectedMoodID,
            Notes
        FROM CheckInRuns
        WHERE RunID = :run_id
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"run_id": run_id}).mappings().fetchone()
    return dict(row) if row else None


async def get_current_checkin_for_elder(elder_id: int) -> dict | None:
    sql = text("""
        SELECT TOP 1
            r.RunID,
            r.ElderID,
            r.Status,
            r.TriggeredAt,
            r.PlannedAt,
            t.ThreadID
        FROM CheckInRuns r
        LEFT JOIN ChatThreads t ON t.RelatedRunID = r.RunID
        WHERE r.ElderID = :elder_id
          AND r.Status IN ('Triggered', 'WaitingUser')
        ORDER BY r.TriggeredAt DESC
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"elder_id": elder_id}).mappings().fetchone()
    return dict(row) if row else None


async def get_first_assistant_message(thread_id: int) -> dict | None:
    sql = text("""
        SELECT TOP 1
            MessageID,
            Content,
            CreatedAt
        FROM ChatMessages
        WHERE ThreadID = :thread_id
          AND Role = 'assistant'
        ORDER BY CreatedAt ASC
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"thread_id": thread_id}).mappings().fetchone()
    return dict(row) if row else None


async def update_run_to_waiting_user(run_id: int, note: str | None = None):
    sql = text("""
        UPDATE CheckInRuns
        SET Status = 'WaitingUser',
            Notes = :note
        WHERE RunID = :run_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"run_id": run_id, "note": note})


async def complete_run(
    run_id: int,
    user_response: str,
    detected_mood_id: int | None
):
    sql = text("""
        UPDATE CheckInRuns
        SET CompletedAt = SYSUTCDATETIME(),
            Status = 'Completed',
            UserResponse = :user_response,
            DetectedMoodID = :detected_mood_id
        WHERE RunID = :run_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {
            "run_id": run_id,
            "user_response": user_response,
            "detected_mood_id": detected_mood_id
        })