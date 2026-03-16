import json

def build_daily_report_prompt(context:dict)-> str:
    return f"""
You are generating a structured daily elder report for an elderly care system.

Use ONLY the provided data.
Do NOT invent facts.
Do NOT add medical diagnoses.
Do NOT output markdown.
Return STRICT JSON only.

Required JSON format:
{{
  "report_type": "daily",
  "report_date": "YYYY-MM-DD",
  "elder_day_overview": {{
    "mood": "string",
    "sleep": "string",
    "water_intake": "string",
    "appetite": "string",
    "energy": "string",
    "overall_day": "string",
    "movement": "string",
    "loneliness": "string",
    "social_interaction": "string",
    "stress": "string"
  }},
  "pain_report": {{
    "has_pain": true,
    "pain_areas": ["string"]
  }},
  "activities": ["string"],
  "ai_checkin_insights": "string",
  "medication_adherence": {{
    "headline": "string",
    "details": ["string"]
  }},
  "meal_adherence": {{
    "breakfast": "string",
    "lunch": "string",
    "dinner": "string"
  }},
  "concerns": ["string"],
  "caregiver_recommendation": "string",
}}

Rules:
- Keep the writing concise and practical.
- If there are no major concerns, return an empty concerns list.
- Medication headline should be short.
- AI check-in insights should summarize the same-day check-ins and elder messages only.
- Do not mention missing data sources explicitly.

Structured daily data:
{json.dumps(context, ensure_ascii=False, indent=2)}
""".strip()
