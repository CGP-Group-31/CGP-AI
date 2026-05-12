# app/services/retrieval_planner.py

from app.integrations.llm_client import ask_llm

PLANNER_TEMPERATURE = 0.1
PLANNER_MAX_TOKENS = 300


async def plan_retrieval(question: str) -> dict:
    """
    Agentic retrieval planner.

    Uses the SAME LLM model to decide:
    - which structured sources to load
    - whether memory retrieval is needed
    """
    prompt = f"""
You are an AI retrieval planning agent.
Your task:
Analyze the user question and decide which data sources are needed.
Available data sources:
1. profile
   - basic personal details
   - caregiver info
   - phone/address/gender/age

2. medical
   - allergies
   - chronic conditions
   - blood type
   - surgeries
   - emergency notes

3. appointments
   - doctor visits
   - hospital appointments
   - upcoming schedules

4. additional_info
   - caregiver notes
   - emotional observations
   - preferences
   - behavior notes
   - health goals

5. meals
   - breakfast/lunch/dinner
   - diet
   - meal status

6. chat_memory
   - previous conversations

7. report_memory
   - care reports
   - summaries
   - historical care analysis

Rules:
- Return ONLY valid JSON.
- No markdown.
- No explanations.
- Use true or false only.
- Enable only relevant data sources.
- For general conversations, usually use chat_memory.
- For personal questions, use profile.
- For emotional/contextual questions, use chat_memory and report_memory.
- For health questions, use medical.
- For food questions, use meals.
- For scheduling questions, use appointments.

Question:
"{question}"

Expected JSON format:
{{
  "use_profile": true,
  "use_medical": false,
  "use_appointments": false,
  "use_additional_info": false,
  "use_meals": false,
  "use_chat_memory": true,
  "use_report_memory": false,
  "reason": "short reason"
}}
"""

    try:
        response = await ask_llm(
            prompt=prompt,
            temperature=PLANNER_TEMPERATURE,
            max_tokens=PLANNER_MAX_TOKENS,
        )

        cleaned = (
            response.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        import json

        data = json.loads(cleaned)

        return {
            "use_profile": bool(data.get("use_profile", False)),
            "use_medical": bool(data.get("use_medical", False)),
            "use_appointments": bool(data.get("use_appointments", False)),
            "use_additional_info": bool(data.get("use_additional_info", False)),
            "use_meals": bool(data.get("use_meals", False)),
            "use_chat_memory": bool(data.get("use_chat_memory", True)),
            "use_report_memory": bool(data.get("use_report_memory", False)),
            "reason": data.get("reason", "No reason"),
        }

    except Exception:
        # fallback safe retrieval
        return {
            "use_profile": True,
            "use_medical": False,
            "use_appointments": False,
            "use_additional_info": False,
            "use_meals": False,
            "use_chat_memory": True,
            "use_report_memory": False,
            "reason": "Fallback retrieval plan",
        }