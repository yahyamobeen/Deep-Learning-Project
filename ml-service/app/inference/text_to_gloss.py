"""English text → ASL gloss.

Selection order (whichever is available wins):
  1. ONNX-int8 flan-T5 from `models/t5_text2gloss/onnx_int8/`  (fastest, smallest)
  2. PyTorch flan-T5 from `models/t5_text2gloss/`              (notebook 05 output)
  3. Rule-based fallback                                       (zero-training, ships day 1)

All three return `list[str]` with uppercase gloss tokens, so the route layer
never has to care which backend is active.
"""
import os
import re

MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "models", "t5_text2gloss")
ONNX_DIR   = os.path.join(MODEL_DIR, "onnx_int8")
PROMPT     = "translate English to ASL gloss: "
FORCE_DUMMY = os.getenv("FORCE_DUMMY_MODELS", "").lower() in {"1", "true", "yes"}

# --- rule-based fallback -----------------------------------------------------
_STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were",
    "do", "does", "did", "of", "to", "and", "but", "or",
    "be", "been", "being", "have", "has", "had",
}
_CONTRACTIONS = {
    "i'm": "i am", "i've": "i have", "i'll": "i will", "i'd": "i would",
    "you're": "you are", "you've": "you have", "you'll": "you will",
    "he's": "he is", "she's": "she is", "it's": "it is",
    "we're": "we are", "we've": "we have", "they're": "they are",
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "can not", "cannot": "can not", "won't": "will not",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not",
    "what's": "what is", "where's": "where is", "who's": "who is",
}
_WH_WORDS = {"what", "where", "who", "when", "why", "how"}


def _rule_based(text: str) -> list[str]:
    """Cheap English → ASL-gloss heuristic.

    Steps:
      1. lowercase + expand contractions
      2. drop stopwords
      3. uppercase remaining tokens
      4. if a wh-word is present, move it to the end (ASL topic-comment order)
    """
    text = text.lower().strip()
    for k, v in _CONTRACTIONS.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)
    tokens = re.findall(r"[a-z][a-z'-]*", text)
    tokens = [t for t in tokens if t not in _STOPWORDS]
    if not tokens:
        return []
    wh = [t for t in tokens if t in _WH_WORDS]
    rest = [t for t in tokens if t not in _WH_WORDS]
    ordered = rest + wh
    return [t.upper() for t in ordered]


class TextToGloss:
    def __init__(self):
        self.backend = "rule"
        self.model = None
        self.tok = None
        if not FORCE_DUMMY:
            self._try_load_onnx() or self._try_load_pytorch()
        print(f"[TextToGloss] backend = {self.backend}")

    def _try_load_onnx(self) -> bool:
        if not os.path.isdir(ONNX_DIR):
            return False
        try:
            from optimum.onnxruntime import ORTModelForSeq2SeqLM
            from transformers import AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(ONNX_DIR)
            self.model = ORTModelForSeq2SeqLM.from_pretrained(ONNX_DIR)
            self.backend = "onnx"
            return True
        except Exception as e:
            print(f"[TextToGloss] ONNX load failed ({e}); trying PyTorch.")
            return False

    def _try_load_pytorch(self) -> bool:
        if not os.path.isdir(MODEL_DIR) or not os.path.exists(os.path.join(MODEL_DIR, "config.json")):
            return False
        try:
            from transformers import AutoTokenizer, T5ForConditionalGeneration
            self.tok = AutoTokenizer.from_pretrained(MODEL_DIR)
            self.model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR).eval()
            self.backend = "pytorch"
            return True
        except Exception as e:
            print(f"[TextToGloss] PyTorch load failed ({e}); using rule-based fallback.")
            return False

    def translate(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        if self.backend == "rule" or self.model is None:
            return _rule_based(text)
        ids = self.tok(PROMPT + text, return_tensors="pt").input_ids
        out = self.model.generate(ids, max_length=32, num_beams=4)
        decoded = self.tok.decode(out[0], skip_special_tokens=True)
        toks = [t.upper() for t in decoded.split() if t.strip()]
        return toks or _rule_based(text)
