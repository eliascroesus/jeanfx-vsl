"""The thank-you video's graphics, v2: AB's beats with Iman Gadzhi's production value.

One system everywhere (Iman's): a dark set, one neon accent (money green; red for the one negative card), wide
all-caps type (Archivo Expanded, the free match for Monument Extended) blurring in word by word on the word, the key
word in the accent with a drawn underline, handwritten accent lines (Caveat), a dot grid fading out from a corner,
film grain, and everything moving: the set is a 3D money scene (ty_money_bg.py) that slowly pushes in, the text drifts
against it, icons float in glass tiles, screens sit in glowing frames with a 3D tilt.
"""
import functools, math, os, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import fx
from fx import W, H, blend, clamp, ease_out, ease_in_out, ease_out_back
from elements import El, asset
import ty_motion as tm

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
FACE = {"wide": "ArchivoExp-ExtraBold", "black": "ArchivoExp-Black", "semi": "ArchivoExp-SemiBold", "hand": "Caveat-Bold",
        "inter": None}
ACCENT = (62, 255, 142)
RED = (255, 48, 72)
BG_CLIP = "/home/user/work/gfx/ty/money_bg.mp4"
BG_LEN = 20.0


@functools.lru_cache(maxsize=64)
def font(face, size):
    if face == "inter":
        return fx.font("bold", size)
    return ImageFont.truetype(os.path.join(FONT_DIR, FACE[face] + ".ttf"), int(size))


@functools.lru_cache(maxsize=1024)
def text_rgba(text, face, size, rgb, track=0.0):
    """(RGBA float32, pad, ascent, ink width): the text with letter spacing, padded for blur and glow."""
    f = font(face, size)
    pad = int(size * 0.55) + 8
    xs = [f.getlength(text[:i + 1]) - f.getlength(ch) + track * i for i, ch in enumerate(text)]
    wink = f.getlength(text) + track * (len(text) - 1)
    asc, desc = f.getmetrics()
    w, h = int(wink) + 2 * pad + 4, asc + desc + 2 * pad
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for x, ch in zip(xs, text):
        d.text((pad + x, pad), ch, font=f, fill=255)
    a = np.asarray(im, np.float32)
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a
    return out, pad, asc, wink


@functools.lru_cache(maxsize=1024)
def glow_rgba(text, face, size, rgb, track, sigma):
    img, pad, asc, wink = text_rgba(text, face, size, rgb, track)
    g = img.copy()
    g[..., 3] = cv2.GaussianBlur(img[..., 3], (0, 0), sigma)
    return g


def _shadow(img, op=0.55, sigma=10):
    s = img.copy()
    s[..., :3] = 0
    s[..., 3] = cv2.GaussianBlur(img[..., 3], (0, 0), sigma) * op
    return s


# ------------------------------------------------------------------ the set
@functools.lru_cache(maxsize=1)
def _grain():
    r = np.random.default_rng(4)
    return [cv2.resize(r.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
            for _ in range(6)]


@functools.lru_cache(maxsize=1)
def _dots():
    """Iman's dot grid: small dots every 16 px."""
    a = np.zeros((H, W), np.float32)
    for y in range(8, H, 16):
        for x in range(8, W, 16):
            cv2.circle(a, (x, y), 1, 1.0, -1, cv2.LINE_AA)
    return a[..., None]


@functools.lru_cache(maxsize=16)
def _radial(cx, cy, rx, ry):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))[..., None]


