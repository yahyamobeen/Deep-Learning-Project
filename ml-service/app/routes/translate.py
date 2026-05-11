from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import numpy as np, base64, cv2, tempfile, os

from app.inference.sign_recognizer import SignRecognizer
from app.inference.text_to_gloss   import TextToGloss
from app.inference.gloss_to_text   import GlossToText
from app.inference.speech_to_text  import SpeechToText
from app.utils.landmarks           import read_frames

router = APIRouter()

recognizer = SignRecognizer()
text2gloss = TextToGloss()
gloss2text = GlossToText()
stt        = SpeechToText()


class TextIn(BaseModel):
    text: str


class GlossOut(BaseModel):
    gloss: list[str]
    clips: list[str]


def _clip_urls(gloss: list[str]) -> list[str]:
    return [f"/static/clips/{g.lower()}.mp4" for g in gloss]


@router.post("/text-to-sign", response_model=GlossOut)
def text_to_sign(payload: TextIn):
    gloss = text2gloss.translate(payload.text)
    return {"gloss": gloss, "clips": _clip_urls(gloss)}


@router.post("/sign-to-text")
async def sign_to_text(file: UploadFile = File(...)):
    """Video clip → ST-GCN/MoViNet → gloss → English sentence."""
    suffix = os.path.splitext(file.filename or "vid.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read()); path = tmp.name
    try:
        frames = read_frames(path, num_frames=32)
        gloss, conf, top5 = recognizer.predict(frames)
        sentence = gloss2text.translate([gloss])
        return {
            "gloss": gloss,
            "sentence": sentence,
            "confidence": conf,
            "top5": top5,
        }
    finally:
        try: os.unlink(path)
        except OSError: pass


@router.post("/speech-to-sign")
async def speech_to_sign(file: UploadFile = File(...)):
    """Audio → Whisper transcript → text→gloss → clip URLs."""
    suffix = os.path.splitext(file.filename or "audio.webm")[1] or ".webm"
    audio  = await file.read()
    text   = stt.transcribe(audio, suffix=suffix)
    gloss  = text2gloss.translate(text)
    return {"transcript": text, "gloss": gloss, "clips": _clip_urls(gloss)}


@router.websocket("/ws")
async def stream_translate(ws: WebSocket):
    """Real-time webcam stream → predicted gloss + sentence every 32 frames."""
    await ws.accept()
    buf: list[np.ndarray] = []
    try:
        while True:
            msg = await ws.receive_text()
            jpg = base64.b64decode(msg.split(",")[-1])
            arr = np.frombuffer(jpg, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None: continue
            buf.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if len(buf) >= 32:
                gloss, conf, _ = recognizer.predict(np.stack(buf[-32:]))
                sentence = gloss2text.translate([gloss])
                await ws.send_json({"gloss": gloss, "sentence": sentence, "confidence": conf})
                buf = buf[-16:]   # 50% overlap
    except WebSocketDisconnect:
        pass
