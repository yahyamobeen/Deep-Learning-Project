"""Smoke tests covering the contract every inference module promises in DUMMY
mode (no checkpoints downloaded). These tests must keep passing so the UI and
mobile app can be developed against an empty `models/` directory.

We force DUMMY mode regardless of which heavy packages happen to be installed
locally, so the same test runs identically in CI and on a developer laptop.
"""
import os
import sys
import numpy as np

os.environ["FORCE_DUMMY_MODELS"] = "1"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.inference.text_to_gloss import TextToGloss, _rule_based as t2g_rule
from app.inference.gloss_to_text import GlossToText, _rule_based as g2t_rule
from app.inference.sign_recognizer import SignRecognizer
from app.inference.speech_to_text  import SpeechToText


def test_text_to_gloss_rule_based():
    out = t2g_rule("I am hungry")
    assert out == ["I", "HUNGRY"]
    out = t2g_rule("where is the bathroom")
    # "where" must move to the end (topic-comment / wh-final).
    assert out[-1] == "WHERE"
    assert "BATHROOM" in out


def test_text_to_gloss_handles_empty():
    assert TextToGloss().translate("") == []
    assert TextToGloss().translate("   ") == []


def test_gloss_to_text_rule_based():
    s = g2t_rule(["I", "HUNGRY"])
    assert s.lower().startswith("i am hungry"), s
    assert s.endswith(".")


def test_sign_recognizer_dummy_shape():
    r = SignRecognizer()
    frames = np.zeros((16, 224, 224, 3), dtype=np.uint8)
    g, conf, top5 = r.predict(frames)
    assert isinstance(g, str) and g
    assert 0.0 <= conf <= 1.0
    assert isinstance(top5, list) and len(top5) == 5


def test_speech_to_text_dummy_returns_string():
    s = SpeechToText().transcribe(b"\x00" * 1024, suffix=".webm")
    assert isinstance(s, str) and s
