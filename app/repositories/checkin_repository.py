from sqlalchemy import text
from app.core.db import engine


async def get_run_by_id(run_id: int) -> dict | None:
    sql = text("""
        SELECT TOP 1
            RunID,
            ElderID,
            Status,
            TriggeredAt,
            CompletedAt,
            UserResponse,
            DetectedMoodID,
            WindowType,
            LocalDate,
            Notes
        FROM CheckInRuns
        WHERE RunID = :run_id
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {"run_id": run_id}).mappings().fetchone()

    return dict(row) if row else None


async def get_run_for_window(elder_id: int, window_type: str, local_date: str) -> dict | None:
    sql = text("""
        SELECT TOP 1
            RunID,
            ElderID,
            Status,
            TriggeredAt,
            CompletedAt,
            WindowType,
            LocalDate,
            Notes
        FROM CheckInRuns
        WHERE ElderID = :elder_id
          AND WindowType = :window_type
          AND LocalDate = :local_date
        ORDER BY RunID DESC
    """)
    with engine.begin() as conn:
        row = conn.execute(sql, {
            "elder_id": elder_id,
            "window_type": window_type,
            "local_date": local_date
        }).mappings().fetchone()

    return dict(row) if row else None


async def create_checkin_run(elder_id: int, window_type: str, local_date: str) -> int:
    sql = text("""
        INSERT INTO CheckInRuns (
            ElderID,
            PlannedAt,
            Status,
            WindowType,
            LocalDate
        )
        OUTPUT INSERTED.RunID
        VALUES (
            :elder_id,
            SYSUTCDATETIME(),
            'WaitingUser',
            :window_type,
            :local_date
        )
    """)
    with engine.begin() as conn:
        run_id = conn.execute(sql, {
            "elder_id": elder_id,
            "window_type": window_type,
            "local_date": local_date
        }).scalar_one()

    return int(run_id)

async def get_current_checkin_for_elder(elder_id: int) -> dict | None:
    sql = text("""
        SELECT TOP 1
            r.RunID,
            r.ElderID,
            r.Status,
            r.TriggeredAt,
            r.CompletedAt,
            r.WindowType,
            r.LocalDate,
            t.ThreadID
        FROM CheckInRuns r
        LEFT JOIN ChatThreads t ON t.RelatedRunID = r.RunID
        WHERE r.ElderID = :elder_id
          AND r.Status IN ('WaitingUser')
        ORDER BY r.RunID DESC
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


async def close_run(run_id: int, note: str | None = None):
    sql = text("""
        UPDATE CheckInRuns
        SET Status = 'Completed',
            CompletedAt = SYSUTCDATETIME(),
            Notes = :note
        WHERE RunID = :run_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {
            "run_id": run_id,
            "note": note
        })


async def close_thread_by_run_id(run_id: int):
    sql = text("""
        UPDATE ChatThreads
        SET ClosedAt = SYSUTCDATETIME()
        WHERE RelatedRunID = :run_id
          AND ClosedAt IS NULL
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"run_id": run_id})