"""Motion-graphic backgrounds and cards that replace stock footage: moving light gradients, rising particles (dollar
signs, embers, city-light bokeh), self-drawing glowing line charts, a glowing neural "brain", an earnings card and a
time card. All drawn from scratch every frame, so nothing is photographic and nothing needs licensing."""
import functools, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

import fx
from fx import W, H, blend, clamp, ease_out, ease_out_back, ease_in_out
from elements import El, asset

PALETTES = {
    # base colour, blobs [(rgb, radius as fraction of height, strength)]
    "blue": ((6, 9, 18), [((20, 70, 190), 0.55, 0.9), ((0, 140, 252), 0.35, 0.55), ((60, 30, 140), 0.5, 0.6), ((10, 90, 120), 0.4, 0.5)]),
    "green": ((5, 12, 9), [((10, 120, 60), 0.55, 0.85), ((40, 190, 110), 0.32, 0.5), ((10, 70, 90), 0.5, 0.6), ((90, 150, 40), 0.35, 0.35)]),
    "ember": ((8, 3, 2), [((150, 30, 5), 0.6, 0.9), ((230, 90, 10), 0.3, 0.6), ((90, 10, 20), 0.5, 0.7), ((200, 60, 0), 0.25, 0.4)]),
    "night": ((4, 6, 14), [((20, 40, 110), 0.6, 0.8), ((150, 80, 20), 0.3, 0.45), ((10, 90, 110), 0.4, 0.5), ((90, 30, 90), 0.4, 0.4)]),
    "red": ((12, 4, 5), [((140, 15, 25), 0.55, 0.85), ((220, 50, 60), 0.3, 0.45), ((70, 10, 40), 0.5, 0.6), ((120, 30, 10), 0.35, 0.4)]),
}

SW, SH = 192, 108
BRAIN = "/home/user/work/assets/fluent/brain_3d.png"


