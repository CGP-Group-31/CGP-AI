import json

def build_weekly_report_prompt(context: dict) -> str:

    schema = {
        "report_type": "weekly",
        "week_start": context["week_start"],
        "week_end": context["week_end"],
        "sections": {
            "Mood & Emotional Well-Being": "",
            "Engagement & Activity Patterns": "",
            "Medication Adherence Trends": "",
            "Meal & Nutrition Patterns": "",
            "Vital Signs Overview": "",
            "Safety & SOS Alerts": "",
            "Weekly Summary": "",
            "Caregiver Recommendations": ""
        }
    }

    return f"""
You are generating a professional weekly caregiver report.

The weekly report should be synthesized primarily from the 7 daily reports.

Return STRICT JSON only in this format:
{json.dumps(schema, indent=2)}

Rules:
- Each section max 4-5 lines
- Use daily reports as primary insight source
- Use vitals and SOS alerts as supporting evidence
- Do NOT invent medical conclusions
- If data missing say "insufficient data"

Weekly data:
{json.dumps(context, indent=2)}
""".strip()