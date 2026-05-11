"""Build tutor reference landmarks (with stale-path fallback).

Tries the dataset's stored video path first. If that file doesn't exist,
falls back to scanning the HF cache for a matching class folder.
"""
import os, json, glob, cv2, numpy as np, mediapipe as mp
print("STEP 0: started", flush=True)

BASE   = r"C:\Users\Maleeha\Desktop\dl project\local_runs"
HF_ORG = "sign-lang"
HF_CACHE_DATA = r"C:\Users\Maleeha\.cache\huggingface\hub\datasets--Voxel51--WLASL\snapshots\3cf8daaac08088798f539d62fa511028bf5e6fd0\data"

os.environ.setdefault("HF_TOKEN",
    os.environ.get("HF_TOKEN") or "hf_paste_your_token_here")

os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import warnings; warnings.filterwarnings("ignore")

from huggingface_hub import login, whoami
login(token=os.environ["HF_TOKEN"], add_to_git_credential=False)
ME = whoami(token=os.environ["HF_TOKEN"])["name"]
print(f"STEP 1: logged in as {ME}", flush=True)


mp_hol = mp.solutions.holistic

EXPECTED_DIM = 1629   # 33*4 + 21*3 + 21*3 + 468*3 = 132 + 63 + 63 + 1404

def lm_frame(rgb, hol):
    r = hol.process(rgb)
    pose = np.zeros((33, 4), np.float32); lh = np.zeros((21, 3), np.float32)
    rh   = np.zeros((21, 3), np.float32); face = np.zeros((468, 3), np.float32)
    if r.pose_landmarks:
        pts = [[p.x, p.y, p.z, getattr(p, "visibility", 0.0)] for p in r.pose_landmarks.landmark]
        pose = np.array(pts, dtype=np.float32)[:33, :4]   # clamp to 33 x 4
    if r.left_hand_landmarks:
        lh = np.array([[p.x, p.y, p.z] for p in r.left_hand_landmarks.landmark], dtype=np.float32)[:21, :3]
    if r.right_hand_landmarks:
        rh = np.array([[p.x, p.y, p.z] for p in r.right_hand_landmarks.landmark], dtype=np.float32)[:21, :3]
    if r.face_landmarks:
        face = np.array([[p.x, p.y, p.z] for p in r.face_landmarks.landmark], dtype=np.float32)[:468, :3]
    vec = np.concatenate([pose.ravel(), lh.ravel(), rh.ravel(), face.ravel()]).astype(np.float32)
    # Pad or truncate to EXPECTED_DIM defensively
    if vec.shape[0] > EXPECTED_DIM:
        vec = vec[:EXPECTED_DIM]
    elif vec.shape[0] < EXPECTED_DIM:
        vec = np.pad(vec, (0, EXPECTED_DIM - vec.shape[0]))
    return vec

def video_to_seq(path, hol, n=32):
    cap = cv2.VideoCapture(path)
    tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if tot < 1:
        cap.release()
        raise ValueError("no frames")
    idxs = np.linspace(0, max(tot - 1, 0), n).astype(int)
    out = np.zeros((n, 1629), np.float32)
    for j, i in enumerate(idxs):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, f = cap.read()
        if ok:
            out[j] = lm_frame(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), hol)
    cap.release()
    return out


from datasets import load_from_disk, Video
print("STEP 2: loading train set + vocab", flush=True)
train = load_from_disk(f"{BASE}/data/wlasl_top300_train").cast_column("video", Video(decode=False))
gloss2id = json.load(open(f"{BASE}/models/gloss_vocab.json"))
print(f"  {len(train)} train rows, {len(gloss2id)} classes", flush=True)

NUM_LESSONS = 30
LESSONS = sorted(gloss2id.keys())[:NUM_LESSONS]
print(f"STEP 3: lessons = {LESSONS}", flush=True)

# Find first available video PATH per label (whatever the dataset stores)
paths_by_label = {}
for ex in train:
    lid = ex["label"]
    if lid not in paths_by_label:
        v = ex["video"]
        p = v["path"] if isinstance(v, dict) else v
        paths_by_label[lid] = p
print(f"  cached {len(paths_by_label)} candidate paths from dataset", flush=True)