@functools.lru_cache(maxsize=2)
def _vignette(strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - strength * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    return v[..., None]


@functools.lru_cache(maxsize=2)
def _grain(seed=0):
    r = np.random.default_rng(seed)
    return [r.normal(0, 3.2, (H, W, 1)).astype(np.float32) for _ in range(3)]


@functools.lru_cache(maxsize=2)
def _grid(step=120):
    a = np.zeros((H, W), np.float32)
    a[:, ::step] = 1
    a[::step, :] = 1
    a = cv2.GaussianBlur(a, (0, 0), 0.8)
    return (a / a.max())[..., None]


class Aurora(El):
    """Dark background with big soft colour blobs drifting slowly (the moving-gradient look of motion-graphic VSLs)."""
    z = 14

    def __init__(self, d):
        super().__init__(d)
        self.base, self.blobs = PALETTES[d.get("palette", "blue")]
        r = np.random.default_rng(d.get("seed", 1))
        self.paths = [(r.uniform(0.25, 0.75) * SW, r.uniform(0.3, 0.7) * SH, r.uniform(0.15, 0.35) * SW, r.uniform(0.12, 0.3) * SH,
                       r.uniform(0.25, 0.6), r.uniform(0.2, 0.5), r.uniform(0, 6.28)) for _ in self.blobs]
        self.yy, self.xx = np.mgrid[0:SH, 0:SW].astype(np.float32)

    def draw(self, frame, t, ctx):
        d = self.d
        tt = (t - self.t0) * d.get("speed", 1.0) + d.get("seed", 1) * 3.1
        img = np.zeros((SH, SW, 3), np.float32) + np.array(self.base, np.float32)
        for (col, rad, k), (cx0, cy0, ax, ay, fx_, fy, ph) in zip(self.blobs, self.paths):
            cx = cx0 + ax * math.sin(fx_ * tt + ph)
            cy = cy0 + ay * math.cos(fy * tt + ph * 1.3)
            rr = rad * SH * (1 + 0.12 * math.sin(tt * 0.7 + ph))
            g = np.exp(-((self.xx - cx) ** 2 + (self.yy - cy) ** 2) / (2 * rr * rr))
            img += g[..., None] * np.array(col, np.float32) * k * d.get("intensity", 0.6)
        up = cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
        if d.get("grid"):
            up += _grid() * d["grid"] * 255 * 0.06
        up = up * _vignette() + _grain()[int(t * 30) % 3]
        op = clamp((t - self.t0) / d.get("fade_in", 0.0001))
        if op >= 1:
            frame[:] = up
        else:
            frame[:] = frame * (1 - op) + up * op


@functools.lru_cache(maxsize=64)
def _dot(size, rgb, soft=0.5, core=1.0):
    s = int(size * 2 + 8)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / size
    a = np.clip(1 - d, 0, 1) ** (1 + soft * 3) * core
    out = np.zeros((s, s, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a * 255
    return out


class Particles(El):
    """Particles drifting through the frame. kind: 'dollar' ($ signs rising, depth-blurred), 'ember' (sparks rising and
    flickering), 'bokeh' (soft out-of-focus city lights drifting)."""
    z = 16

    def __init__(self, d):
        super().__init__(d)
        r = np.random.default_rng(d.get("seed", 2))
        n = d.get("n", 40)
        x0, y0, x1, y1 = d.get("rect", (0, 0, W, H))
        self.rect = (x0, y0, x1, y1)
        self.p = []
        for i in range(n):
            depth = r.uniform(0, 1)
            self.p.append(dict(x=r.uniform(x0, x1), y=r.uniform(y0, y1), depth=depth, ph=r.uniform(0, 6.28),
                               sp=r.uniform(0.6, 1.4), sway=r.uniform(10, 40), hue=r.uniform(0, 1)))
        self.kind = d.get("kind", "dollar")

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        x0, y0, x1, y1 = self.rect
        hgt = y1 - y0 + 200
        op_all = min(clamp(dt / 0.3), clamp((self.t1 - t) / 0.2)) * d.get("alpha", 1.0)
        for p in sorted(self.p, key=lambda q: q["depth"]):
            dep = p["depth"]
            if self.kind == "dollar":
                speed = (60 + 160 * dep) * p["sp"]
                y = y1 + 100 - ((dt * speed + (p["y"] - y0)) % hgt)
                x = p["x"] + p["sway"] * math.sin(dt * 0.9 + p["ph"])
                size = int(26 + 70 * dep)
                col = (60, 230, 130) if p["hue"] < 0.7 else (150, 255, 190)
                bi = 4 if dep < 0.25 else 2 if dep < 0.5 else 0
                g, ox, oy = fx.glyph("bold", size, "$", col, bi)
                blend(frame, g, x + ox, y + oy, op_all * (0.25 + 0.55 * dep))
            elif self.kind == "ember":
                speed = (80 + 220 * dep) * p["sp"]
                y = y1 + 50 - ((dt * speed + (p["y"] - y0)) % hgt)
                x = p["x"] + p["sway"] * math.sin(dt * 1.7 + p["ph"]) + 20 * math.sin(dt * 4.3 + p["ph"] * 2)
                size = 4 + 11 * dep
                life = 1 - clamp((y1 - y) / (y1 - y0))
                fl = 0.6 + 0.4 * math.sin(dt * 13 + p["ph"] * 5)
                col = (255, int(120 + 100 * p["hue"]), 40)
                spr = _dot(round(size * 2.5), col, 0.8, 1.0)
                blend(frame, spr, x - spr.shape[1] / 2, y - spr.shape[0] / 2, op_all * fl * (0.3 + 0.7 * life))
                core = _dot(round(size), (255, 230, 170), 0.2, 1.0)
                blend(frame, core, x - core.shape[1] / 2, y - core.shape[0] / 2, op_all * fl * life)
            else:  # bokeh
                x = p["x"] + 25 * math.sin(dt * 0.25 + p["ph"]) + dt * 12 * (p["sp"] - 1)
                y = p["y"] + 15 * math.cos(dt * 0.2 + p["ph"])
                size = round(30 + 90 * dep)
                cols = [(255, 170, 70), (255, 210, 140), (120, 180, 255), (255, 120, 80), (180, 230, 255)]
                col = cols[int(p["hue"] * len(cols)) % len(cols)]
                spr = _dot(size, col, 0.05, 0.9)
                tw = 0.75 + 0.25 * math.sin(dt * 1.3 + p["ph"])
                blend(frame, spr, x - spr.shape[1] / 2, y - spr.shape[0] / 2, op_all * tw * (0.18 + 0.3 * (1 - dep)))


def _series(kind, n, seed):
    r = np.random.default_rng(seed)
    if kind == "up":
        v = np.cumsum(r.normal(0.5, 1.6, n))
    elif kind == "down":
        v = np.cumsum(r.normal(-0.55, 1.6, n))
    else:
        v = np.cumsum(r.normal(0.05, 2.2, n)) + 6 * np.sin(np.linspace(0, 9, n))
    v = np.convolve(np.pad(v, 2, mode="edge"), np.ones(5) / 5, "valid")
    return (v - v.min()) / (v.max() - v.min() + 1e-9)


class LineChart(El):
    """A glowing line chart that draws itself left to right, with a gradient fill under it and a bright leading dot.
    Full frame (over an Aurora) or inside a framed rect on black (Fear / Greed cards)."""
    z = 30

    def __init__(self, d):
        super().__init__(d)
        self.rect = d.get("rect")
        self.v = _series(d.get("trend", "up"), d.get("n", 90), d.get("seed", 3))
        self.col = tuple(d.get("rgb", (40, 220, 120)))

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        framed = self.rect is not None
        x0, y0, x1, y1 = self.rect if framed else (0, 0, W, H)
        w, h = x1 - x0, y1 - y0
        k = ease_out(dt / d.get("draw", 1.2), 2)
        n = len(self.v)
        m = 1 + k * (n - 1)
        i = int(m)
        pad_t, pad_b = 0.16 * h, 0.14 * h
        pts = [(w * 0.04 + j / (n - 1) * w * 0.92, pad_t + (1 - self.v[j]) * (h - pad_t - pad_b)) for j in range(min(i + 1, n))]
        if i < n - 1:
            f = m - i
            a, b = pts[-1], (w * 0.04 + (i + 1) / (n - 1) * w * 0.92, pad_t + (1 - self.v[i + 1]) * (h - pad_t - pad_b))
            pts.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        if framed:
            region = np.zeros((h, w, 3), np.float32) + np.array(d.get("bg", (10, 11, 14)), np.float32)
        else:
            region = frame[y0:y1, x0:x1]
        # grid
        gl = Image.new("L", (w, h), 0)
        gd = ImageDraw.Draw(gl)
        step = max(60, w // 10)
        for gx in range(0, w, step):
            gd.line([(gx, 0), (gx, h)], fill=40, width=1)
        for gy in range(0, h, step):
            gd.line([(0, gy), (w, gy)], fill=40, width=1)
        ga = np.asarray(gl, np.float32)[..., None] / 255 * 0.5
        region[:] = region * (1 - ga) + 255 * ga * 0.35 + region * ga
        if len(pts) >= 2:
            # area fill: polygon mask times a vertical gradient
            am = Image.new("L", (w, h), 0)
            ImageDraw.Draw(am).polygon(pts + [(pts[-1][0], h), (pts[0][0], h)], fill=255)
            grad = np.linspace(0.42, 0.0, h, dtype=np.float32)[:, None]
            aa = (np.asarray(am, np.float32) / 255 * grad)[..., None]
            region[:] = region * (1 - aa) + np.array(self.col, np.float32) * aa
            # line + glow
            lw = max(4, int(h / 140))
            lm = Image.new("L", (w, h), 0)
            ImageDraw.Draw(lm).line(pts, fill=255, width=lw, joint="curve")
            la = np.asarray(lm, np.float32) / 255
            small = cv2.resize(la, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
            glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (w, h), interpolation=cv2.INTER_LINEAR)
            region[:] = region + np.array(self.col, np.float32) * (glow[..., None] * 1.6)
            region[:] = region * (1 - la[..., None]) + np.array([min(255, c + 60) for c in self.col], np.float32) * la[..., None]
            # leading dot
            ex, ey = pts[-1]
            dot = _dot(int(lw * 5), self.col, 0.6, 1.0)
            blend(region, dot, ex - dot.shape[1] / 2, ey - dot.shape[0] / 2, 0.9)
            core = _dot(int(lw * 1.6), (255, 255, 255), 0.1, 1.0)
            blend(region, core, ex - core.shape[1] / 2, ey - core.shape[0] / 2, 1.0)
        np.clip(region, 0, 255, out=region)
        if framed:
            op = clamp(dt / 0.12)
            bd = d.get("border", 4)
            frame[y0 - bd:y1 + bd, x0 - bd:x1 + bd] = frame[y0 - bd:y1 + bd, x0 - bd:x1 + bd] * (1 - op) + 255 * op
            frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - op) + region * op


class Neural(El):
    """A brain made of glowing nodes and connections (sampled inside a brain silhouette), with signals travelling along
    the connections. Turns slowly."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        size = d.get("size", 720)
        sil = Image.open(BRAIN).convert("RGBA").resize((size, size))
        a = np.asarray(sil)[..., 3] > 128
        r = np.random.default_rng(d.get("seed", 5))
        ys, xs = np.where(a)
        idx = r.choice(len(xs), d.get("n", 170), replace=False)
        pts = np.stack([xs[idx], ys[idx]], 1).astype(np.float32)
        # spread them out a little (relaxation)
        for _ in range(12):
            dd = pts[:, None, :] - pts[None, :, :]
            dist = np.sqrt((dd ** 2).sum(2)) + np.eye(len(pts)) * 1e6
            push = (dd / dist[..., None] ** 2 * 120).sum(1)
            pts = pts + np.clip(push, -6, 6)
            pts[:, 0] = np.clip(pts[:, 0], 0, size - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, size - 1)
            ok = a[pts[:, 1].astype(int), pts[:, 0].astype(int)]
            pts[~ok] = pts[~ok] * 0.9 + np.array([size / 2, size / 2]) * 0.1
        self.pts = pts
        self.z_ = r.uniform(-1, 1, len(pts))
        dist = np.sqrt(((pts[:, None] - pts[None]) ** 2).sum(2)) + np.eye(len(pts)) * 1e6
        edges = set()
        for i in range(len(pts)):
            for j in np.argsort(dist[i])[:3]:
                edges.add((min(i, j), max(i, j)))
        self.edges = sorted(edges)
        self.eph = r.uniform(0, 1, len(self.edges))
        self.nph = r.uniform(0, 6.28, len(pts))
        self.size = size

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        s = self.size
        ang = 0.35 * math.sin(dt * 0.6)
        br = 1 + 0.02 * math.sin(dt * 2.0)
        c = s / 2
        P = self.pts.copy()
        P[:, 0] = c + (P[:, 0] - c) * math.cos(ang) * br + self.z_ * 40 * math.sin(ang)
        P[:, 1] = c + (P[:, 1] - c) * br
        k = clamp(dt / 0.5)
        layer = Image.new("RGB", (s, s), (0, 0, 0))
        dr = ImageDraw.Draw(layer)
        for (i, j), ph in zip(self.edges, self.eph):
            if (i + j) % 7 / 7 > k:
                continue
            dr.line([tuple(P[i]), tuple(P[j])], fill=(20, 80, 170), width=2)
        for (i, j), ph in zip(self.edges, self.eph):
            u = (dt * 0.9 + ph) % 1.6
            if u < 1 and k >= 1:
                x = P[i][0] + (P[j][0] - P[i][0]) * u
                y = P[i][1] + (P[j][1] - P[i][1]) * u
                dr.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(160, 220, 255))
        for i, (x, y) in enumerate(P):
            if i / len(P) > k * 1.2:
                continue
            tw = 0.6 + 0.4 * math.sin(dt * 3 + self.nph[i])
            rr = 3 + 3 * (self.z_[i] + 1) / 2
            dr.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(int(90 * tw + 80), int(170 * tw + 60), 255))
        arr = np.asarray(layer, np.float32)
        small = cv2.resize(arr, (s // 4, s // 4), interpolation=cv2.INTER_AREA)
        glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 5), (s, s), interpolation=cv2.INTER_LINEAR)
        out = np.clip(arr + glow * 2.2, 0, 255)
        x0, y0 = int(d["cx"] - s / 2), int(d["cy"] - s / 2)
        reg = frame[y0:y0 + s, x0:x0 + s]
        op = clamp(dt / 0.25)
        reg[:] = 255 - (255 - reg) * (255 - out * op) / 255          # screen blend: glows over the dark plate


def _f(kind, size):
    return fx.font(kind, size)


class Earnings(El):
    """A delivery-app style weekly earnings card: the total counts up to $500 while the daily bars grow."""
    z = 60
    BARS = [0.55, 0.72, 0.6, 0.83, 0.78, 1.0, 0.66]

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        cw, ch = 620, 720
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=(22, 22, 26, 255), outline=(60, 60, 68, 255), width=2)
        dr.text((48, 44), "Weekly earnings", font=_f("medium", 34), fill=(150, 150, 160))
        v = d.get("total", 500) * ease_out(dt / 1.1, 3)
        dr.text((48, 92), f"${v:,.2f}", font=_f("semibold", 108), fill=(255, 255, 255))
        base_y, bw, gap = 590, 56, 22
        for i, hgt in enumerate(self.BARS):
            k = ease_out_back((dt - 0.15 - i * 0.07) / 0.35, 1.3)
            if k <= 0:
                continue
            bx = 48 + i * (bw + gap)
            bh = hgt * 300 * k
            dr.rounded_rectangle((bx, base_y - bh, bx + bw, base_y), 12, fill=(255, 59, 48, 255))
            dr.text((bx + bw / 2 - 9, base_y + 18), "MTWTFSS"[i], font=_f("medium", 28), fill=(140, 140, 150))
        dr.ellipse((48, 652, 80, 684), outline=(150, 150, 160), width=3)
        dr.line([(64, 668), (64, 658)], fill=(150, 150, 160), width=3)
        dr.line([(64, 668), (72, 672)], fill=(150, 150, 160), width=3)
        dr.text((96, 648), "Last delivery 11:58 PM", font=_f("medium", 30), fill=(150, 150, 160))
        arr = np.asarray(im, np.float32)
        sc = 0.9 + 0.1 * ease_out_back(dt / 0.35, 1.6)
        arr = fx.resize_rgba(arr, sc)
        blend(frame, arr, d["cx"] - arr.shape[1] / 2, d["cy"] - arr.shape[0] / 2, clamp(dt / 0.15))


class TimeCard(El):
    """A time-clock card: the clock hands sweep from 9:00 to 5:00, then CLOCK OUT lands."""
    z = 60

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        cw, ch = 620, 720
        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((0, 0, cw - 1, ch - 1), 40, fill=(22, 22, 26, 255), outline=(60, 60, 68, 255), width=2)
        dr.text((48, 44), "TIME CARD", font=_f("bold", 34), fill=(150, 150, 160))
        span = max(self.t1 - self.t0 - 0.6, 0.8)
        k = ease_in_out(clamp((dt - 0.2) / span))
        hours = 9 + 8 * k
        cx, cy, r = cw / 2, 290, 165
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(230, 230, 236), width=8)
        for h_ in range(12):
            a = h_ / 12 * 2 * math.pi
            r0 = r - 26 if h_ % 3 == 0 else r - 16
            dr.line([(cx + math.sin(a) * r0, cy - math.cos(a) * r0), (cx + math.sin(a) * (r - 8), cy - math.cos(a) * (r - 8))],
                    fill=(200, 200, 210), width=5 if h_ % 3 == 0 else 3)
        ah = (hours % 12) / 12 * 2 * math.pi
        am = (hours % 1) * 2 * math.pi
        dr.line([(cx, cy), (cx + math.sin(ah) * 90, cy - math.cos(ah) * 90)], fill=(255, 255, 255), width=10)
        dr.line([(cx, cy), (cx + math.sin(am) * 135, cy - math.cos(am) * 135)], fill=(0, 140, 252), width=6)
        dr.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(255, 255, 255))
        dr.text((48, 500), "CLOCK IN", font=_f("medium", 34), fill=(150, 150, 160))
        dr.text((cw - 48, 500), "9:00 AM", font=_f("semibold", 34), fill=(255, 255, 255), anchor="ra")
        if k > 0.97:
            dr.text((48, 556), "CLOCK OUT", font=_f("medium", 34), fill=(150, 150, 160))
            dr.text((cw - 48, 556), "5:00 PM", font=_f("semibold", 34), fill=(255, 255, 255), anchor="ra")
        dr.text((48, 640), "Mon–Fri", font=_f("medium", 30), fill=(120, 120, 130))
        arr = np.asarray(im, np.float32)
        sc = 0.9 + 0.1 * ease_out_back(dt / 0.35, 1.6)
        arr = fx.resize_rgba(arr, sc)
        blend(frame, arr, d["cx"] - arr.shape[1] / 2, d["cy"] - arr.shape[0] / 2, clamp(dt / 0.15))


class Annot(El):
    """A hand-drawn style red circle that draws itself around a point (mistake marked on the chart)."""
    z = 70

    def draw(self, frame, t, ctx):
        d = self.d
        k = ease_out((t - self.t0) / 0.4, 2)
        if k <= 0:
            return
        r = d.get("r", 80)
        s = int(r * 2 + 40)
        im = Image.new("L", (s, s), 0)
        dr = ImageDraw.Draw(im)
        dr.arc((20, 20, s - 20, s - 20), -100, -100 + 380 * k, fill=255, width=d.get("width", 9))
        a = np.asarray(im, np.float32)
        out = np.zeros((s, s, 4), np.float32)
        out[..., :3] = d.get("rgb", (242, 54, 69))
        out[..., 3] = a
        blend(frame, out, d["x"] - s / 2, d["y"] - s / 2, 1.0)


TYPES = {"aurora": Aurora, "particles": Particles, "linechart": LineChart, "neural": Neural, "earnings": Earnings,
         "timecard": TimeCard, "annot": Annot}