class Scene(El):
    """The 3D money set behind a graphic: its own slice of the money clip, pushing in slowly, graded green or red,
    darkened where the text goes, an accent glow from one corner with the dot grid fading out of it, film grain."""
    z = 10

    def __init__(self, d):
        super().__init__(d)
        self.dec, self.next = None, None
        self.off = d.get("off", 0.0) % max(0.1, BG_LEN - (self.t1 - self.t0) - 0.2)

    def _read(self, t):
        k = int(round((t - self.t0) * 30))
        if self.dec is None or k != self.next:
            if self.dec:
                self.dec.kill()
            self.dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{self.off + k / 30:.3f}", "-i", BG_CLIP, "-f", "rawvideo",
                                         "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.next = k
        raw = self.dec.stdout.read(W * H * 3)
        self.next += 1
        if len(raw) < W * H * 3:
            return np.zeros((H, W, 3), np.float32)
        return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)

    def close(self):
        if self.dec:
            self.dec.kill()

    def draw(self, frame, t, ctx):
        d = self.d
        img = self._read(t)
        u = clamp((t - self.t0) / max(self.t1 - self.t0, 0.1))
        s = 1.0 + d.get("push", 0.06) * u                         # the camera keeps pushing in
        M = np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H * 0.45]])
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        if d.get("palette") == "red":
            lum = img.mean(2, keepdims=True)
            img = lum * np.array([1.55, 0.32, 0.38], np.float32) + img * 0.08
        cx, cy = d.get("text_at", (960, 500))
        img *= 1 - d.get("dark", 0.55) * _radial(cx, cy, 820, 420)
        gx, gy = d.get("glow", (1700, 120))
        gx += 60 * math.sin(t * 0.5)
        acc = np.array(RED if d.get("palette") == "red" else ACCENT, np.float32)
        gl = _radial(int(gx // 40 * 40), int(gy), 900, 620)
        img += gl * acc * d.get("glow_op", 0.22)
        img += _dots() * gl * 70 * d.get("dots", 1.0)
        img *= d.get("level", 0.85)
        img += _grain()[int(t * 24) % 6] * 5.0
        frame[:] = img


# ------------------------------------------------------------------ titles
class Title(El):
    """Wide caps, word by word on the word: each word blurs in (Iman's letters), sliding a few px from the right and
    settling from 106%. Accent words in neon green with a glow; `underline` draws a glowing line under the word;
    `count` runs a number up; `hand` lines are handwritten and write on left to right. A sheen sweeps across once
    everything's in, and the block drifts slowly up against the pushing set."""
    z = 84

    def __init__(self, d):
        super().__init__(d)
        self.lines = []
        for L in d["lines"]:
            face, size, track = L.get("face", "wide"), L["size"], L.get("track", 0)
            sp = font(face, size).getlength(" ") + track * 2
            items, x = [], 0.0
            for w in L["words"]:
                txt = w["w"] if not w.get("count") else w["count"][2] % w["count"][1]
                _, _, _, wink = text_rgba(txt, face, size, (255, 255, 255), track)
                items.append(dict(w, x=x, wink=wink))
                x += wink + sp
            total = x - sp
            x0 = L.get("x", d.get("x", 960)) - total / 2
            for it in items:
                it["x"] += x0
            self.lines.append(dict(L, face=face, size=size, track=track, items=items, x0=x0, x1=x0 + total))
        self.t_all = max(it["t"] for L in self.lines for it in L["items"])

    def draw(self, frame, t, ctx):
        d = self.d
        drift = -14 * clamp((t - self.t0) / max(self.t1 - self.t0, 0.1))
        sheen_t = t - (self.t_all + 0.45)
        if d.get("backdrop"):                         # a soft dark pool behind the block (over busy screens)
            ys = [L["y"] for L in self.lines]
            cy = (min(ys) + max(ys)) / 2 - 30
            rx = max(L["x1"] - L["x0"] for L in self.lines) * 0.62 + 120
            k = clamp((t - self.t0) / 0.3)
            frame *= 1 - 0.78 * k * _radial(960, int(cy), int(rx), int((max(ys) - min(ys)) / 2 + 170))
        for L in self.lines:
            face, size, track = L["face"], L["size"], L["track"]
            for it in L["items"]:
                dt = t - it["t"]
                if dt < 0:
                    continue
                acc = it.get("accent") or L.get("accent")
                rgb = tuple(L.get("rgb", (255, 255, 255))) if not acc else tuple(d.get("accent_rgb", ACCENT))
                txt = it["w"]
                if it.get("count"):
                    v0, v1, fmt = it["count"]
                    txt = fmt % round(v0 + (v1 - v0) * ease_out(dt / 0.8, 3))
                img, pad, asc, wink = text_rgba(txt, face, size, rgb, track)
                y = L["y"] + drift
                if face == "hand":                      # writes on, left to right
                    k = clamp(dt / max(0.05, 0.045 * len(txt)))
                    img = img.copy()
                    cut = int(pad + (wink + 10) * ease_in_out(k))
                    img[:, cut:, 3] *= 0
                    sh = _shadow(img, 0.6, 6)
                    blend(frame, sh, it["x"] - pad, y - pad - asc + 4, 1.0)
                    g = img.copy()
                    g[..., 3] = cv2.GaussianBlur(img[..., 3], (0, 0), size * 0.12)
                    blend(frame, g, it["x"] - pad, y - pad - asc, 0.55)
                    blend(frame, img, it["x"] - pad, y - pad - asc, 1.0)
                    continue
                k = ease_out(dt / 0.34, 3)
                blur = (1 - k) * 16
                op = clamp(k * 1.6)
                sc = 1 + 0.06 * (1 - k)
                dx = 26 * (1 - k)
                if sheen_t > 0 and sheen_t < 0.9:          # a light sheen sweeps across, left to right
                    sx = L["x0"] - 300 + (L["x1"] - L["x0"] + 600) * (sheen_t / 0.9)
                    cols = it["x"] - pad + np.arange(img.shape[1])
                    band = np.exp(-((cols - sx) / 110) ** 2)[None, :, None]
                    img = img.copy()
                    img[..., :3] = np.clip(img[..., :3] + band * 90, 0, 255)
                draw = img if blur < 0.6 else img.copy()
                if blur >= 0.6:
                    draw[..., 3] = cv2.GaussianBlur(img[..., 3], (0, 0), blur)
                if sc != 1:
                    draw = fx.resize_rgba(draw, sc)
                ox = it["x"] - pad + dx - (draw.shape[1] - img.shape[1]) / 2
                oy = y - pad - asc - (draw.shape[0] - img.shape[0]) / 2
                blend(frame, _shadow(draw, 0.65, size * 0.12), ox, oy + size * 0.06, op)
                g = glow_rgba(txt, face, size, rgb, track, size * 0.16)
                blend(frame, g, it["x"] - pad + dx, y - pad - asc, op * (0.75 if acc else 0.22))
                blend(frame, draw, ox, oy, op)
                if (it.get("underline") or L.get("underline")) and dt > 0.15:
                    ku = ease_out((dt - 0.15) / 0.4, 3)
                    th = max(4, int(size * 0.075))
                    x0, x1 = it["x"] - 4, it["x"] - 4 + (wink + 8) * ku
                    yy = y + size * 0.2 + drift * 0
                    bar = np.zeros((th * 8, int(wink + 40), 4), np.float32)
                    ucol = tuple(float(c) for c in d.get("accent_rgb", ACCENT))
                    cv2.rectangle(bar, (20, th * 4 - th // 2), (20 + int(x1 - x0), th * 4 + th // 2), (*ucol, 255.0), -1)
                    gb = bar.copy()
                    gb[..., 3] = cv2.GaussianBlur(bar[..., 3], (0, 0), th * 1.2)
                    blend(frame, gb, x0 - 20, yy - th * 4, 0.9)
                    blend(frame, bar, x0 - 20, yy - th * 4, 1.0)


# ------------------------------------------------------------------ icons in glass tiles
@functools.lru_cache(maxsize=16)
def glass_tile(size, rgb=ACCENT, radius=46):
    pad = 70
    S = size + 2 * pad
    out = np.zeros((S, S, 4), np.float32)
    fill = np.zeros((S, S), np.uint8)
    cv2.rectangle(fill, (pad, pad), (pad + size, pad + size), 255, -1)
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((pad, pad, pad + size, pad + size), radius, fill=255)
    body = np.asarray(m, np.float32)
    bd = Image.new("L", (S, S), 0)
    ImageDraw.Draw(bd).rounded_rectangle((pad, pad, pad + size, pad + size), radius, outline=255, width=3)
    border = np.asarray(bd, np.float32)
    yy = np.linspace(0, 1, S, dtype=np.float32)[:, None]
    glass = np.array([16, 30, 24], np.float32) * (1.25 - 0.5 * yy)[..., None]
    out[..., :3] = glass
    out[..., 3] = body * 0.78
    glow = cv2.GaussianBlur(border, (0, 0), 16)
    a_glow = glow * 0.9
    col = np.array(rgb, np.float32)
    # outer glow, then the glass, then the bright border
    res = np.zeros_like(out)
    res[..., :3] = col
    res[..., 3] = np.clip(a_glow, 0, 255)
    a1 = out[..., 3:4] / 255
    res[..., :3] = res[..., :3] * (1 - a1) + out[..., :3] * a1
    res[..., 3] = np.maximum(res[..., 3], out[..., 3])
    a2 = border[..., None] / 255
    res[..., :3] = res[..., :3] * (1 - a2) + col * a2
    res[..., 3] = np.maximum(res[..., 3], border)
    return res, pad


@functools.lru_cache(maxsize=16)
def icon_glow(icon, size, rgb):
    ic = tm.icon_rgba(icon, size).copy()
    ic[..., :3] = rgb
    g = ic.copy()
    g[..., 3] = cv2.GaussianBlur(ic[..., 3], (0, 0), size * 0.08)
    return ic, g


class IconTile(El):
    """A neon line icon in a dark glass tile with a glowing edge, label in wide caps under it. Pops in with an
    overshoot and a flash of glow, then floats."""
    z = 82

    def draw(self, frame, t, ctx):
        d = self.d
        size = d.get("size", 230)
        dt = t - self.t0
        sc = 0.55 + 0.45 * ease_out_back(dt / 0.42, 2.0)
        op = clamp(dt / 0.12)
        fl = 6 * math.sin((t - self.t0) * 2.1 + d.get("phase", 0))
        tile, pad = glass_tile(size)
        img = fx.resize_rgba(tile, sc)
        cx, cy = d["cx"], d["cy"] + fl
        blend(frame, _shadow(img, 0.6, 22), cx - img.shape[1] / 2, cy - img.shape[0] / 2 + 24, op)
        blend(frame, img, cx - img.shape[1] / 2, cy - img.shape[0] / 2, op)
        ic, g = icon_glow(d["icon"], int(size * 0.56), tuple(d.get("rgb", ACCENT)))
        flash = 1 + 1.5 * clamp(1 - dt / 0.5)
        gi = fx.resize_rgba(g, sc)
        ii = fx.resize_rgba(ic, sc)
        blend(frame, gi, cx - gi.shape[1] / 2, cy - gi.shape[0] / 2, min(1.0, op * 0.8 * flash))
        blend(frame, ii, cx - ii.shape[1] / 2, cy - ii.shape[0] / 2, op)
        if d.get("label"):
            img_l, padl, asc, wink = text_rgba(d["label"], "wide", d.get("label_size", 36), (255, 255, 255), 1.0)
            k = ease_out((dt - 0.12) / 0.3, 3)
            if k > 0:
                ly = cy + size * sc / 2 + 44 + 14 * (1 - k)
                blend(frame, img_l, cx - wink / 2 - padl, ly - padl - asc, k)


class Ripple(El):
    """Rings pulsing out of a point (the ringing phone)."""
    z = 81

    def draw(self, frame, t, ctx):
        d = self.d
        cx, cy, r0, tr = d["cx"], d["cy"], d.get("r0", 130), d.get("travel", 240)
        R = int(r0 + tr + 20)
        layer = np.zeros((2 * R + 20, 2 * R + 20), np.float32)
        for k in range(3):
            u = ((t - self.t0) / 1.1 + k / 3) % 1.0
            r = int(r0 + tr * ease_out(u, 2))
            cv2.circle(layer, (R + 10, R + 10), r, float((1 - u) ** 1.5), 3, cv2.LINE_AA)
        g = cv2.GaussianBlur(layer, (0, 0), 6) * 1.6 + layer
        rgba = np.zeros(layer.shape + (4,), np.float32)
        rgba[..., :3] = ACCENT
        rgba[..., 3] = np.clip(g * 255, 0, 255)
        blend(frame, rgba, cx - R - 10, cy - R - 10, clamp((t - self.t0) / 0.2))


# ------------------------------------------------------------------ screens in glowing frames
def _rot(ax, ay):
    cx, sx, cy, sy = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay)
    return np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def warp_card(frame, card, cx, cy, scale, ax, ay, op=1.0, f=1800.0):
    """Draw an RGBA card rotated in 3D (radians about x and y) and scaled, centred at (cx, cy)."""
    h, w = card.shape[:2]
    pts = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], np.float32) * scale
    p = pts @ _rot(ax, ay).T
    z = p[:, 2] + f
    q = np.stack([cx + p[:, 0] * f / z, cy + p[:, 1] * f / z], 1)
    x0, y0 = np.floor(q.min(0)).astype(int) - 2
    x1, y1 = np.ceil(q.max(0)).astype(int) + 2
    x0c, y0c, x1c, y1c = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if x1c - x0c < 2 or y1c - y0c < 2:
        return
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(q - [x0, y0]))
    out = cv2.warpPerspective(card, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    blend(frame, out[y0c - y0:y1c - y0, x0c - x0:x1c - x0], x0c, y0c, op)


@functools.lru_cache(maxsize=32)
def framed(name, width, blur=0.0, radius=28, rgb=ACCENT, border=4, glow=True):
    """A screenshot as a rounded card with a glowing accent edge (Iman's screen frames), padded for the glow."""
    im = Image.open(asset(name)).convert("RGB")
    s = width / im.width
    im = im.resize((width, max(1, round(im.height * s))), Image.LANCZOS)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    w, h = im.size
    pad = 60 if glow else 4
    out = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.float32)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    body = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    body[pad:pad + h, pad:pad + w] = np.asarray(m, np.float32)
    bd = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(bd).rounded_rectangle((pad - border // 2, pad - border // 2, pad + w + border // 2, pad + h + border // 2),
                                         radius + 2, outline=255, width=border)
    bdr = np.asarray(bd, np.float32)
    col = np.array(rgb, np.float32)
    if glow:
        g = cv2.GaussianBlur(bdr, (0, 0), 18) * 1.4
        out[..., :3] = col
        out[..., 3] = np.clip(g, 0, 255)
    rgb_img = np.zeros_like(out[..., :3])
    rgb_img[pad:pad + h, pad:pad + w] = np.asarray(im, np.float32)
    a = body[..., None] / 255
    out[..., :3] = out[..., :3] * (1 - a) + rgb_img * a
    out[..., 3] = np.maximum(out[..., 3], body)
    a2 = bdr[..., None] / 255
    out[..., :3] = out[..., :3] * (1 - a2) + col * a2
    out[..., 3] = np.maximum(out[..., 3], bdr)
    return out


class Screen(El):
    """A screen (the application page) in a glowing frame, flying up from small with a 3D tilt that settles to a
    slight angle, then a scan line sweeps down it ("reviewing your application") ticking each field."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        self.card = framed(d["img"], d.get("w", 1300), d.get("blur", 0.0), d.get("radius", 30))

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        k = ease_out(dt / d.get("dur", 0.75), 3)
        sc = d.get("s0", 0.2) + (1 - d.get("s0", 0.2)) * k
        ax = math.radians(d.get("ax0", 28) * (1 - k) + d.get("ax1", 6))
        ay = math.radians(d.get("ay0", -24) * (1 - k) + d.get("ay1", -5) + 1.2 * math.sin(dt * 0.9))
        card = self.card
        if d.get("scan") and dt > 0.8:
            card = card.copy()
            h = card.shape[0]
            pad = 60
            u = clamp((dt - 0.8) / d.get("scan_dur", 2.2))
            ys = int(pad + (h - 2 * pad) * u)
            band = np.zeros((h, card.shape[1], 1), np.float32)
            band[pad:h - pad, pad:card.shape[1] - pad, 0] = np.exp(-((np.arange(pad, h - pad) - ys) / 18.0) ** 2)[:, None]
            card[..., :3] = np.clip(card[..., :3] * (1 - 0.15 * band) + np.array(ACCENT) * 0.85 * band, 0, 255)
            for fy in d.get("checks", []):                         # a tick lands as the scan passes each field
                yy = int(pad + (h - 2 * pad) * fy)
                if ys > yy:
                    kk = ease_out_back((ys - yy) / 60.0, 2)
                    r = int(26 * min(kk, 1.3))
                    xx = card.shape[1] - pad - 70
                    cv2.circle(card, (xx, yy), r, (*ACCENT, 255.0), -1, cv2.LINE_AA)
                    if r > 10:
                        cv2.polylines(card, [np.int32([[xx - 11, yy], [xx - 3, yy + 9], [xx + 12, yy - 9]])], False,
                                      (10, 30, 18, 255.0), 5, cv2.LINE_AA)
        sh = _shadow(card, 0.7, 30)
        warp_card(frame, sh, d["cx"], d["cy"] + 40 * sc, sc, ax, ay, clamp(dt / 0.1))
        warp_card(frame, card, d["cx"], d["cy"], sc, ax, ay, clamp(dt / 0.1))


class Carousel3D(El):
    """Discord posts in three depths sliding left at different speeds (parallax): small dim ones far back, the
    biggest close up and fastest; each in a glowing frame, with motion blur."""
    z = 40

    def __init__(self, d):
        super().__init__(d)
        r = np.random.default_rng(d.get("seed", 3))
        self.cards = []
        rows = [("far", 0.52, 140, 0.55, 3.0, 300), ("mid", 0.78, 250, 0.8, 0.0, 560), ("near", 1.0, 380, 1.0, 0.0, 640)]
        imgs = list(d["imgs"])
        k = 0
        for name, s, v, light, blur, y in rows:
            n = {"far": 6, "mid": 4, "near": 3}[name]
            x = r.uniform(-200, 100)
            for _ in range(n):
                card = framed(imgs[k % len(imgs)], int(d.get("w", 520) * s), blur, 18, ACCENT, 3, name != "far").copy()
                card[..., :3] *= light
                self.cards.append(dict(card=card, x=x, y=y + r.uniform(-50, 50), v=v, depth=name))
                x += card.shape[1] + r.uniform(40, 160) * s
                k += 1

    def draw(self, frame, t, ctx):
        dt = t - self.t0
        op = clamp(dt / 0.2)
        for c in self.cards:                                      # far first
            img = c["card"]
            x = c["x"] - c["v"] * dt + 120
            if x > W + 50 or x + img.shape[1] < -50:
                continue
            b = int(c["v"] / 70)
            if b > 1:
                img = cv2.blur(img, (b * 2 + 1, 1))
            if c["depth"] == "near":
                blend(frame, _shadow(img, 0.6, 24), x, c["y"] - img.shape[0] / 2 + 30, op)
            blend(frame, img, x, c["y"] - img.shape[0] / 2, op)


class Wall3D(El):
    """The testimonial wall, tilted back like a floor going away from us, scrolling up, fading into the dark at the
    top, with the accent glow under it."""
    z = 15

    def __init__(self, d):
        super().__init__(d)
        self.wall = tm.WallUp(dict(d, type="wallup"))

    def draw(self, frame, t, ctx):
        d = self.d
        wl = self.wall
        u = clamp((t - self.t0) / max(self.t1 - self.t0, 0.1))
        start, end = d.get("y_start", 700), d.get("y_end", -(wl.used - 900))
        y0 = int(start + (end - start) * u)
        full = np.zeros((H, W, 4), np.float32)
        a_l, b_l = max(0, -y0), min(wl.used, H - y0)
        if b_l > a_l:
            full[y0 + a_l:y0 + b_l] = wl.layer[a_l:b_l]
        tilt = d.get("tilt", 0.2)
        src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
        dst = np.float32([[W * tilt, 40], [W * (1 - tilt), 40], [W + 140, H + 40], [-140, H + 40]])
        out = cv2.warpPerspective(full, cv2.getPerspectiveTransform(src, dst), (W, H), flags=cv2.INTER_LINEAR)
        fade = np.clip((np.linspace(0, 1, H, dtype=np.float32) - 0.04) / 0.42, 0, 1)[:, None]
        out[..., 3] *= fade * 0.95
        blend(frame, out, 0, 0, 1.0)


class GuruFlash(El):
    """The guru thumbnails slamming in one after another: each lands from 118% with a tilt, an RGB-split glitch and a
    white flash, in a thin white frame."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        self.imgs = [framed(n, d.get("w", 1180), 0.0, 14, (255, 255, 255), 3, False) for n in d["imgs"]]

    def draw(self, frame, t, ctx):
        d = self.d
        each = d.get("each", 0.3)
        k = min(len(self.imgs) - 1, int((t - self.t0) / each))
        tin = t - self.t0 - k * each
        img = self.imgs[k]
        u = ease_out(tin / 0.18, 3)
        sc = 1.18 - 0.18 * u
        rot = (-5 if k % 2 else 4) * (1 - u) + (-1.5 if k % 2 else 1.5)
        im = fx.resize_rgba(img, sc)
        if rot:
            Mr = cv2.getRotationMatrix2D((im.shape[1] / 2, im.shape[0] / 2), rot, 1.0)
            im = cv2.warpAffine(im, Mr, (im.shape[1], im.shape[0]), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        split = int(16 * (1 - u))
        cx, cy = d.get("cx", 960), d.get("cy", 500)
        blend(frame, _shadow(im, 0.7, 26), cx - im.shape[1] / 2, cy - im.shape[0] / 2 + 26, 1.0)
        if split > 1:
            r_ = im.copy(); r_[..., 1:3] = 0
            b_ = im.copy(); b_[..., 0:2] = 0
            blend(frame, r_, cx - im.shape[1] / 2 - split, cy - im.shape[0] / 2, 0.6)
            blend(frame, b_, cx - im.shape[1] / 2 + split, cy - im.shape[0] / 2, 0.6)
        blend(frame, im, cx - im.shape[1] / 2, cy - im.shape[0] / 2, 1.0)
        fl = clamp(1 - tin / 0.12) * 0.35
        if fl > 0:
            frame[:] = frame + (255 - frame) * fl


class NeonLine(El):
    """A chart line crashing down the frame, drawing itself, neon with a wide glow and a spark at its head."""
    z = 30
    PTS = [(-40, 150), (300, 250), (420, 200), (640, 470), (760, 410), (1060, 700), (1200, 640), (1500, 900), (1980, 1060)]

    def draw(self, frame, t, ctx):
        d = self.d
        u = clamp((t - self.t0) / d.get("dur", 1.3))
        pts = [tuple(p) for p in d.get("pts", self.PTS)]
        segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        Lt = sum(segs) * ease_out(u, 2)
        out, acc = [pts[0]], 0
        for (a, b), sl in zip(zip(pts, pts[1:]), segs):
            if acc + sl <= Lt:
                out.append(b)
                acc += sl
            else:
                f = (Lt - acc) / sl
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                break
        if len(out) < 2:
            return
        small = np.zeros((H // 2, W // 2), np.float32)
        cv2.polylines(small, [np.int32(np.array(out) / 2)], False, 1.0, 4, cv2.LINE_AA)
        hx, hy = out[-1]
        cv2.circle(small, (int(hx / 2), int(hy / 2)), 7, 1.0, -1, cv2.LINE_AA)
        wide = cv2.GaussianBlur(small, (0, 0), 22) * 2.2 + cv2.GaussianBlur(small, (0, 0), 6) * 1.2
        line = cv2.resize(small, (W, H))[..., None]
        glow = cv2.resize(wide, (W, H))[..., None]
        col = np.array(d.get("rgb", RED), np.float32)
        op = d.get("op", 1.0) * clamp((self.t1 - t) / 0.15)
        frame[:] = frame + glow * col * 0.9 * op
        line = line * op
        frame[:] = frame * (1 - line) + ((col * 0.35 + 255 * 0.65) * 0.9 + col * 0.1) * line


class FrameShot(El):
    """His shot shrinking into a rounded card with a glowing edge and sliding up off the top (AB's move, Iman's frame)."""
    z = 70

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        k1 = ease_in_out(dt / d.get("shrink", 0.6))
        k2 = ease_in_out((dt - d.get("shrink", 0.6) - d.get("hold", 0.6)) / d.get("slide", 0.7))
        sc = 1 - (1 - d.get("scale", 0.56)) * k1
        cy = 540 - (540 - d.get("cy", 470)) * k1 - (d.get("cy", 470) + 720) * k2
        shot = ctx["shot"]
        w, h = int(W * sc), int(H * sc)
        small = cv2.resize(shot, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
        rad = int(34 * k1)
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), rad, fill=255)
        rgba = np.dstack([small, np.asarray(m, np.float32)])
        if k1 > 0.02:
            pad = 60
            bd = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
            ImageDraw.Draw(bd).rounded_rectangle((pad - 2, pad - 2, pad + w + 1, pad + h + 1), rad + 2, outline=255, width=4)
            b = np.asarray(bd, np.float32)
            g = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.float32)
            g[..., :3] = ACCENT
            g[..., 3] = np.clip(cv2.GaussianBlur(b, (0, 0), 18) * 1.4 + b, 0, 255) * k1
            blend(frame, _shadow(g, 0.8, 30), 960 - w / 2 - pad, cy - h / 2 - pad + 30, 1)
            blend(frame, g, 960 - w / 2 - pad, cy - h / 2 - pad, 1)
        blend(frame, rgba, 960 - w / 2, cy - h / 2, 1)


TYPES = {"scene": Scene, "title": Title, "icontile": IconTile, "ripple": Ripple, "screen": Screen, "carousel3d": Carousel3D,
         "wall3d": Wall3D, "guruflash": GuruFlash, "neonline": NeonLine, "frameshot": FrameShot}
