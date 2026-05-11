"""CPU latency micro-benchmark for the SignRecognizer.

Usage:
    python scripts/bench_latency.py --n 100 --device cpu

Reports p50 / p95 / p99 latency in milliseconds and asserts p95 < 350 ms
(the project SLO from docs/RESULTS.md).
"""
import argparse
import os
import sys
import time
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.inference.sign_recognizer import SignRecognizer  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--slo-ms", type=float, default=350.0)
    ap.add_argument("--frames", type=int, default=32)
    args = ap.parse_args()

    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    rec = SignRecognizer()
    rng = np.random.default_rng(42)
    clips = [rng.integers(0, 256, (args.frames, 224, 224, 3), dtype=np.uint8) for _ in range(args.n)]

    # Warm-up
    for _ in range(3):
        rec.predict(clips[0])

    times_ms = []
    for clip in clips:
        t0 = time.perf_counter()
        rec.predict(clip)
        times_ms.append((time.perf_counter() - t0) * 1000.0)

    arr = np.asarray(times_ms)
    p50, p95, p99 = np.percentile(arr, [50, 95, 99])
    print(f"N={args.n}  device={args.device}")
    print(f"  p50 = {p50:7.1f} ms")
    print(f"  p95 = {p95:7.1f} ms   (SLO {args.slo_ms} ms)")
    print(f"  p99 = {p99:7.1f} ms")
    print(f"  max = {arr.max():7.1f} ms")

    if p95 > args.slo_ms:
        print(f"FAIL: p95 {p95:.1f} ms > SLO {args.slo_ms:.1f} ms", file=sys.stderr)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
