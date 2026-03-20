from typing import List, Literal
from pydantic import BaseModel, Field


class DailyElderReport(BaseModel):
    report_type: Literal["daily"] = "daily"
    report_date: str

    overall_summary: str
    mood_observations: str
    checkin_engagement: str
    medication_insights: str
    meal_insights: str
    behavioral_observations: str
    risk_flags: str
    caregiver_follow_up: str
