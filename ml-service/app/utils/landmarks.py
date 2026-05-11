"""MediaPipe Holistic landmark extraction (1629-D per frame) + raw-frame loader."""
import cv2, numpy as np, mediapipe as mp


def read_frames(path: str, num_frames: int = 16) -> np.ndarray:
    """Uniform frame sample from a video file. Returns (T, H, W, 3) uint8 RGB."""
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idxs = np.linspace(0, max(total - 1, 0), num_frames).astype(int)
    frames = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = cap.read()
        if not ok:
            frames.append(np.zeros((224, 224, 3), dtype=np.uint8)); continue
        frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    cap.release()
    return np.stack(frames)

_mp_hol = mp.solutions.holistic


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
        pose = np.zeros((33, 4));  lh = np.zeros((21, 3))
        rh   = np.zeros((21, 3));  face = np.zeros((468, 3))
        if res.pose_landmarks:
            pose = np.array([[p.x, p.y, p.z, p.visibility] for p in res.pose_landmarks.landmark])
        if res.left_hand_landmarks:
            lh = np.array([[p.x, p.y, p.z] for p in res.left_hand_landmarks.landmark])
        if res.right_hand_landmarks:
            rh = np.array([[p.x, p.y, p.z] for p in res.right_hand_landmarks.landmark])
        if res.face_landmarks:
            face = np.array([[p.x, p.y, p.z] for p in res.face_landmarks.landmark])
        return np.concatenate([pose.flatten(), lh.flatten(), rh.flatten(), face.flatten()]).astype(np.float32)

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
