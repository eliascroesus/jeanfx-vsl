"""The money scene behind every graphic in the thank-you video (in place of AB's flat green gradient): $100 bills
falling in slow motion at three depths (far ones small and soft, a few huge out-of-focus ones drifting past the lens),
tumbling as they fall, light dust drifting up, on a near-black set with a soft green light from below. Rendered once
as a 20 s clip; each graphic takes its own slice and grades it (green, red) and darkens it behind the text.

    python ty_money_bg.py OUT.mp4 [--jobs 4]
"""
import math, os, subprocess, sys
from multiprocessing import Process
import numpy as np
import cv2
from PIL import Image

W, H, FPS, DUR = 1920, 1080, 30, 20.0
GEN = "/home/user/work/gen"


def texture(side):
    im = Image.open(f"{GEN}/bill_{side}_cut.png").convert("RGBA").resize((1200, 510), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    rgb = a[..., :3]
    # a real $100's colours: pale green-cream paper, deep green-black ink (the texture is grey)
    lum = np.clip((rgb.mean(2, keepdims=True) - 70) / 160, 0, 1) ** 1.3
    ink, paper = np.array([30, 52, 40], np.float32), np.array([212, 226, 198], np.float32)
    a[..., :3] = ink + (paper - ink) * lum
    return a


class Bill:
    def __init__(self, r, layer):
        self.layer = layer
        self.z = {"far": r.uniform(0.22, 0.42), "mid": r.uniform(0.55, 0.85), "near": r.uniform(1.7, 2.6)}[layer]
        span = H + 900 * self.z
        self.vy = {"far": r.uniform(55, 95), "mid": r.uniform(90, 150), "near": r.uniform(170, 260)}[layer]
        self.y0 = r.uniform(-450 * self.z, H + 300) - self.vy * r.uniform(0, 4)
        self.span = span + 600 * self.z
        self.x0 = r.uniform(-150, W + 150)
        self.sway, self.sway_f, self.ph = r.uniform(30, 110), r.uniform(0.25, 0.6), r.uniform(0, 6.28)
        self.ax, self.ay, self.az = r.uniform(0, 6.28, 3)
        self.wx, self.wy, self.wz = r.uniform(-1.1, 1.1), r.uniform(-1.4, 1.4), r.uniform(-0.5, 0.5)
        self.side = "front" if r.uniform() < 0.55 else "back"
        self.blur = {"far": r.uniform(3.5, 6), "mid": r.uniform(0.8, 2.0), "near": r.uniform(16, 26)}[layer]
        self.light = {"far": 0.42, "mid": 0.7, "near": 0.55}[layer] * r.uniform(0.85, 1.1)

    def corners(self, t):
        y = (self.y0 + self.vy * t) % self.span - 450 * self.z
        x = self.x0 + self.sway * math.sin(self.sway_f * t * 6.28 + self.ph)
        ax, ay, az = self.ax + self.wx * t, self.ay + self.wy * t, self.az + self.wz * t
        hw, hh = 0.5 * 420 * self.z, 0.5 * 178 * self.z
        pts = np.array([[-hw, -hh, 0], [hw, -hh, 0], [hw, hh, 0], [-hw, hh, 0]], np.float32)
        # a falling bill curls: bend the corners a little out of plane
        pts[:, 2] += 0.18 * hw * np.sin(ay * 2 + np.array([0, 1.5, 3, 4.5]))
        cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
        R = (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
             @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))
        p = pts @ R.T
        f = 1100.0
        zz = p[:, 2] + f
        return np.stack([x + p[:, 0] * f / zz, y + p[:, 1] * f / zz], 1), cy * cx


def scene(seed=11):
    r = np.random.default_rng(seed)
    bills = [Bill(r, "far") for _ in range(46)] + [Bill(r, "mid") for _ in range(12)] + [Bill(r, "near") for _ in range(3)]
    dust = np.column_stack([r.uniform(0, W, 140), r.uniform(0, H, 140), r.uniform(1.5, 5.5, 140), r.uniform(10, 45, 140),
                            r.uniform(0, 6.28, 140), r.uniform(0.25, 1.0, 140)])
    return bills, dust


