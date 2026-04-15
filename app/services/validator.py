import re
from datetime import datetime


def validate_answer(question: str, answer: str):

    q = question.lower().strip()
    a = answer.strip()

    if not a:
        return False, "Field cannot be empty"

    # -------------------------------------------------
    # NAME
    # -------------------------------------------------
    if any(word in q for word in ["name", "பெயர்"]):
        if not re.fullmatch(r"[A-Za-z ]{2,50}", a):
            return False, "Name must contain only letters"
        return True, a.title()

    # -------------------------------------------------
    # DATE (Flexible format)
    # -------------------------------------------------
    if any(word in q for word in ["date", "held on", "தேதி", "பிறந்த தேதி"]):

        a = a.replace("-", "/")  # allow 23-09-2005

        try:
            parsed = datetime.strptime(a, "%d/%m/%Y")
            return True, parsed.strftime("%d/%m/%Y")
        except ValueError:
            return False, "Enter date in DD/MM/YYYY format"

    # -------------------------------------------------
    # AGE
    # -------------------------------------------------
    if any(word in q for word in ["age", "வயது"]):
        if not a.isdigit() or not (1 <= int(a) <= 120):
            return False, "Enter valid age (1-120)"
        return True, a

    # -------------------------------------------------
    # MOBILE
    # -------------------------------------------------
    if any(word in q for word in ["mobile", "phone", "மொபைல்"]):
        if not re.fullmatch(r"\d{10}", a):
            return False, "Enter valid 10-digit mobile number"
        return True, a

    # -------------------------------------------------
    # EMAIL
    # -------------------------------------------------
    if "email" in q:
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", a):
            return False, "Enter valid email address"
        return True, a.lower()

    # -------------------------------------------------
    # YEAR
    # -------------------------------------------------
    if "year" in q:
        if not re.fullmatch(r"\d{4}", a):
            return False, "Enter 4-digit year"
        return True, a

    # -------------------------------------------------
    # GENDER (Simplified)
    # -------------------------------------------------
    if any(word in q for word in ["sex", "gender", "செக்ஸ்", "பாலினம்"]):

        value = a.lower().strip()

        if value in ["male", "m", "ஆண்", "aan"]:
            return True, "Male"

        if value in ["female", "f", "பெண்", "pen"]:
            return True, "Female"

        if value in ["tg", "transgender", "third gender", "திருநங்கை"]:
            return True, "TG"

        return True, a.title()

    # -------------------------------------------------
    # CASTE / CATEGORY (Simplified)
    # -------------------------------------------------
    if any(word in q for word in ["category", "caste", "சாதி", "community"]):

        value = a.strip().upper()

        if value in ["SC", "ST", "MBC", "BC", "OC"]:
            return True, value

        return True, value

    # -------------------------------------------------
    # ADDRESS
    # -------------------------------------------------
    if any(word in q for word in ["address", "முகவரி"]):
        if len(a) < 5:
            return False, "Enter valid address"
        return True, a

    # -------------------------------------------------
    # DEFAULT
    # -------------------------------------------------
    return True, a