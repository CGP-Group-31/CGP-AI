import httpx
from app.core.config import settings


async def get_daily_reports(elder_id: int, week_start: str, week_end: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/ai_system/weekly-reports/last-week-daily/{elder_id}",
            params={"start": week_start, "end": week_end}
        )
        if r.status_code != 200:
            return []
        return r.json()


async def get_vitals(elder_id: int, week_start: str, week_end: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/ai_system/weekly-reports/elder/{elder_id}/vitals/last-week",
            params={"week_start": week_start, "week_end": week_end}
        )
        if r.status_code != 200:
            return []
        return r.json()


async def get_sos_alerts(elder_id: int, week_start: str, week_end: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/ai_system/weekly-reports/sos-week/{elder_id}",
            params={"week_start": week_start, "week_end": week_end}
        )
        if r.status_code != 200:
            return []
        return r.json()


async def get_caregiver_notes(elder_id: int, week_start: str, week_end: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/ai_system/additional-info/elder/{elder_id}",
            params={"week_start": week_start, "week_end": week_end}
        )
        if r.status_code != 200:
            return []
        return r.json()