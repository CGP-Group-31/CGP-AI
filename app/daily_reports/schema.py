from typing import List, Literal
from pydantic import BaseModel, Field


class ElderDayOverview(BaseModel):
    mood: str
    sleep: str
    water_intake: str
    appetite: str
    energy: str
    overall_day: str
    movement: str
    loneliness: str
    social_interaction: str
    stress: str


class PainReport(BaseModel):
    has_pain: bool
    pain_areas: List[str] = Field(default_factory=list)


class MedicationAdherenceSection(BaseModel):
    headline: str
    details: List[str] = Field(default_factory=list)


class MealAdherenceSection(BaseModel):
    breakfast: str
    lunch: str
    dinner: str


class DailyElderReport(BaseModel):
    report_type: Literal["daily"] = "daily"
    report_date: str

    elder_day_overview: ElderDayOverview
    pain_report: PainReport
    activities: List[str] = Field(default_factory=list)
    ai_checkin_insights: str
    medication_adherence: MedicationAdherenceSection
    meal_adherence: MealAdherenceSection
    concerns: List[str] = Field(default_factory=list)
    caregiver_recommendation: str
