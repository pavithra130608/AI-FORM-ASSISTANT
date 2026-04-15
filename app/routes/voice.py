from fastapi import APIRouter, UploadFile, File
import speech_recognition as sr

router = APIRouter(prefix="/voice")

@router.post("/")
async def voice_to_text(file: UploadFile = File(...)):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file.file) as source:
        audio = recognizer.record(source)
    text = recognizer.recognize_google(audio)
    return {"text": text}
