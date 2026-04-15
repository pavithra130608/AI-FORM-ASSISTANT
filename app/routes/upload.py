from fastapi import APIRouter, UploadFile, File
import os
from app.config import UPLOAD_DIR

router = APIRouter()

@router.post("/chat/upload/")
async def upload_form(file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    print("UPLOAD SAVED:", file_path)

    return {
        "filename": file.filename,
        "type": file.content_type
    }
