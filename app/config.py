import os

# Points to: .../ai_form_assistant/backend
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

# Points to: .../ai_form_assistant/backend/uploaded_forms
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_forms")

print("CONFIG UPLOAD_DIR =", UPLOAD_DIR)

os.makedirs(UPLOAD_DIR, exist_ok=True)
