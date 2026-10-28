"""Find the moments Jean's screen recording jumps to a new page (dashboard, email, certificate), so each one gets a
mouse click. Works on the cut base video (output time) and ignores his webcam in the top-right corner.

    python proof_clicks.py base.mp4 t0 t1 out.json
"""
import json, subprocess, sys
import numpy as np

src, t0, t1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
FPS, W, H = 15, 384, 216
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", src, "-vf", f"fps={FPS},scale={W}:{H}",
                      "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
mask = np.ones((H, W), bool)
mask[:int(H * 0.36), int(W * 0.72):] = False          # webcam
d = np.array([np.abs(fr[i + 1] - fr[i])[mask].mean() for i in range(len(fr) - 1)])
med = np.median(d)
times = []
for i, v in enumerate(d):
    if v > max(6 * med, 7.0) and (not times or (i + 1) / FPS + t0 - times[-1] > 0.5):
        times.append(round(t0 + (i + 1) / FPS, 3))
json.dump(times, open(out, "w"))
print(len(times), "page changes", times[:20])
