from app.daily_reports.client import get_elder_form, get_meal_adherence, get_med_adherence
from app.daily_reports.prompt import build_daily_report_prompt
from app.daily_reports.repository import report_exist_for_day, get_checkin_runs_for_day, save_daily_report
from app.integrations.llm_client import ask_llm_for_daily_report
from app.vector_store.report_indexer import index_daily_weekly_report

def _summarize_checkins(checkins: list[dict]) -> dict:
    completed = sum(1 for x in checkins if x.get("Status") == "Completed")
    missed = sum(1 for x in checkins if x.get("Status") == "Missed")
    failed = sum(1 for x in checkins if x.get("Status") == "Failed")
    waiting_user = sum(1 for x in checkins if x.get("Status") == "WaitingUser")

    responses = []
    notes = []
    moods = []
    windows_present = []
    closed_by_elder_count = 0

    for x in checkins:
        window = x.get("WindowType")
        if window:
            windows_present.append(window)

        response = x.get("UserResponse")
        if response and str(response).strip():
            responses.append(str(response).strip())

        mood = x.get("DetectedMood")
        if mood and str(mood).strip():
            moods.append(str(mood).strip())

        note = x.get("Notes")
        if note and str(note).strip():
            clean_note = str(note).strip()
            notes.append(clean_note)
            if clean_note.lower() == "closed by elder":
                closed_by_elder_count += 1

    return {
        "total_runs": len(checkins),
        "completed": completed,
        "missed": missed,
        "failed": failed,
        "waiting_user": waiting_user,
        "windows_present": sorted(list(set(windows_present))),
        "response_count": len(responses),
        "mood_count": len(moods),
        "closed_by_elder_count": closed_by_elder_count,
        "key_responses": responses[:5],
        "notes": notes[:10],
        "moods": moods[:10],
        "data_quality": {
            "has_meaningful_response": len(responses) > 0,
            "has_mood_signal": len(moods) > 0,
            "limited_detail": len(responses) == 0 and len(moods) == 0,
        },
    }

'''
def _summarize_elder_messages(messages: list[dict]) -> list[dict]:
    result = []
    for m in messages[:10]:
        result.append({
            "message_id": m.get("MessageID"),
            "content": m.get("Content"),
            "created_at": str(m.get("CreatedAt")),
            "detected_mood": m.get("DetectedMood"),
            "safety_flag": m.get("SafetyFlag")
        })
    return result
'''

def _summarize_medication(items: list[dict]) -> dict:
    total = len(items)
    taken = sum(1 for x in items if str(x.get("status", "")).lower() == "taken")
    missed = sum(1 for x in items if str(x.get("status", "")).lower() == "missed")
    skipped = sum(1 for x in items if str(x.get("status", "")).lower() == "skipped")
   
    return {
       "total": total,
       "taken": taken,
       "missed": missed,
       "skipped": skipped,
       "items": items[:20]
   }



def _summarize_meals(items: list[dict]) -> dict:
    total = len(items)
    taken = sum(1 for x in items if str(x.get("status", "")).lower() == "taken")
    missed = sum(1 for x in items if str(x.get("status", "")).lower() == "missed")
    skipped = sum(1 for x in items if str(x.get("status", "")).lower() == "skipped")
   
    return {
       "total": total,
       "taken": taken,
       "missed": missed,
       "skipped": skipped,
       "items": items
   }


def build_fallback_text(report: dict) -> str:
    return "\n\n".join([
        f"Overall Daily Summary:\n{report.get('overall_summary', '')}",
        f"Mood and Emotional Observations:\n{report.get('mood_observations', '')}",
        f"Check-In Participation and Engagement:\n{report.get('checkin_engagement', '')}",
        f"Medication Adherence Insights:\n{report.get('medication_insights', '')}",
        f"Meal and Nutrition Insights:\n{report.get('meal_insights', '')}",
        f"Behavioral or Cognitive Observations:\n{report.get('behavioral_observations', '')}",
        f"Risk Flags or Concerns:\n{report.get('risk_flags', '')}",
        f"Caregiver Follow-Up Suggestions:\n{report.get('caregiver_follow_up', '')}",
    ]).strip()



def build_source_refs(checkin: list[dict]) -> list[dict]:
    ref = []

    for c in checkin:
        if c.get("RunID") is not None:
            ref.append({
                "source_type": "checkin_run",
                "source_id": int(c["RunID"])
            })

    seen = set()
    unique = []
    for r in ref:
        key = (r["source_type"], r["source_id"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique





async def generate_daily_report_for_elder(elder_id: int, report_date: str) -> dict:
    if await report_exist_for_day(elder_id, report_date):
        return {
            "status": "exists",
            "elder_id": elder_id,
            "report_date": report_date,
            "message": "Daily report already exists."

        }
    checkins = await get_checkin_runs_for_day(elder_id, report_date)
    elder_form = await get_elder_form(elder_id, report_date)
    medication = await get_med_adherence(elder_id, report_date)
    meals = await get_meal_adherence(elder_id, report_date)
   
    context = {
        "elder_id": elder_id,
        "report_date": report_date,
        "elder_form": elder_form,
        "checkins": _summarize_checkins(checkins),
        "medication": _summarize_medication(medication),
        "meals": _summarize_meals(meals)
    }

    prompt = build_daily_report_prompt(context)
    report_obj = await ask_llm_for_daily_report(prompt)
    report_dict = report_obj.model_dump()

    fallback_text = build_fallback_text(report_dict)
    source_refs = build_source_refs(checkins)

    report_id = await save_daily_report(
        elder_id=elder_id,
        report_date=report_date,
        report_json=report_dict,
        report_text=fallback_text,
        source_refs=source_refs
    )

    await index_daily_weekly_report(
    report_id=report_id,
    elder_id=elder_id,
    report_type="daily",
    period_start=report_date,
    period_end=report_date,
    content=fallback_text
    
)

    return {
        "status": "success",
        "report_id": report_id,
        "elder_id": elder_id,
        "report_date": report_date,
        "report": report_dict,
        "source_count": len(source_refs)
    }
