from fastapi import APIRouter
import os
import re

from app.config import UPLOAD_DIR
from app.services.form_parser import extract_questions
from app.services.validator import validate_answer
from app.services.language import translate  # <-- important

router = APIRouter(prefix="/chat")

sessions = {}

SUPPORTED_LANGS = {
    "english": "en",
    "tamil": "ta",
    "hindi": "hi"
}

MAX_RETRIES = 3


# ----------------------------------------------------------
# SAFE TRANSLATION WRAPPER
# ----------------------------------------------------------
def safe_translate(text, source, target):
    try:
        return translate(text, source, target)
    except Exception as e:
        print("TRANSLATION ERROR:", e)
        return text  # fallback


# ----------------------------------------------------------
# Detect logical field type
# ----------------------------------------------------------
def detect_field_type(question: str):
    q = question.lower()

    if (
        "sex" in q
        or "gender" in q
        or "செக்ஸ்" in question
        or re.search(r"ஆண்\s*/\s*பெண்", question)
    ):
        return "gender"

    if "religion" in q or "மதம்" in question:
        return "religion"

    if (
        "caste" in q
        or "category" in q
        or "சாதி" in question
        or re.search(r"sc\s*/\s*st", q)
    ):
        return "caste"

    if "name" in q or "பெயர்" in question:
        return "name"

    if "address" in q or "முகவரி" in question:
        return "address"

    return None


# ==========================================================
# START CHAT
# ==========================================================
@router.post("/start")
def start_chat(session_id: str, filename: str):

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return {"question": "Uploaded file not found ❌"}

    questions = extract_questions(file_path)

    if not questions:
        return {"question": "No valid questions detected ❌"}

    # 🔥 CLEAN duplicate instruction lines
    cleaned_questions = []
    for q in questions:
        text = q["question"]

        if "ஆண்" in text and "பெண்" in text and "செக்ஸ்" not in text:
            continue

        if "SC" in text and "ST" in text and "சாதி" not in text:
            continue

        cleaned_questions.append(q)

    sessions[session_id] = {
        "questions": cleaned_questions,
        "answers": {},
        "index": 0,
        "retry_count": 0,
        "asked_fields": set(),
        "language": None,
        "filename": filename   # ✅ THIS IS THE FIX

    }

    return {
        "question": "Which language do you prefer? (English / Tamil / Hindi)"
    }


# ==========================================================
# ANSWER FLOW
# ==========================================================
@router.post("/answer")
def answer(session_id: str, text: str):

    session = sessions.get(session_id)

    if not session:
        return {"completed": True}

    # ---------------- LANGUAGE SELECTION ----------------
    if session["language"] is None:

        lang = text.strip().lower()

        if lang not in SUPPORTED_LANGS:
            return {"question": "Please choose: English / Tamil / Hindi"}

        session["language"] = SUPPORTED_LANGS[lang]

        first_question = session["questions"][0]["question"]

        if session["language"] == "en":
            return {"question": first_question}

        translated = safe_translate(first_question, "en", session["language"])
        return {"question": translated}

    questions = session["questions"]

    # Skip duplicate logical fields
    while session["index"] < len(questions):

        current_question = questions[session["index"]]["question"]
        field_type = detect_field_type(current_question)

        if field_type and field_type in session["asked_fields"]:
            session["index"] += 1
            continue

        break

    if session["index"] >= len(questions):
        return {
            "completed": True,
            "answers": session["answers"]
        }

    current_q_obj = questions[session["index"]]
    current_question = current_q_obj["question"]
    current_q_id = current_q_obj.get("id", str(session["index"]))

    # ---------------- TRANSLATE ANSWER SAFELY ----------------
    if session["language"] == "en":
        answer_en = text
    else:
        answer_en = safe_translate(text, session["language"], "en")

    is_valid, result = validate_answer(current_question, answer_en)

    if not is_valid:

        session["retry_count"] += 1

        if session["retry_count"] >= MAX_RETRIES:
            session["retry_count"] = 0
            session["answers"][current_q_id] = answer_en
            session["index"] += 1
        else:
            error_msg = result
            if session["language"] != "en":
                error_msg = safe_translate(result, "en", session["language"])
            return {"question": error_msg}

    else:

        session["retry_count"] = 0
        session["answers"][current_q_id] = result

        field_type = detect_field_type(current_question)
        if field_type:
            session["asked_fields"].add(field_type)

        session["index"] += 1

    # Skip duplicates again
    while session["index"] < len(questions):

        next_question = questions[session["index"]]["question"]
        field_type = detect_field_type(next_question)

        if field_type and field_type in session["asked_fields"]:
            session["index"] += 1
            continue

        break

    if session["index"] >= len(questions):
        return {
            "completed": True,
            "answers": session["answers"]
        }

    next_question = questions[session["index"]]["question"]

    if session["language"] == "en":
        return {"question": next_question}

    translated = safe_translate(next_question, "en", session["language"])
    return {"question": translated}