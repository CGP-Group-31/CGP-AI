from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.weekly_report.service import generate_weekly_report_for_elder

router = APIRouter(tags=["Weekly Reports"])

class WeeklyReportRequest(BaseModel):
    elder_id: int
    week_start: str  # YYYY-MM-DD
    week_end: str    # YYYY-MM-DD


@router.post("/reports/weekly/generate")
async def generate_weekly_reports(payload: WeeklyReportRequest):
    try:
        return await generate_weekly_report_for_elder(
            elder_id=payload.elder_id,
            week_start=payload.week_start,
            week_end=payload.week_end
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))