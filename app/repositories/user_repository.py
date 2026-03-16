from sqlalchemy import text
from app.core.db import engine


async def get_user_timezone(elder_id: int) -> str | None:
    sql = text("""
        SELECT Timezone
        FROM Users
        WHERE UserID = :elder_id
    """)

    with engine.begin() as conn:
        row = conn.execute(sql, {"elder_id": elder_id}).fetchone()

    return row[0] if row else None