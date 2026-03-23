import json

def build_weekly_report_prompt(context: dict) -> str:

    schema = {
        "report_type": "weekly",
        "week_start": context["week_start"],
        "week_end": context["week_end"],
        "mood_observations": "",
        "engagement_patterns": "",
        "medication_adherence": "",
        "nutrition_patterns": "",
        "vitals_overview": "",
        "safety_alerts": "",
        "weekly_summary": "",
        "caregiver_recommendations": ""
    }

    return f"""
You are generating a professional weekly caregiver report.

IMPORTANT OUTPUT RULES:
- Return ONLY a valid JSON object.
- Do NOT include explanations.
- Do NOT include markdown or code blocks.
- The response MUST start with {{ and end with }}.

The JSON MUST follow this exact structure:

{json.dumps(schema, indent=2)}

Guidelines:
- Each section must be maximum 4–5 lines.
- Use daily reports as the primary source.
- Use vitals and SOS alerts only as supporting information.
- Do NOT invent medical conclusions.
- If information is missing write: "insufficient data".

Weekly data:
{json.dumps(context)}
""".strip()