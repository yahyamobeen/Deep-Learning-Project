"""ASL gloss → English sentence.

Selection order:
  1. ONNX-int8 flan-T5 reverse-direction model (`models/gloss2text/onnx_int8/`)
  2. PyTorch flan-T5 reverse model              (`models/gloss2text/`)
  3. Rule-based fallback                        (lowercase + insert "I am / the" heuristics)

Returns a single English sentence (str).
"""
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models", "gloss2text")
ONNX_DIR  = os.path.join(MODEL_DIR, "onnx_int8")
PROMPT    = "translate ASL gloss to English: "
FORCE_DUMMY = os.getenv("FORCE_DUMMY_MODELS", "").lower() in {"1", "true", "yes"}

_AUX_AFTER = {  # subject pronoun → auxiliary to insert after
    "i": "am", "you": "are", "he": "is", "she": "is", "it": "is",
    "we": "are", "they": "are",
}


def _rule_based(gloss_tokens: list[str]) -> str:
    """Cheap gloss → English heuristic.

    Steps:
      1. lowercase
      2. if first token is a subject pronoun and second isn't a verb-like
         auxiliary, insert the matching aux after it
      3. add a period
    """
    if not gloss_tokens:
        return ""
    toks = [t.lower() for t in gloss_tokens if t.strip()]
    if len(toks) >= 2 and toks[0] in _AUX_AFTER:
        aux = _AUX_AFTER[toks[0]]
        if toks[1] != aux and toks[1] not in {"am", "is", "are", "have", "has", "will", "can"}:
            toks = [toks[0], aux] + toks[1:]
    sentence = " ".join(toks)
    return sentence[0].upper() + sentence[1:] + "."


class GlossToText:
    def __init__(self):
        self.backend = "rule"
        self.model = None
        self.tok = None
        if not FORCE_DUMMY:
            self._try_load_onnx() or self._try_load_pytorch()
        print(f"[GlossToText] backend = {self.backend}")

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
            print(f"[GlossToText] ONNX load failed ({e}); trying PyTorch.")
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
            print(f"[GlossToText] PyTorch load failed ({e}); using rule-based fallback.")
            return False

    def translate(self, gloss_tokens: list[str]) -> str:
        if not gloss_tokens:
            return ""
        if self.backend == "rule" or self.model is None:
            return _rule_based(gloss_tokens)
        gloss_str = " ".join(t.upper() for t in gloss_tokens)
        ids = self.tok(PROMPT + gloss_str, return_tensors="pt").input_ids
        out = self.model.generate(ids, max_length=64, num_beams=4)
        decoded = self.tok.decode(out[0], skip_special_tokens=True).strip()
        return decoded or _rule_based(gloss_tokens)
