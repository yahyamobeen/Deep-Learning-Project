"""Pre-extract MediaPipe landmarks for all WLASL-Top-300 videos.
Runs OUTSIDE Jupyter to free ~1.5 GB of RAM.

Usage from PowerShell with the venv active, in training/ folder:
    python extract_landmarks.py
    python extract_landmarks.py val           # only val split
    python extract_landmarks.py val test      # multiple splits
"""
import os, sys, gc, time, glob, json, cv2, numpy as np, mediapipe as mp
from datasets import load_from_disk, Video

BASE  = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
CACHE = f"{BASE}/data/wlasl_top300_landmarks_npz"
os.makedirs(CACHE, exist_ok=True)

# Where the real .mp4 files live (Voxel51 HF cache layout)
HF_CACHE_DATA = r"C:\Users\Maleeha\.cache\huggingface\hub\datasets--Voxel51--WLASL\snapshots\3cf8daaac08088798f539d62fa511028bf5e6fd0\data"

# Build a filename -> absolute-path index ONCE so every lookup is O(1)
_FNAME_INDEX = {}
if os.path.isdir(HF_CACHE_DATA):
    for class_dir in os.listdir(HF_CACHE_DATA):
        full_dir = os.path.join(HF_CACHE_DATA, class_dir)
        if os.path.isdir(full_dir):
            for mp4 in os.listdir(full_dir):
                if mp4.endswith(".mp4"):
                    _FNAME_INDEX[mp4] = os.path.join(full_dir, mp4)
    print(f"indexed {len(_FNAME_INDEX)} videos in HF cache", flush=True)


def resolve_path(stored_path):
    """Make the dataset's stored path absolute + correct."""
    if not stored_path:
        return None
    # 1. Already absolute and exists
    if os.path.isabs(stored_path) and os.path.exists(stored_path):
        return stored_path
    # 2. Look up filename in the pre-built index
    fname = os.path.basename(stored_path)
    if fname in _FNAME_INDEX:
        return _FNAME_INDEX[fname]
    return None

CHUNK             = 50
MEDIAPIPE_COMPLEX = 0
NUM_FRAMES        = 32
EXPECTED_DIM      = 1629   # 33*4 + 21*3 + 21*3 + 468*3

mp_hol = mp.solutions.holistic


def lm_frame(rgb, hol):
    r = hol.process(rgb)
    pose = np.zeros((33, 4), np.float32); lh = np.zeros((21, 3), np.float32)
    rh   = np.zeros((21, 3), np.float32); face = np.zeros((468, 3), np.float32)
    if r.pose_landmarks:
        pts = [[p.x, p.y, p.z, getattr(p, "visibility", 0.0)] for p in r.pose_landmarks.landmark]
        pose = np.array(pts, dtype=np.float32)[:33, :4]
    if r.left_hand_landmarks:
        lh = np.array([[p.x, p.y, p.z] for p in r.left_hand_landmarks.landmark], dtype=np.float32)[:21, :3]
    if r.right_hand_landmarks:
        rh = np.array([[p.x, p.y, p.z] for p in r.right_hand_landmarks.landmark], dtype=np.float32)[:21, :3]
    if r.face_landmarks:
        face = np.array([[p.x, p.y, p.z] for p in r.face_landmarks.landmark], dtype=np.float32)[:468, :3]
    vec = np.concatenate([pose.ravel(), lh.ravel(), rh.ravel(), face.ravel()]).astype(np.float32)
    if vec.shape[0] > EXPECTED_DIM:
        vec = vec[:EXPECTED_DIM]
    elif vec.shape[0] < EXPECTED_DIM:
        vec = np.pad(vec, (0, EXPECTED_DIM - vec.shape[0]))
    return vec


def video_to_seq(path, hol, n=NUM_FRAMES):
    cap = cv2.VideoCapture(path)
    tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    idxs = np.linspace(0, max(tot-1, 0), n).astype(int)
    out = np.zeros((n, EXPECTED_DIM), dtype=np.float32)
    for j, i in enumerate(idxs):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if ok:
            out[j] = lm_frame(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), hol)
    cap.release()
    return out


def cache_split(name):
    final = f"{CACHE}/{name}.npz"
    if os.path.exists(final):
        print(f"{name}: already cached"); return

    chunk_dir = f"{CACHE}/{name}_chunks"
    os.makedirs(chunk_dir, exist_ok=True)

    ds_path = f"{BASE}/data/wlasl_top300_{name}"
    if not os.path.exists(ds_path):
        print(f"{name}: dataset folder missing, skipping"); return

    ds = load_from_disk(ds_path).cast_column("video", Video(decode=False))
    N = len(ds)
    done = sorted(int(f[:-4].split("_")[-1]) for f in os.listdir(chunk_dir) if f.endswith(".npz"))
    start = (done[-1] + 1) if done else 0
    total = (N + CHUNK - 1) // CHUNK
    print(f"{name}: {N} clips, {total} chunks, resume@{start}", flush=True)

    hol = mp_hol.Holistic(
        static_image_mode=False,
        model_complexity=MEDIAPIPE_COMPLEX,
        refine_face_landmarks=False,
        enable_segmentation=False,
        smooth_landmarks=False,
    )
    try:
        for cid in range(start, total):
            lo, hi = cid * CHUNK, min((cid + 1) * CHUNK, N)
            X = np.zeros((hi - lo, NUM_FRAMES, EXPECTED_DIM), dtype=np.float32)
            y = np.zeros(hi - lo, dtype=np.int64)
            t0 = time.time()
            missing_paths = 0
            for j in range(lo, hi):
                ex = ds[j]
                v = ex["video"]
                raw_path = v["path"] if isinstance(v, dict) else v
                path = resolve_path(raw_path)
                if path is None:
                    missing_paths += 1
                    y[j - lo] = ex["label"]   # leave X[j-lo] as zeros
                    continue
                try:
                    X[j - lo] = video_to_seq(path, hol)
                    y[j - lo] = ex["label"]
                except Exception as e:
                    print(f"  skip {path}: {e}", flush=True)
            if missing_paths > 0:
                print(f"  WARNING: {missing_paths}/{hi-lo} videos unresolved", flush=True)
            np.savez_compressed(f"{chunk_dir}/chunk_{cid:04d}.npz", X=X, y=y)
            del X, y; gc.collect()
            print(f"  chunk {cid+1}/{total}  ({hi-lo} clips, {time.time()-t0:.0f}s)", flush=True)
    finally:
        hol.close()

    chunk_files = sorted(f for f in os.listdir(chunk_dir) if f.endswith(".npz"))
    Xs, ys = [], []
    for f in chunk_files:
        d = np.load(f"{chunk_dir}/{f}")
        Xs.append(d["X"]); ys.append(d["y"])
    X_all = np.concatenate(Xs, axis=0); y_all = np.concatenate(ys, axis=0)
    np.savez_compressed(final, X=X_all, y=y_all)
    del Xs, ys, X_all, y_all; gc.collect()
    print(f"{name}: merged -> {final}", flush=True)


if __name__ == "__main__":
    splits = sys.argv[1:] if len(sys.argv) > 1 else ["val", "test", "train"]
    for s in splits:
        cache_split(s)
        gc.collect()
    print("all done")
