import pytesseract
from PIL import Image
import re
import os
import subprocess
import tempfile

# ==================================================
# REGEX
# ==================================================
MAIN_Q = re.compile(r"^\s*(\d{1,3})\s*[\.\)]\s*(.+)")
SUB_Q_PAREN = re.compile(r"^\s*\(([a-z])\)\s*(.+)")
SUB_Q_DOT = re.compile(r"^\s*([a-z])\)\s*(.+)")
DOTS = re.compile(r"\.{4,}")
BLANKS = re.compile(r"_{3,}|\.{5,}")

# Option-only lines (Male, SC, etc.)
OPTION_ONLY = re.compile(
    r"^(male|female|m|f|tg|transgender|sc|st|mbc|bc|oc|"
    r"hindu|christian|muslim)$",
    re.IGNORECASE
)

# Option list line (SC / ST / MBC / BC / OC)
OPTION_SLASH_LINE = re.compile(
    r"^(sc|st|mbc|bc|oc)(\s*/\s*(sc|st|mbc|bc|oc))+$",
    re.IGNORECASE
)

# ==================================================
# KEYWORDS
# ==================================================
LABOUR_KEYWORDS = [
    "name of the worker",
    "sex",
    "religion",
    "caste",
    "category",
    "father",
    "husband",
    "date of birth",
    "marital status",
    "permanent address",
    "present address",
    "nature of work",
    "number of years",
]

VEHICLE_KEYWORDS = [
    "registered number",
    "date of issue",
    "date of expiry",
    "registering authority",
    "class of vehicle",
    "motor vehicle was registered",
    "type of body",
]

CERTIFICATE_KEYWORDS = [
    "bonafide",
    "certified that",
    "academic year",
    "department",
    "examined",
    "viva",
]

IGNORE_PHRASES = [
    "hereby",
    "declare",
    "attached",
    "signature",
    "office use",
    "to be filled by",
    "see rule",
]

# ==================================================
# HELPERS
# ==================================================
def is_noise(text: str) -> bool:
    return bool(re.search(r"(.)\1{5,}", text))


def should_ignore(text: str) -> bool:
    t = text.lower().strip()

    if len(t) < 3:
        return True

    if DOTS.fullmatch(t):
        return True

    if is_noise(t):
        return True

    if OPTION_ONLY.fullmatch(t):
        return True

    if OPTION_SLASH_LINE.fullmatch(t):
        return True

    return any(p in t for p in IGNORE_PHRASES)


def detect_form_type(lines):
    joined = " ".join(lines).lower()

    if any(k in joined for k in LABOUR_KEYWORDS):
        return "labour"

    if any(k in joined for k in VEHICLE_KEYWORDS):
        return "vehicle"

    if any(k in joined for k in CERTIFICATE_KEYWORDS):
        return "certificate"

    return "unknown"

# ==================================================
# CERTIFICATE BLANK → QUESTIONS
# ==================================================
def extract_blanks_as_questions(lines):
    questions = []
    idx = 1

    for line in lines:
        blanks = list(BLANKS.finditer(line))
        if not blanks:
            continue

        for blank in blanks:
            before = line[:blank.start()].strip().rstrip(":,-")
            label = before.lower()

            if "bonafide work of" in label or "work of" in label:
                q = "Enter student name"
            elif "guide" in label:
                q = "Enter guide name"
            elif "academic year" in label:
                q = "Enter academic year"
            elif "viva" in label or "examination held" in label:
                q = "Enter viva examination date"
            elif "department" in label:
                q = "Enter department"
            elif "place" in label:
                q = "Enter place"
            else:
                q = f"Enter {before}"

            questions.append({
                "id": str(idx),
                "question": q
            })
            idx += 1

    return questions


# ==================================================
# IMAGE → QUESTIONS
# ==================================================
def extract_questions_from_image(image_path: str):

    text = pytesseract.image_to_string(
        Image.open(image_path),
        lang="eng",
        config="--psm 6"
    )

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    questions = []
    current_main = None

    MAIN_Q = re.compile(r"^\s*(\d{1,2})[\.\)]\s*(.+)")
    SUB_Q = re.compile(r"^\s*\(([a-z])\)\s*(.+)")

    IGNORE_EXTRA = [
        "xerox",
        "copy",
        "enclose",
        "attested",
        "group",
        "officer"
    ]

    for line in lines:

        lower = line.lower()

        # ❌ Ignore noisy lines
        if any(word in lower for word in IGNORE_EXTRA):
            continue

        # MAIN QUESTION
        m = MAIN_Q.match(line)
        if m:
            qid, qtext = m.groups()

            questions.append({
                "id": qid,
                "question": qtext.strip()
            })

            current_main = qid
            continue

        # SUB QUESTION
        s = SUB_Q.match(line)
        if s and current_main:
            sid, qtext = s.groups()

            questions.append({
                "id": f"{current_main}{sid}",
                "question": qtext.strip()
            })
            continue

    return questions
# ==================================================
# PDF → QUESTIONS
# ==================================================
def extract_questions_from_pdf(pdf_path: str):
    temp_dir = tempfile.mkdtemp()
    prefix = os.path.join(temp_dir, "page")

    subprocess.run(
        ["pdftoppm", "-png", "-r", "300", pdf_path, prefix],
        check=True
    )

    all_q = []

    for f in sorted(os.listdir(temp_dir)):
        if f.endswith(".png"):
            all_q.extend(
                extract_questions_from_image(os.path.join(temp_dir, f))
            )

    return all_q


def extract_questions(file_path: str):
    if file_path.lower().endswith(".pdf"):
        return extract_questions_from_pdf(file_path)

    return extract_questions_from_image(file_path)