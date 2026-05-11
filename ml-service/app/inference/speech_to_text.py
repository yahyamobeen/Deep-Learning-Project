"""English-only speech-to-text via Hugging Face Whisper.

Default model is `openai/whisper-base.en` — 74 M params, ~290 MB, runs at
roughly real-time on a free HF Spaces CPU. Override with WHISPER_MODEL.
Falls back to a DUMMY string so the UI flow still works without weights.
"""
import os
import tempfile

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "openai/whisper-base.en")
FORCE_DUMMY   = os.getenv("FORCE_DUMMY_MODELS", "").lower() in {"1", "true", "yes"}


class SpeechToText:
    def __init__(self):
        self.available = False
        self.pipe = None
        if FORCE_DUMMY:
            print("[SpeechToText] FORCE_DUMMY_MODELS set; DUMMY mode.")
            return
        try:
            from transformers import pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=WHISPER_MODEL,
                device=-1,                # CPU
                chunk_length_s=15,
                return_timestamps=False,
            )
            self.available = True
            print(f"[SpeechToText] loaded {WHISPER_MODEL}")
        except Exception as e:
            print(f"[SpeechToText] could not load {WHISPER_MODEL} ({e}); DUMMY mode.")

    def transcribe(self, audio_bytes: bytes, suffix: str = ".webm") -> str:
        if not self.available:
            return "hello how are you"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes); path = tmp.name
        try:
            out = self.pipe(path)
            return (out.get("text") if isinstance(out, dict) else "").strip()
        finally:
            try: os.unlink(path)
            except OSError: pass
