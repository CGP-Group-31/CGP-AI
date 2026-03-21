from typing import Literal
from pydantic import BaseModel


class WeeklyElderReport(BaseModel):
    report_type: Literal["weekly"] = "weekly"
    week_start: str
    week_end: str

    mood_observations: str
    engagement_patterns: str
    medication_adherence: str
    nutrition_patterns: str
    vitals_overview: str
    safety_alerts: str
    weekly_summary: str
    caregiver_recommendations: str