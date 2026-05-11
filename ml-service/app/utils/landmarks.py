"""MediaPipe Holistic landmark extraction (1629-D per frame) + raw-frame loader."""
import cv2, numpy as np, mediapipe as mp


def read_frames(path: str, num_frames: int = 16, size: int = 224) -> np.ndarray:
    """Uniform frame sample from a video file. Returns (T, size, size, 3) uint8 RGB.

    Every frame is resized to (size x size) so np.stack always succeeds even when
    the source clip changes resolution mid-recording (common with browser webcam).
    """
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idxs = np.linspace(0, max(total - 1, 0), num_frames).astype(int)
    frames = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if not ok:
            frames.append(np.zeros((size, size, 3), dtype=np.uint8)); continue
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA)
        frames.append(rgb)
    cap.release()
    return np.stack(frames)

_mp_hol = mp.solutions.holistic
EXPECTED_DIM = 1629   # 33*4 + 21*3 + 21*3 + 468*3 — must match trained model's input


class LandmarkExtractor:
    def __init__(self, complexity: int = 1):
        self.holistic = _mp_hol.Holistic(
            static_image_mode=False,
            model_complexity=complexity,
            min_detection_confidence=0.5,
        )

    def from_frame(self, bgr: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        res = self.holistic.process(rgb)
        pose = np.zeros((33, 4), np.float32); lh = np.zeros((21, 3), np.float32)
        rh   = np.zeros((21, 3), np.float32); face = np.zeros((468, 3), np.float32)
        if res.pose_landmarks:
            pts = [[p.x, p.y, p.z, getattr(p, "visibility", 0.0)] for p in res.pose_landmarks.landmark]
            pose = np.array(pts, dtype=np.float32)[:33, :4]
        if res.left_hand_landmarks:
            lh = np.array([[p.x, p.y, p.z] for p in res.left_hand_landmarks.landmark], dtype=np.float32)[:21, :3]
        if res.right_hand_landmarks:
            rh = np.array([[p.x, p.y, p.z] for p in res.right_hand_landmarks.landmark], dtype=np.float32)[:21, :3]
        if res.face_landmarks:
            face = np.array([[p.x, p.y, p.z] for p in res.face_landmarks.landmark], dtype=np.float32)[:468, :3]
        vec = np.concatenate([pose.ravel(), lh.ravel(), rh.ravel(), face.ravel()]).astype(np.float32)
        # Defensive clamp/pad so newer MediaPipe versions (which emit 1662-D) stay compatible
        if vec.shape[0] > EXPECTED_DIM:
            vec = vec[:EXPECTED_DIM]
        elif vec.shape[0] < EXPECTED_DIM:
            vec = np.pad(vec, (0, EXPECTED_DIM - vec.shape[0]))
        return vec

    def from_video(self, path: str, num_frames: int = 32) -> np.ndarray:
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        idxs = np.linspace(0, max(total - 1, 0), num_frames).astype(int)
        out = []
        for i in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, frame = cap.read()
            if not ok:
                out.append(np.zeros(1629, dtype=np.float32)); continue
            out.append(self.from_frame(frame))
        cap.release()
        return np.stack(out)
