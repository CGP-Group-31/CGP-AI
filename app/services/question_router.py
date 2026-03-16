def detect_primary_intent(question: str) -> str:
    q = question.lower()

    if any(x in q for x in [
        "allergy", "allergies", "blood type", "condition", "conditions",
        "medical", "chronic", "surgery", "emergency notes"
    ]):
        return "medical"

    if any(x in q for x in [
        "caregiver", "who looks after me", "my profile", "my details",
        "my name", "my phone", "my address"
    ]):
        return "profile"

    if any(x in q for x in [
        "appointment", "doctor visit", "hospital", "next appointment"
    ]):
        return "appointments"

    if any(x in q for x in [
        "meal", "food", "eat", "eaten", "breakfast", "lunch", "dinner", "diet"
    ]):
        return "meals"

    if any(x in q for x in [
        "behavior", "caregiver note", "health goals", "preferences",
        "recent notes", "observation"
    ]):
        return "additional_info"

    return "general_chat"