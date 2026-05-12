from app.integrations.llm_client import ask_llm


async def plan_retrieval(question: str) -> dict:
    prompt = f"""
You are a retrieval planning AI.

Your task:
Determine what information sources are needed
to answer the user's question.

Available sources:
- profile
- medical
- appointments
- meals
- additional_info
- chat_memory
- report_memory

Return ONLY valid JSON.

Question:
{question}

JSON format:
{{
  "profile": true,
  "medical": false,
  "appointments": false,
  "meals": false,
  "additional_info": false,
  "chat_memory": true,
  "report_memory": false
}}
"""

    result = await ask_llm(
        prompt=prompt,
        temperature=0
    )

    import json

    try:
        return json.loads(result)
    except Exception:
        return {
            "profile": False,
            "medical": False,
            "appointments": False,
            "meals": False,
            "additional_info": False,
            "chat_memory": True,
            "report_memory": False
        }