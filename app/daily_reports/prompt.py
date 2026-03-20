import json


def build_daily_report_prompt(context: dict) -> str:
    return f"""
You are generating a professional daily caregiver report for an elderly care system.

Use ONLY the provided structured data:
- elder form/profile data
- medication adherence data
- meal adherence data
- AI check-in data

Do NOT invent facts.
Do NOT add medical diagnoses.
Do NOT exaggerate.
Return STRICT JSON only.
Do NOT output markdown.

Important rules:
- Every section must contain 2 to 3 practical sentences.
- Base all insights strictly on the provided data.
- If data is limited, say that clearly in a natural professional way.
- A completed AI check-in with no response or mood should be described as completed participation with limited qualitative detail.
- If a check-in says "Closed by elder", do NOT automatically treat it as negative behavior.
- Caregiver follow-up should be practical and short.

Required JSON format:
{{
  "report_type": "daily",
  "report_date": "YYYY-MM-DD",
  "overall_summary": "string",
  "mood_observations": "string",
  "checkin_engagement": "string",
  "medication_insights": "string",
  "meal_insights": "string",
  "behavioral_observations": "string",
  "risk_flags": "string",
  "caregiver_follow_up": "string"
}}

Structured daily data:
{json.dumps(context, ensure_ascii=False, indent=2)}
""".strip()