"""Sign-language video → gloss prediction.

Two-stage ensemble (per the project plan):
  1. Pose stream: MediaPipe Holistic → ST-GCN (OpenHands), tiny + fast on CPU.
  2. RGB fallback: MoViNet-A0 on raw frames, used only if the pose stream
     fails (low confidence OR no hand landmarks detected).

Selection by env var:
  SIGN_RECOGNIZER_MODE = "pose" | "rgb" | "ensemble"   (default "ensemble")

DUMMY mode (no weights present) preserves the original return-shape contract so
the UI tests pass during development.
"""
import os
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
POSE_DIR   = os.path.join(MODELS_DIR, "sthgcn_wlasl300")
RGB_DIR    = os.path.join(MODELS_DIR, "movinet_a0_wlasl300")

MODE = os.getenv("SIGN_RECOGNIZER_MODE", "ensemble").lower()
POSE_CONFIDENCE_THRESHOLD = float(os.getenv("POSE_CONFIDENCE_THRESHOLD", "0.6"))
FORCE_DUMMY = os.getenv("FORCE_DUMMY_MODELS", "").lower() in {"1", "true", "yes"}
NUM_FRAMES = 32   # pose stream default; RGB path resamples internally


class _DummyBackend:
    """Returns a stable tuple so UI flows work before any weights are downloaded."""
    available = False
    def predict(self, frames):
        return "HELLO", 0.42, ["HELLO", "HI", "HEY", "WAVE", "BYE"]


class _PoseBackend:
    """MediaPipe landmarks → ST-GCN classifier."""
    available = False
    def __init__(self):
        if not os.path.isdir(POSE_DIR):
            return
        try:
            import torch, json
            self.torch = torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            # OpenHands export: we expect a TorchScript file + label map.
            # If the notebook produced an ONNX export, load that instead.
            ts_path   = os.path.join(POSE_DIR, "model.ts")
            onnx_path = os.path.join(POSE_DIR, "model.onnx")
            label_path = os.path.join(POSE_DIR, "labels.json")
            if os.path.exists(ts_path):
                self.runtime = "torchscript"
                self.model = torch.jit.load(ts_path, map_location=self.device).eval()
            elif os.path.exists(onnx_path):
                import onnxruntime as ort
                self.runtime = "onnx"
                self.session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
            else:
                print(f"[SignRecognizer/pose] no model.ts or model.onnx in {POSE_DIR}")
                return
            self.id2label = {int(k): v for k, v in json.load(open(label_path)).items()} \
                if os.path.exists(label_path) else {}
            from app.utils.landmarks import LandmarkExtractor
            self.extractor = LandmarkExtractor(complexity=1)
            self.available = True
        except Exception as e:
            print(f"[SignRecognizer/pose] init failed: {e}")

    def predict(self, frames: np.ndarray):
        # frames: (T, H, W, 3) uint8 RGB → 32 × 543-D landmark vector
        T = frames.shape[0]
        idx = np.linspace(0, max(T - 1, 0), NUM_FRAMES).astype(int)
        seq = []
        hand_hits = 0
        for f in frames[idx]:
            import cv2
            bgr = cv2.cvtColor(f, cv2.COLOR_RGB2BGR)
            v = self.extractor.from_frame(bgr)
            seq.append(v)
            # heuristic: hand landmarks live at offsets [132:195] (left) + [195:258] (right)
            if v[132:258].any():
                hand_hits += 1
        x = np.stack(seq).astype(np.float32)[None, ...]   # (1, T, 1629)
        if self.runtime == "torchscript":
            with self.torch.no_grad():
                logits = self.model(self.torch.from_numpy(x).to(self.device))[0]
            probs = self.torch.softmax(logits, dim=-1).cpu().numpy()
        else:
            (logits,) = self.session.run(None, {self.session.get_inputs()[0].name: x})
            logits = logits[0]
            e = np.exp(logits - logits.max()); probs = e / e.sum()
        top5_idx = np.argsort(probs)[::-1][:5]
        top1, conf = int(top5_idx[0]), float(probs[top5_idx[0]])
        label = self.id2label.get(top1, str(top1))
        top5  = [self.id2label.get(int(i), str(int(i))) for i in top5_idx]
        return label, conf, top5, hand_hits


class _RgbBackend:
    """MoViNet-A0 on raw frames."""
    available = False
    def __init__(self):
        if not os.path.isdir(RGB_DIR):
            return
        try:
            # Lazy import — only loaded when this backend exists.
            import torch, json
            self.torch = torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            ts_path = os.path.join(RGB_DIR, "model.ts")
            if not os.path.exists(ts_path):
                print(f"[SignRecognizer/rgb] missing {ts_path}")
                return
            self.model = torch.jit.load(ts_path, map_location=self.device).eval()
            self.id2label = {int(k): v for k, v in json.load(open(os.path.join(RGB_DIR, "labels.json"))).items()}
            self.available = True
        except Exception as e:
            print(f"[SignRecognizer/rgb] init failed: {e}")

    def predict(self, frames: np.ndarray):
        import cv2
        T = frames.shape[0]
        idx = np.linspace(0, max(T - 1, 0), 16).astype(int)
        clip = np.stack([cv2.resize(frames[i], (172, 172)) for i in idx])  # MoViNet-A0
        x = (clip.astype(np.float32) / 255.0).transpose(3, 0, 1, 2)[None]  # (1, C, T, H, W)
        with self.torch.no_grad():
            logits = self.model(self.torch.from_numpy(x).to(self.device))[0]
        probs = self.torch.softmax(logits, dim=-1).cpu().numpy()
        top5_idx = np.argsort(probs)[::-1][:5]
        top1, conf = int(top5_idx[0]), float(probs[top5_idx[0]])
        return self.id2label.get(top1, str(top1)), conf, [self.id2label.get(int(i), str(int(i))) for i in top5_idx]


class SignRecognizer:
    def __init__(self):
        if FORCE_DUMMY:
            self.pose = self.rgb = None
        else:
            self.pose = _PoseBackend() if MODE in ("pose", "ensemble") else None
            self.rgb  = _RgbBackend()  if MODE in ("rgb",  "ensemble") else None
        self.dummy = _DummyBackend()
        active = []
        if self.pose and self.pose.available: active.append("pose")
        if self.rgb  and self.rgb.available:  active.append("rgb")
        self.available = bool(active)
        print(f"[SignRecognizer] mode={MODE} active={active or ['DUMMY']}")

    def predict(self, frames: np.ndarray):
        """frames: (T, H, W, 3) uint8 RGB. Returns (gloss, confidence, top5)."""
        if not self.available:
            return self.dummy.predict(frames)

        # Pose first when allowed
        if self.pose and self.pose.available:
            label, conf, top5, hand_hits = self.pose.predict(frames)
            pose_ok = conf >= POSE_CONFIDENCE_THRESHOLD and hand_hits >= 8
            if pose_ok or not (self.rgb and self.rgb.available):
                return label, conf, top5

        # Fallback / RGB-only mode
        if self.rgb and self.rgb.available:
            return self.rgb.predict(frames)

        return self.dummy.predict(frames)
