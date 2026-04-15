from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
import traceback

from app.routes.chat import sessions
from app.config import UPLOAD_DIR
from app.utils.pdf_filler import auto_fill_any_form
from app.services.pdf_to_image import pdf_to_image

router = APIRouter()

OUTPUT_DIR = os.path.join(UPLOAD_DIR, "filled")
IMAGE_DIR = os.path.join(UPLOAD_DIR, "pdf_images")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)


@router.get("/generate-pdf")
def generate_pdf(session_id: str):

    try:
        session = sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        filename = session.get("filename")
        if not filename:
            return {"error": "Uploaded file not found in session"}

        file_path = os.path.join(UPLOAD_DIR, filename)

        print("SESSION:", session)
        print("FILE:", file_path)

        if filename.lower().endswith(".pdf"):
            images = pdf_to_image(file_path, IMAGE_DIR)

            print("IMAGES:", images)

            if not images:
                return {"error": "PDF to image conversion failed"}

            image_path = images[0]
        else:
            image_path = file_path

        output_pdf = os.path.join(
            OUTPUT_DIR,
            f"{session_id}_filled.pdf"
        )

        answers_dict = session.get("answers", {})

        print("ANSWERS:", answers_dict)

        auto_fill_any_form(image_path, output_pdf, answers_dict)

        print("OUTPUT EXISTS:", os.path.exists(output_pdf))

        if not os.path.exists(output_pdf):
            return {"error": "PDF not created"}

        return FileResponse(
            path=output_pdf,
            media_type="application/pdf",
            filename="filled_form.pdf",
            headers={
                "Content-Disposition": "attachment; filename=filled_form.pdf"
            }
        )

    except Exception as e:
        print("PDF GENERATION ERROR:")
        traceback.print_exc()
        return {"error": str(e)}