# Print one sample to see what the stored path looks like
if paths_by_label:
    any_lid = next(iter(paths_by_label))
    print(f"  sample stored path: {paths_by_label[any_lid]}", flush=True)


def resolve_clip(lesson_name, label_id):
    """Find a real .mp4 on disk for this lesson."""
    # 1. Try the dataset's stored path as-is
    p = paths_by_label.get(label_id)
    if p and os.path.exists(p):
        return p

    # 2. Try HF_CACHE_DATA / <lesson_name> / first .mp4
    cand_dir = os.path.join(HF_CACHE_DATA, lesson_name)
    if os.path.isdir(cand_dir):
        mp4s = glob.glob(os.path.join(cand_dir, "*.mp4"))
        if mp4s:
            return mp4s[0]

    # 3. If the stored path was a filename only, search HF_CACHE_DATA recursively
    if p:
        fname = os.path.basename(p)
        matches = glob.glob(os.path.join(HF_CACHE_DATA, "**", fname), recursive=True)
        if matches:
            return matches[0]

    return None


print("STEP 4: extracting landmarks (one clip per lesson)", flush=True)
hol = mp_hol.Holistic(static_image_mode=False, model_complexity=0)
raw = {}
try:
    for lesson in LESSONS:
        lid = gloss2id[lesson]
        path = resolve_clip(lesson, lid)
        if not path:
            print(f"  SKIP (no clip on disk): {lesson}", flush=True); continue
        try:
            seq = video_to_seq(path, hol)
            raw[lesson] = seq
            print(f"  built {lesson} from {os.path.basename(path)}", flush=True)
        except Exception as e:
            print(f"  SKIP ({e}): {lesson}", flush=True)
finally:
    hol.close()
print(f"STEP 5: built landmarks for {len(raw)} lessons", flush=True)


# ST-GCN encoder embeddings (optional)
ENCODER = f"{BASE}/models/sthgcn_wlasl300/encoder.onnx"
embeddings = {}
if raw and os.path.exists(ENCODER):
    print("STEP 6: computing ST-GCN encoder embeddings", flush=True)
    import onnxruntime as ort
    sess = ort.InferenceSession(ENCODER, providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0].name
    for lesson, seq in raw.items():
        x = seq.astype(np.float32)[None, ...]
        (emb,) = sess.run(None, {inp: x})
        embeddings[lesson] = emb.squeeze().tolist()
    print(f"  embeddings for {len(embeddings)} lessons", flush=True)
else:
    print(f"STEP 6: skipping embeddings (raw={len(raw)}, encoder exists={os.path.exists(ENCODER)})", flush=True)


# Save + push only if non-empty
blob = {}
for lesson, seq in raw.items():
    entry = {"landmarks": seq.tolist()}
    if lesson in embeddings:
        entry["embedding"] = embeddings[lesson]
    blob[lesson] = entry

out_path = f"{BASE}/models/reference_signs.json"
json.dump(blob, open(out_path, "w"))
print(f"STEP 7: saved {len(blob)} references -> {out_path}", flush=True)

if not blob:
    print("STEP 8: no references built — skipping push", flush=True)
    print("STEP 9: done (with 0 lessons — tutor falls back to DTW-only)", flush=True)
else:
    from huggingface_hub import HfApi, create_repo
    from huggingface_hub.utils import HfHubHTTPError
    api = HfApi()
    SLUG = "sign-tutor-refs"
    def push(org):
        repo = f"{org}/{SLUG}"
        print(f"STEP 8: pushing to {repo}", flush=True)
        create_repo(repo, repo_type="model", private=True, exist_ok=True,
                    token=os.environ["HF_TOKEN"])
        api.upload_file(
            path_or_fileobj=out_path,
            path_in_repo="reference_signs.json",
            repo_id=repo, repo_type="model",
            token=os.environ["HF_TOKEN"],
        )
        print(f"  pushed -> {repo}", flush=True)

    try:
        push(HF_ORG)
    except HfHubHTTPError as e:
        code = e.response.status_code if e.response is not None else None
        if code in (401, 403):
            print(f"  cannot push to {HF_ORG}; falling back to {ME}", flush=True)
            push(ME)
        else:
            raise
    print("STEP 9: all done", flush=True)
