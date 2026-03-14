from sqlalchemy import text
from app.core.db import engine


async def get_mood_id_by_name(mood_name: str) -> int | None:
    sql = text("""SELECT MoodID FROM MoodTypes WHERE MoodName = :mood_name""")
    with engine.begin() as conn:
        row = conn.execute(sql, {"mood_name": mood_name}).fetchone()
    return int(row[0]) if row else None