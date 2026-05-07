# app/services/question_router.py
def detect_primary_intent(question: str) -> str:
    q = question.lower().strip()

    if any(x in q for x in [
        "allergy", "allergies", "blood type", "condition", "conditions",
        "medical", "chronic", "surgery", "emergency notes"
    ]):
        return "medical"

    if any(x in q for x in [
        "caregiver", "who looks after me", "my profile", "my details",
         "my phone", "my address", "my age", "my gender",
        "age", "gender", "date of birth", "myself", "my details"
    ]):
        return "profile"

    if any(x in q for x in [
        "appointment", "doctor visit", "hospital", "next appointments", "upcoming", "upcoming appointments", "doctor appointments",
        "appointments","my doctor appointments", "my appointments", "my upcoming doctor appointments"
    ]):
        return "appointments"

    if any(x in q for x in [
         "meal", "food", "eat", "eaten", "breakfast", "lunch", "dinner", "diet", "today meal", "meals", "my meals", "today meals",
         "today meal", "my today meals", "what did i eat today", "my food today", "today's food", "today's meals"
    ]):
        return "meals"

    if any(x in q for x in [
        "behavior", "caregiver note", "health goals", "preferences",
        "recent notes", "observation", "observations", "note", "notes"
    ]):
        return "additional_info"

    return "general_chat"
