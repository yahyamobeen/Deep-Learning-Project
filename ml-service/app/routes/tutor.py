from fastapi import APIRouter, UploadFile, File, Form
import os, tempfile, json
from app.inference.tutor_scorer import TutorScorer
from app.utils.landmarks       import LandmarkExtractor

router = APIRouter()
scorer    = TutorScorer()
extractor = LandmarkExtractor()

REF_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "reference_signs.json")


@router.get("/lessons")
def lessons():
    """List of available lessons (gloss, demo video URL, difficulty)."""
    return [
        {"id": "hello",     "label": "HELLO",     "video": "/static/clips/hello.mp4",     "level": 1},
        {"id": "thank-you", "label": "THANK-YOU", "video": "/static/clips/thank-you.mp4", "level": 1},
        {"id": "yes",       "label": "YES",       "video": "/static/clips/yes.mp4",       "level": 1},
        {"id": "no",        "label": "NO",        "video": "/static/clips/no.mp4",        "level": 1},
        {"id": "please",    "label": "PLEASE",    "video": "/static/clips/please.mp4",    "level": 2},
    ]


@router.post("/score")
async def score_attempt(lesson_id: str = Form(...), file: UploadFile = File(...)):
    """Compares the user's recorded attempt against the reference for the lesson."""
    suffix = os.path.splitext(file.filename or "vid.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read()); path = tmp.name
    try:
        user_seq = extractor.from_video(path, num_frames=32)
        score, hint = scorer.compare(lesson_id, user_seq)
        return {"score": round(score, 1), "hint": hint, "passed": score >= 70}
    finally:
        os.unlink(path)
