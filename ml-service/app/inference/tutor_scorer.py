"""Tutor scoring: DTW over MediaPipe landmarks + (optional) ST-GCN-encoder
embedding cosine similarity.

If the ST-GCN encoder is present, the final score is a 60/40 blend; otherwise
we fall back to pure DTW (the original behaviour).
"""
import os
import json
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import cosine

MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "models")
REF_PATH   = os.path.join(MODEL_DIR, "reference_signs.json")
ENCODER    = os.path.join(MODEL_DIR, "sthgcn_wlasl300", "encoder.onnx")


def _hint(score: float) -> str:
    if score >= 85: return "Excellent — very close to the reference."
    if score >= 70: return "Good. Try to keep your hand orientation steadier."
    if score >= 50: return "Almost — slow the motion down and watch the start position."
    return "Re-watch the demo. Focus on hand shape and movement direction."


class TutorScorer:
    def __init__(self):
        self.refs: dict[str, np.ndarray] = {}
        self.ref_embs: dict[str, np.ndarray] = {}
        self.encoder = None

        if os.path.exists(REF_PATH):
            blob = json.load(open(REF_PATH))
            for k, v in blob.items():
                if isinstance(v, dict):
                    self.refs[k] = np.array(v["landmarks"], dtype=np.float32)
                    if "embedding" in v:
                        self.ref_embs[k] = np.array(v["embedding"], dtype=np.float32)
                else:
                    self.refs[k] = np.array(v, dtype=np.float32)
        else:
            print(f"[TutorScorer] no reference signs at {REF_PATH} — scoring will return 0.")

        if os.path.exists(ENCODER):
            try:
                import onnxruntime as ort
                self.encoder = ort.InferenceSession(ENCODER, providers=["CPUExecutionProvider"])
                print("[TutorScorer] loaded ST-GCN encoder for embedding-channel scoring.")
            except Exception as e:
                print(f"[TutorScorer] encoder load failed ({e}); using DTW only.")

    def _embed(self, seq: np.ndarray) -> np.ndarray | None:
        if self.encoder is None:
            return None
        x = seq.astype(np.float32)[None, ...]   # (1, T, 1629)
        try:
            (emb,) = self.encoder.run(None, {self.encoder.get_inputs()[0].name: x})
            return emb.squeeze()
        except Exception as e:
            print(f"[TutorScorer] encoder run failed: {e}")
            return None

    def compare(self, lesson_id: str, user_seq: np.ndarray):
        ref = self.refs.get(lesson_id)
        if ref is None:
            return 0.0, "Reference for this lesson is not available yet."

        # DTW channel
        dist, _ = fastdtw(ref, user_seq, dist=lambda a, b: cosine(a, b) if a.any() and b.any() else 1.0)
        norm = dist / max(len(ref), 1)
        dtw_score = max(0.0, 100.0 * (1.0 - min(norm, 1.0)))

        # Embedding channel (optional)
        ref_emb = self.ref_embs.get(lesson_id)
        if ref_emb is None and self.encoder is not None:
            ref_emb = self._embed(ref)
            if ref_emb is not None:
                self.ref_embs[lesson_id] = ref_emb
        user_emb = self._embed(user_seq) if self.encoder is not None else None

        if ref_emb is not None and user_emb is not None:
            cos = 1.0 - cosine(ref_emb, user_emb)        # in [-1, 1]
            emb_score = max(0.0, min(100.0, 50.0 * (cos + 1.0)))
            score = 0.6 * dtw_score + 0.4 * emb_score
        else:
            score = dtw_score

        return score, _hint(score)
