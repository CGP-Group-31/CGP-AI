from app.daily_reports.client import get_elder_form, get_meal_adherence, get_med_adherence
from app.daily_reports.prompt import build_daily_report_prompt
from app.daily_reports.repository import report_exist_for_day, get_checkin_runs_for_day, save_daily_report, get_ai_chat_for_day, queue_semantic_index

from app.integrations.llm_client import ask_llm_for_daily_report


def _summarize_checkins(checkins: list[dict]) -> dict:
    completed = sum(1 for x in checkins if x.get("Status")=="Completed")
    missed = sum(1 for x in checkins if x.get("Status")=="Missed")
    failed = sum(1 for x in checkins if x.get("Status")=="Failed")
    waiting_user = sum(1 for x in checkins if x.get("Status")=="WaitingUser")

    moods = [x.get("DetectedMood") for x in checkins if x.get("DetectedMood")]
    responses = [x.get("UserResponse") for x in checkins if x.get("UserResponse")]

    return {
        "total_runs": len(checkins),
        "completed": completed,
        "missed": missed,
        "failed": failed,
        "waiting_user": waiting_user,
        "detected_moods": moods,
        "key_responses": responses[:5]
    }


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
       "items": items
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
    lines = [
        "Elder Day Overview:",
        f"- Mood: {report['elder_day_overview']['mood']}",
        f"- Sleep: {report['elder_day_overview']['sleep']}",
        f"- Water Intake: {report['elder_day_overview']['water_intake']}",
        f"- Appetite: {report['elder_day_overview']['appetite']}", 
        f"- Energy: {report['elder_day_overview']['energy']}", 
        f"- Overall Day: {report['elder_day_overview']['overall_day']}", 
        f"- Movement: {report['elder_day_overview']['movement']}",
        f"- Loneliness: {report['elder_day_overview']['loneliness']}",
        f"- Social Interaction: {report['elder_day_overview']['social_interaction']}",   
        f"- Stress: {report['elder_day_overview']['stress']}", 
        f"- Pain Report: {', '.join(report['pain_report']['pain_areas'])if report['pain_report']['pain_areas']  else 'No pain reported'}",
         f"Activities: {', '.join(report['activities']) if report['activities'] else 'No activities recorded'}",
        f"- AI Check-In Insights: {report.get('ai_chekin_insights','No AI check-in insights available')}", 
        f"- Medication Adherence: {report['medication_adherence']['headline']}",
    ]

    for d in report["medication_adherence"]["details"]:
        lines.append(f"- {d}")

    lines.append(
        "Meal Adherence: "
        f"Breakfast={report['meal_adherence']['breakfast']}, "
        f"Lunch={report['meal_adherence']['lunch']}, "
        f"Dinner={report['meal_adherence']['dinner']}"
    )

    if report["concerns"]:
        lines.append("Concerns:")
        for c in report["concerns"]:
            lines.append(f"- {c}")
    else:
        lines.append("Concerns: None significant noted.")
    
    lines.append(f"Caregiver Recommendations: {report['caregiver_recommendation']}")
    return "\n".join(lines)


def build_source_refs(checkin: list[dict], messages: list[dict]) -> list[dict]:
    ref = []

    for c in checkin:
        if c.get("RunID") is not None:
            ref.append({
                "source_type": "checkin_run",
                "source_id": int(c["RunID"])
            })

    for m in messages:
        if m.get("MessageID") is not None:
            ref.append({
                "source_type": "chat_message",
                "source_id": int(m["MessageID"])
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
    elder_messages = await get_ai_chat_for_day(elder_id, report_date)
    elder_form = await get_elder_form(elder_id, report_date)
    medication = await get_med_adherence(elder_id, report_date)
    meals = await get_meal_adherence(elder_id, report_date)
   
    context = {
        "elder_id": elder_id,
        "report_date": report_date,
        "elder_form": elder_form,
        "checkins": _summarize_checkins(checkins),
        "elder_messages": _summarize_elder_messages(elder_messages),
        "medication": _summarize_medication(medication),
        "meals": _summarize_meals(meals)
    }

    prompt = build_daily_report_prompt(context)
    report_obj = await ask_llm_for_daily_report(prompt)

    report_dict = report_obj.model_dump()
    fallback_text = build_fallback_text(report_dict)
    source_refs = build_source_refs(checkins, elder_messages)

    report_id = await save_daily_report(
        elder_id=elder_id,
        report_date=report_date,
        report_json=report_dict,
        report_text=fallback_text,
        source_refs=source_refs
    )

    await queue_semantic_index(
        source_type="care_report",
        source_id=report_id,
        elder_id=elder_id
    )

    return {
        "status": "success",
        "report_id": report_id,
        "elder_id": elder_id,
        "report_date": report_date,
        "report": report_dict,
        "source_count": len(source_refs)
    }
