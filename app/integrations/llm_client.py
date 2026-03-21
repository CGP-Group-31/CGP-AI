import re
import httpx
from app.core.config import settings
import json
from pydantic import ValidationError
from app.daily_reports.schema import DailyElderReport
from app.weekly_report.schema import WeeklyElderReport

CHAT_TEMPERATURE = 0.5
CHAT_MAX_TOKENS = 350

CHECKIN_TEMPERATURE = 0.4
CHECKIN_MAX_TOKENS = 450

DAILY_REPORT_TEMPERATURE = 0.2
DAILY_REPORT_MAX_TOKENS = 1200

WEEKLY_REPORT_TEMPERATURE = 0.2
WEEKLY_REPORT_MAX_TOKENS = 1500

async def _post_llm(messages: list, temperature: float, max_tokens: int) -> str:
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            settings.LLM_BASE_URL,
            headers=headers,
            json=body
        )

    response.raise_for_status()
    data = response.json()

    choices = data.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content")

    if content is None:
        return ""

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text_val = item.get("text")
                if text_val:
                    parts.append(text_val)
        return " ".join(parts).strip()

    return str(content).strip()


async def ask_llm(
    prompt: str,
    temperature: float = CHAT_TEMPERATURE,
    max_tokens: int = CHAT_MAX_TOKENS
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful elderly-care AI companion of TrustCare."
                "Be supportive, calm, clear and safe."
                "Do not give dangerous or definitive medical advice."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    text = await _post_llm(messages, temperature, max_tokens)
    return text or "I'm here with you. Could you tell me a little more?"


async def detect_mood(text: str) -> str:
    if not text:
        return "Neutral"

    t = text.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)

    happy_words = [
        "happy", "great", "better", "glad", "calm",
        "peaceful", "nice", "well", "enjoyed"
    ]
    sad_words = [
        "sad", "lonely", "down", "depressed", "cry",
        "upset", "hopeless", "empty", "unhappy", "hurt"
    ]
    anxious_words = [
        "anxious", "worried", "nervous", "panic", "fear",
        "afraid", "uneasy", "stressed", "tense"
    ]
    angry_words = [
        "angry", "mad", "annoyed", "frustrated",
        "irritated", "hate", "furious"
    ]
    confused_words = [
        "confused", "unsure", "don't know",
        "cannot understand", "forgot", "forget",
        "lost", "mixed up"
    ]
    tired_words = [
        "tired", "weak", "sleepy", "exhausted",
        "fatigued", "no energy", "low energy", "drained"
    ]

    def contains_any(words: list[str]) -> bool:
        return any(w in t for w in words)

    if contains_any(sad_words):
        return "Sad"
    if contains_any(anxious_words):
        return "Anxious"
    if contains_any(angry_words):
        return "Angry"
    if contains_any(confused_words):
        return "Confused"
    if contains_any(tired_words):
        return "Tired"
    if contains_any(happy_words):
        return "Happy"

    return "Neutral"



def _extract_json_object(text: str) -> dict:
    """
    Extract the first valid JSON object from LLM output.
    """

    if not text:
        raise ValueError("LLM returned empty response")

    text = text.strip()

    # remove markdown fences
    text = re.sub(r"^```json", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in LLM output: {text}")

    json_str = text[start:end + 1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned by LLM: {e}\n{text}")
    


    

async def ask_llm_for_daily_report(prompt: str) -> DailyElderReport:
    messages = [
        {
            "role": "system",
            "content": (
                "You generate structured elder reports. "
                "Return valid JSON only. "
                "No markdown. "
                "No code fences. "
                "Do not include explanations outside the JSON object."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    raw_text = await _post_llm(
        messages=messages,
        temperature=DAILY_REPORT_TEMPERATURE,
        max_tokens=DAILY_REPORT_MAX_TOKENS,
    )

    data = _extract_json_object(raw_text)

    try:
        return DailyElderReport.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Daily report schema validation failed: {e}") from e
    



async def ask_llm_for_weekly_report(prompt: str) -> WeeklyElderReport:

    messages = [
        {
            "role": "system",
            "content": (
                "You generate structured weekly elder care reports. "
                "Return valid JSON only. "
                "No markdown. "
                "No code fences. "
                "Do not include explanations outside the JSON object."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    raw_text = await _post_llm(
        messages=messages,
        temperature=WEEKLY_REPORT_TEMPERATURE,
        max_tokens=WEEKLY_REPORT_MAX_TOKENS,
    )

    data = _extract_json_object(raw_text)

    try:
        return WeeklyElderReport.model_validate(data)

    except ValidationError as e:
        raise ValueError(
            f"Weekly report schema validation failed: {e}"
        ) from e