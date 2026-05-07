import json
from app.weekly_report.client import (
    get_daily_reports,
    get_vitals,
    get_sos_alerts,
    get_caregiver_notes,
)
from app.vector_store.report_indexer import index_daily_weekly_report
from app.weekly_report.prompt import build_weekly_report_prompt
from app.weekly_report.repository import report_exist_for_week, save_weekly_report
from app.integrations.llm_client import ask_llm_for_weekly_report


def build_weekly_fallback_text(report: dict) -> str:
    return "\n\n".join([
        f"Mood & Emotional Well-Being:\n{report.get('mood_observations','')}",
        f"Engagement & Activity Patterns:\n{report.get('engagement_patterns','')}",
        f"Medication Adherence Trends:\n{report.get('medication_adherence','')}",
        f"Meal & Nutrition Patterns:\n{report.get('nutrition_patterns','')}",
        f"Vital Signs Overview:\n{report.get('vitals_overview','')}",
        f"Safety & SOS Alerts:\n{report.get('safety_alerts','')}",
        f"Weekly Summary:\n{report.get('weekly_summary','')}",
        f"Caregiver Recommendations:\n{report.get('caregiver_recommendations','')}",
    ]).strip()


def build_source_refs(daily_reports, vitals, sos_alerts):

    refs = []

    for r in daily_reports:
        if r.get("report_id"):
            refs.append({"source_type": "daily_report", "source_id": int(r["report_id"])})

    for v in vitals:
        if v.get("vital_id"):
            refs.append({"source_type": "vital", "source_id": int(v["vital_id"])})

    for s in sos_alerts:
        if s.get("alert_id"):
            refs.append({"source_type": "sos", "source_id": int(s["alert_id"])})

    seen = set()
    unique = []

    for r in refs:
        key = (r["source_type"], r["source_id"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


async def generate_weekly_report_for_elder(elder_id: int, week_start: str, week_end: str):

    if await report_exist_for_week(elder_id, week_start, week_end):
        return {
            "status": "exists",
            "elder_id": elder_id,
            "week_start": week_start,
            "week_end": week_end,
            "message": "Weekly report already exists.",
        }

    daily_reports = await get_daily_reports(elder_id, week_start, week_end)
    vitals = await get_vitals(elder_id, week_start, week_end)
    sos_alerts = await get_sos_alerts(elder_id, week_start, week_end)
    caregiver_notes = await get_caregiver_notes(elder_id, week_start, week_end)

    context = {
        "elder_id": elder_id,
        "week_start": week_start,
        "week_end": week_end,
        "daily_reports": daily_reports,
        "vitals": vitals,
        "sos_alerts": sos_alerts,
        "caregiver_notes": caregiver_notes,
    }

    prompt = build_weekly_report_prompt(context)

    try:
        report_obj = await ask_llm_for_weekly_report(prompt)

        if hasattr(report_obj, "model_dump"):
            report_json = report_obj.model_dump()
        else:
            report_json = dict(report_obj)

    except Exception as e:
        return {"status": "error", "message": str(e)}

    fallback_text = build_weekly_fallback_text(report_json)
    source_refs = build_source_refs(daily_reports, vitals, sos_alerts)

    try:
        report_id = await save_weekly_report(
            elder_id=elder_id,
            week_start=week_start,
            week_end=week_end,
            report_json=report_json,
            report_text=fallback_text,
            source_refs=source_refs,
        )
    except Exception:
        return {"status": "error", "message": "DB insert failed."}

    try:
        await index_daily_weekly_report(
            report_id=report_id,
            elder_id=elder_id,
            report_type="weekly",
            period_start=week_start,
            period_end=week_end,
            content=fallback_text,
        )
    except Exception:
        pass

    return {
        "status": "success",
        "report_id": report_id,
        "elder_id": elder_id,
        "week_start": week_start,
        "week_end": week_end,
        "report": report_json,
        "source_count": len(source_refs),
    }