"""Render Jean's AB-style VSL from edit.json.

1. base.mp4: the raw recording cut down to the kept pieces (frame-exact, 30 fps).
2. Frames: the shot (with AB's zoom moves) plus every element, drawn in z order, rendered in parallel chunks.
3. Audio: voice chain + the boom-free song bed (15 LU under the voice, like AB) + sound effects, mastered to -14 LUFS.

    python render.py edit.json OUT.mp4 [--jobs 4] [--range t0 t1] [--audio-only] [--video-only]
"""
import json, math, os, subprocess, sys
from multiprocessing import Process

import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fx
import elements as E

W, H, FPS = 1920, 1080, 30
RAW = "/home/user/work/jean/jeanfxvsl.mov"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-3000:])
    return r


def make_base(edit, path):
    """The kept frames of the raw recording, in one pass (select by frame number), re-timed to a clean 30 fps."""
    if os.path.exists(path):
        return
    expr = "+".join(f"between(n,{a},{b - 1})" for a, b in edit["keep_frames"])
    run(["ffmpeg", "-y", "-v", "error", "-i", RAW, "-vf", f"select='{expr}',setpts=N/{FPS}/TB,format=yuv420p", "-an",
         "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-g", "15", path + ".tmp.mp4"])
    os.replace(path + ".tmp.mp4", path)


class Zoom:
    """AB's zoom: moves between framings (fast ease-out punch or a hard cut) with a slow drift while holding."""

    def __init__(self, moves):
        self.m = sorted(moves, key=lambda x: x["t"])

    def at(self, t):
        z, cx, cy = 1.0, W / 2, H / 2
        hold, drift = None, 0.0
        for mv in self.m:
            if mv["t"] > t:
                break
            if hold is not None and mv["t"] > hold:          # carry the drift of the previous hold (no jump)
                z *= 1 + min(drift * (mv["t"] - hold), 0.03)
            dur = mv.get("dur", 0.35)
            if mv.get("ease") == "cut":
                k = 1.0
            elif mv.get("ease", "out") == "out":
                k = fx.ease_out((t - mv["t"]) / dur, 3)
            else:
                k = fx.ease_in_out((t - mv["t"]) / dur)
            z = z + (mv["z"] - z) * k
            cx = cx + (mv.get("cx", W / 2) - cx) * k
            cy = cy + (mv.get("cy", H / 2) - cy) * k
            hold, drift = mv["t"] + (0 if mv.get("ease") == "cut" else dur), mv.get("drift", 0.004)
        if hold is not None and t > hold:
            z *= 1 + min(drift * (t - hold), 0.03)
        return z, cx, cy

    @staticmethod
    def apply(base, z, cx, cy):
        if abs(z - 1) < 0.002:
            return base
        cw, ch = W / z, H / z
        x0 = min(max(cx - cw / 2, 0), W - cw)
        y0 = min(max(cy - ch / 2, 0), H - ch)
        M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
        out = cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        if z > 1.04:                                   # 1080p source: a touch of sharpening on punch-ins
            bl = cv2.GaussianBlur(out, (0, 0), 1.3)
            out = cv2.addWeighted(out, 1.45, bl, -0.45, 0)
        return out


def render_chunk(edit, base_path, f0, f1, out_path):
    zoom = Zoom(edit["zoom"])
    els = [d for d in edit["elements"] if d["t1"] > f0 / FPS - 0.5 and d["t0"] < f1 / FPS + 0.5]
    objs = sorted([E.build(d) for d in els], key=lambda o: o.z)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f0 / FPS:.5f}", "-i", base_path, "-frames:v", str(f1 - f0),
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-g", "60", out_path], stdin=subprocess.PIPE)
    last = None
    for i in range(f0, f1):
        t = i / FPS
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            raw = last
        last = raw
        base = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        z, cx, cy = zoom.at(t)
        shot = Zoom.apply(base, z, cx, cy)
        frame = shot.astype(np.float32)
        ctx = {"base": base, "shot": shot}
        for o in objs:
            if o.active(t):
                o.draw(frame, t, ctx)
        enc.stdin.write(np.clip(frame, 0, 255).astype(np.uint8).tobytes())
        if (i - f0) % 300 == 0:
            print(f"  chunk {f0}: {t:7.1f}s", flush=True)
    enc.stdin.close()
    enc.wait()
    dec.kill()


def render_video(edit, out_dir, jobs, rng=None):
    base = os.environ.get("JEAN_BASE", f"{out_dir}/base.mp4")
    make_base(edit, base)
    n = int(round(edit["total"] * FPS))
    a, b = (0, n) if rng is None else (int(rng[0] * FPS), min(n, int(rng[1] * FPS)))
    step = math.ceil((b - a) / jobs)
    chunks = [(s, min(s + step, b)) for s in range(a, b, step)]
    procs = []
    for k, (s, e) in enumerate(chunks):
        p = Process(target=render_chunk, args=(edit, base, s, e, f"{out_dir}/chunk_{k:02d}.mp4"))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
        if p.exitcode:
            sys.exit(f"chunk failed ({p.exitcode})")
    with open(f"{out_dir}/chunks.txt", "w") as f:
        for k in range(len(chunks)):
            f.write(f"file 'chunk_{k:02d}.mp4'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{out_dir}/chunks.txt", "-c", "copy",
         f"{out_dir}/video.mp4"])
    return a / FPS, b / FPS


def main():
    edit_path, out = sys.argv[1], sys.argv[2]
    edit = json.load(open(edit_path))
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
    rng = None
    if "--range" in sys.argv:
        i = sys.argv.index("--range")
        rng = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
    out_dir = os.path.splitext(out)[0] + "_work"
    os.makedirs(out_dir, exist_ok=True)
    t0, t1 = 0.0, edit["total"]
    if "--audio-only" not in sys.argv:
        t0, t1 = render_video(edit, out_dir, jobs, rng)
    if "--video-only" in sys.argv:
        return
    import mix
    mix.mix(edit, f"{out_dir}/mix.wav")
    run(["ffmpeg", "-y", "-v", "error", "-i", f"{out_dir}/video.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
         "-i", f"{out_dir}/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-shortest", "-movflags", "+faststart", out])
    print("done", out)


if __name__ == "__main__":
    main()
