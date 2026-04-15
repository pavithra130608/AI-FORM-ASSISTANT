import cv2
import numpy as np
import pytesseract
from pytesseract import Output
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import blue, black


# ==================================================
# CHECKBOX DETECTION
# ==================================================
def detect_checkboxes(gray):
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        15, 2
    )

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 12 < w < 30 and 12 < h < 30:
            boxes.append((x, y, w, h))

    return boxes


def match_checkbox(label, answer):
    l = label.lower().strip()
    a = answer.lower().strip()

    mapping = {
        "m": ["male", "m"],
        "f": ["female", "f"],
        "tg": ["tg", "transgender"],
        "sc": ["sc"],
        "st": ["st"],
        "mbc": ["mbc"],
        "bc": ["bc"],
        "oc": ["oc"]
    }

    return l in mapping and a in mapping[l]


def tick_checkbox(c, box, img_w, img_h, page_w, page_h):
    x, y, w, h = box
    px = (x + w / 2) / img_w * page_w
    py = page_h - ((y + h / 2) / img_h * page_h)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(px - 4, py - 4, "✔")


# ==================================================
# MAIN PDF FILLER
def auto_fill_any_form(image_path, output_pdf, answers_dict, family_members=None):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Image not loaded")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pil = Image.open(image_path)

    ocr = pytesseract.image_to_data(
        pil,
        output_type=Output.DICT,
        config="--psm 6"
    )

    c = canvas.Canvas(output_pdf, pagesize=A4)
    page_w, page_h = A4
    img_h, img_w = img.shape[:2]

    # Background
    c.drawImage(image_path, 0, 0, width=page_w, height=page_h)

    # ==================================================
    # STEP 1: NORMALIZE QUESTION TEXT
    # ==================================================
    def normalize(text):
        return (
            text.lower()
            .replace("(a)", "")
            .replace("(b)", "")
            .replace("(c)", "")
            .replace("(d)", "")
            .replace("(e)", "")
            .replace(":", "")
            .strip()
        )

    # ==================================================
    # STEP 2: BUILD ANCHORS (question → colon index)
    # ==================================================
    anchors = {}

    for i, word in enumerate(ocr["text"]):
        if word.strip() != ":":
            continue

        words = []
        for j in range(i - 1, max(i - 25, -1), -1):
            t = ocr["text"][j].strip()
            if not t or t == ":":
                continue
            words.insert(0, t)

        label = normalize(" ".join(words))

        for q in answers_dict.keys():
            qn = normalize(q)
            if qn and qn in label and q not in anchors:
                anchors[q] = i

    # ==================================================
    # STEP 3: FILL TEXT FIELDS
    # ==================================================
    for q, answer in answers_dict.items():
        if q not in anchors:
            continue

        i = anchors[q]

        x = ocr["left"][i]
        y = ocr["top"][i]
        w = ocr["width"][i]

        pdf_x = (x + w + 12) / img_w * page_w
        pdf_y = page_h - (y / img_h * page_h)

        c.setFont("Helvetica", 10)
        c.setFillColor(blue)
        c.drawString(pdf_x, pdf_y, answer)
        c.setFillColor(black)

    # ==================================================
    # STEP 4: CHECKBOX TICKING (FIXED)
    # ==================================================
    checkboxes = detect_checkboxes(gray)

    for q, answer in answers_dict.items():
        if q not in anchors:
            continue

        i = anchors[q]
        y_ref = ocr["top"][i]

        for idx, label in enumerate(ocr["text"]):
            label = label.strip()
            if not label:
                continue

            if abs(ocr["top"][idx] - y_ref) < 18:
                if match_checkbox(label, answer):
                    for box in checkboxes:
                        bx, by, bw, bh = box
                        if abs(by - ocr["top"][idx]) < 12:
                            tick_checkbox(c, box, img_w, img_h, page_w, page_h)

    c.save()
