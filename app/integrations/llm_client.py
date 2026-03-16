import re
import httpx
from app.core.config import settings
import json
from pydantic import ValidationError
from app.daily_reports.schema import DailyElderReport

CHAT_TEMPERATURE = 0.5
CHAT_MAX_TOKENS = 250

CHECKIN_TEMPERATURE = 0.4
CHECKIN_MAX_TOKENS = 220


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
                "You are a helpful elderly-care AI assistant. "
                "Be supportive, calm, clear, and safe. "
                "Do not give dangerous or definitive medical advice. "
                "If something sounds serious, encourage contacting a caregiver or doctor."
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



async def ask_llm_for_daily_report(prompt: str) -> DailyElderReport:
    messages = [
        {
            "role": "system",
            "content": (
                "You generate structured elder reports. "
                "Return valid JSON only. No markdown. No code fences"
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    raw_text = await _post_llm(
        messages=messages,
        temperature=0.2,
        max_tokens=900
    )

    raw_text = raw_text.strip()

    if raw_text.startswith("'''"):
        raw_text=raw_text.strip("'")
        raw_text=raw_text.replace("json","", 1).strip()

    try:
        data=json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {raw_text}") from e
    
    try:
        return DailyElderReport.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Daily report schema validation failed: {e}") from e