def base_light():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W * 0.5) / (W * 0.55)) ** 2 + ((yy - H * 1.05) / (H * 0.75)) ** 2))
    top = np.exp(-(((xx - W * 0.3) / (W * 0.35)) ** 2 + ((yy + H * 0.1) / (H * 0.45)) ** 2))
    img = np.zeros((H, W, 3), np.float32) + np.array([4, 6, 5], np.float32)
    img += g[..., None] * np.array([10, 52, 30], np.float32) + top[..., None] * np.array([14, 22, 18], np.float32)
    return img


def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.66)) ** 2)
    return (1 - 0.62 * np.clip(d - 0.35, 0, 1) ** 1.4)[..., None]


def finish(fr, vig):
    """Bloom on the bright bits, then the vignette (a lens look)."""
    small = cv2.resize(fr, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    bright = np.clip(small - 120, 0, None)
    bloom = cv2.resize(cv2.GaussianBlur(bright, (0, 0), 9), (W, H))
    return (fr + bloom * 0.55) * vig


def draw_bill(frame, tex, b, t):
    src = np.float32([[0, 0], [1199, 0], [1199, 509], [0, 509]])
    q, facing = b.corners(t)
    pad = int(b.blur * 3) + 6
    x0, y0 = np.floor(q.min(0)).astype(int) - pad
    x1, y1 = np.ceil(q.max(0)).astype(int) + pad
    if x1 < 0 or y1 < 0 or x0 > W or y0 > H:
        return
    x0c, y0c, x1c, y1c = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x1c - x0c < 3 or y1c - y0c < 3:
        return
    M = cv2.getPerspectiveTransform(src, np.float32(q - [x0, y0]))
    tx = tex[b.side if facing >= 0 else ("back" if b.side == "front" else "front")]
    w = cv2.warpPerspective(tx, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    if b.blur > 0.6:
        w = cv2.GaussianBlur(w, (0, 0), b.blur)
    w = w[y0c - y0:y1c - y0, x0c - x0:x1c - x0]
    shade = b.light * (0.62 + 0.38 * abs(facing))
    # key light from the top left: the side of the bill facing it is brighter, falling off across it
    hh, ww = w.shape[:2]
    gy = np.linspace(1.25, 0.78, hh, dtype=np.float32)[:, None, None]
    gx = np.linspace(1.08, 0.92, ww, dtype=np.float32)[None, :, None]
    rgb = w[..., :3] * shade * gy * gx
    if b.layer == "far":                           # haze: far bills sink into the set's colour
        rgb = rgb * 0.7 + np.array([8, 30, 18], np.float32) * 0.3
    a = w[..., 3:4] / 255
    dst = frame[y0c:y1c, x0c:x1c]
    dst[:] = dst * (1 - a) + rgb * a


def render(f0, f1, out, seed=11):
    bills, dust = scene(seed)
    tex = {s: texture(s) for s in ("front", "back")}
    base = base_light()
    order = sorted(bills, key=lambda b: b.z)
    vig = vignette()
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    for i in range(f0, f1):
        t = i / FPS
        fr = base.copy()
        for b in order:
            if b.layer == "near":
                continue
            draw_bill(fr, tex, b, t)
        # dust: soft points of light drifting up
        glow = np.zeros((H // 4, W // 4), np.float32)
        for x, y, s, v, ph, br in dust:
            yy = (y - v * t) % H
            xx = (x + 20 * math.sin(t * 0.7 + ph)) % W
            cv2.circle(glow, (int(xx / 4), int(yy / 4)), max(1, int(s / 2)), float(br * (0.6 + 0.4 * math.sin(t * 2 + ph))), -1, cv2.LINE_AA)
        glow = cv2.GaussianBlur(cv2.resize(glow, (W, H)), (0, 0), 3)
        fr += glow[..., None] * np.array([150, 230, 170], np.float32) * 0.55
        for b in order:
            if b.layer == "near":
                draw_bill(fr, tex, b, t)
        fr = finish(fr, vig)
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    out = sys.argv[1]
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
    n = int(DUR * FPS)
    step = math.ceil(n / jobs)
    parts = [(s, min(s + step, n), f"{out}.part{k}.mp4") for k, s in enumerate(range(0, n, step))]
    ps = [Process(target=render, args=p) for p in parts]
    [p.start() for p in ps]
    [p.join() for p in ps]
    with open(out + ".txt", "w") as f:
        for _, _, p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", out + ".txt", "-c", "copy", out], check=True)
    for _, _, p in parts:
        os.remove(p)
    os.remove(out + ".txt")
