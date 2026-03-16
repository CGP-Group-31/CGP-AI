from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.daily_reports.service import generate_daily_report_for_elder

router = APIRouter(tags=["Daily Reports"])

class DailyReportRequest(BaseModel):
    elder_id: int
    report_date: str


@router.post("/reports/daily/generate")
async def generate_daily_reports(payload: DailyReportRequest):
    try:
        return await generate_daily_report_for_elder(
            elder_id=payload.elder_id,
            report_date=payload.report_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))