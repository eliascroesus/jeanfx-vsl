"""Money: the $100-bill texture, AB's falling-money drop (bills tumbling in 3D with motion blur and depth blur), the
money-pile B-roll, and a burning bill. Bills are drawn from scratch (a stylised $100: pale green paper, big "100"s,
the blue security ribbon, the copper bell), so nothing is licensed."""
import functools, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = "/usr/share/fonts/opentype/inter"
BW, BH = 1200, 510          # bill texture size (real ratio 2.35)


def _font(n, s):
    return ImageFont.truetype(f"{FD}/{n}", s)


@functools.lru_cache(maxsize=4)
def bill(side="front", seed=0, gen_path=None):
    """RGBA bill texture. If a generated photo of a bill exists (gen_path), that's used instead."""
    if gen_path:
        try:
            im = Image.open(gen_path).convert("RGBA").resize((BW, BH), Image.LANCZOS)
            return np.asarray(im)
        except OSError:
            pass
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    base = np.array([214, 220, 200], np.float32) if side == "front" else np.array([196, 214, 188], np.float32)
    paper = base + 10 * np.sin(xx / 37 + yy / 53)[..., None] + r.normal(0, 3, (BH, BW, 1))
    # fine guilloche lines
    g = (np.sin(xx / 3.1 + 6 * np.sin(yy / 41)) * np.sin(yy / 2.7 + 5 * np.sin(xx / 63))) > 0.6
    paper[g] -= 18
    im = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)
    ink = (52, 78, 64) if side == "front" else (40, 96, 60)
    d.rectangle((14, 14, BW - 15, BH - 15), outline=ink, width=6)
    d.rectangle((30, 30, BW - 31, BH - 31), outline=ink, width=2)
    f_big, f_mid = _font("InterDisplay-Black.otf", 120), _font("InterDisplay-Bold.otf", 46)
    if side == "front":
        # portrait oval
        d.ellipse((BW * 0.36, 70, BW * 0.64, BH - 70), fill=(180, 186, 168), outline=ink, width=5)
        for k in range(0, 160, 9):
            d.ellipse((BW * 0.36 + k * 0.4, 70 + k * 0.6, BW * 0.64 - k * 0.4, BH - 70 - k * 0.6), outline=(150, 160, 140), width=1)
        d.ellipse((BW * 0.43, 140, BW * 0.57, 300), fill=(120, 132, 116))
        d.chord((BW * 0.39, 290, BW * 0.61, 520), 180, 360, fill=(110, 122, 108))
        # blue ribbon
        d.rectangle((BW * 0.30, 0, BW * 0.33, BH), fill=(40, 90, 200))
        for y in range(10, BH, 34):
            d.text((BW * 0.302, y), "100", font=_font("InterDisplay-Bold.otf", 16), fill=(220, 160, 60))
        # copper bell + 100
        d.text((BW * 0.70, BH * 0.52), "100", font=f_big, fill=(170, 110, 60))
        d.ellipse((BW * 0.71, BH * 0.18, BW * 0.79, BH * 0.42), fill=(176, 120, 70))
        d.text((44, 34), "100", font=f_mid, fill=ink)
        d.text((44, BH - 92), "100", font=f_mid, fill=ink)
        d.text((BW * 0.67, 40), "THE UNITED STATES OF AMERICA", font=_font("InterDisplay-Bold.otf", 22), fill=ink)
        d.text((BW * 0.06, BH * 0.4), "FEDERAL RESERVE NOTE", font=_font("InterDisplay-SemiBold.otf", 20), fill=ink)
        d.text((BW * 0.08, BH * 0.62), "LD 86409912 E", font=_font("InterDisplay-Medium.otf", 26), fill=(40, 110, 70))
    else:
        d.rectangle((BW * 0.3, 80, BW * 0.7, BH - 80), fill=(170, 196, 168), outline=ink, width=4)
        d.text((BW * 0.39, BH * 0.30), "ONE HUNDRED", font=_font("InterDisplay-Bold.otf", 44), fill=ink)
        d.text((44, 34), "100", font=f_mid, fill=ink)
        d.text((BW - 140, BH - 92), "100", font=f_mid, fill=ink)
        d.text((BW * 0.72, BH * 0.36), "100", font=f_big, fill=(60, 110, 70))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    a = np.dstack([np.asarray(im), np.full((BH, BW), 255, np.uint8)])
    return a


class Bill:
    def __init__(self, r, t0, spread=1.0, near=False, region=(0, 1920), early=False):
        self.t0 = t0 + (0.0 if early else r.uniform(0, 0.5))
        self.x = r.uniform(region[0] - 200, region[1] + 200)
        self.y = r.uniform(-900, -150) if not early else r.uniform(-500, 950)
        self.z = r.uniform(0.35, 0.9) if not near else r.uniform(1.4, 2.6)   # scale-ish depth
        self.vy = r.uniform(900, 1700) * (1.3 if near else 1.0)
        self.vx = r.uniform(-180, 180)
        self.ax, self.ay, self.az = r.uniform(0, 6.28, 3)
        self.wx, self.wy, self.wz = r.uniform(-7, 7), r.uniform(-9, 9), r.uniform(-3, 3)
        self.side = "front" if r.uniform() < 0.6 else "back"

    def corners(self, t):
        dt = t - self.t0
        x, y = self.x + self.vx * dt, self.y + self.vy * dt + 120 * dt * dt
        ax, ay, az = self.ax + self.wx * dt, self.ay + self.wy * dt, self.az + self.wz * dt
        hw, hh = 0.5 * 420 * self.z, 0.5 * 178 * self.z
        pts = np.array([[-hw, -hh, 0], [hw, -hh, 0], [hw, hh, 0], [-hw, hh, 0]], np.float32)
        cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        p = pts @ (Rz @ Ry @ Rx).T
        f = 900.0
        z = p[:, 2] + f
        return np.stack([x + p[:, 0] * f / z, y + p[:, 1] * f / z], 1), math.cos(ay) * math.cos(ax)


class MoneyDrop:
    """Bills falling and tumbling past the camera (AB's money drop). n bills over [t0, t1]; some huge, blurred ones in
    front (near=True layer drawn last)."""

    def __init__(self, t0, t1, n=26, seed=3, near_n=5, region=(0, 1920), gen_paths=None, rate=0.55):
        r = np.random.default_rng(seed)
        self.t0, self.t1 = t0, t1
        gp = gen_paths or {}
        self.tex = {s: bill(s, 0, gp.get(s)) for s in ("front", "back")}
        span = max(t1 - t0 - 0.6, 0.2)
        self.far = [Bill(r, t0 + span * rate * i / max(n, 1), near=False, region=region, early=i < n // 3) for i in range(n)]
        self.near = [Bill(r, t0 + span * rate * i / max(near_n, 1), near=True, region=region) for i in range(near_n)]

    def _draw(self, frame, b, t, blur):
        src = np.float32([[0, 0], [1199, 0], [1199, 509], [0, 509]])
        q0, facing = b.corners(t)
        if q0[:, 1].min() > 1180 or q0[:, 1].max() < -100 or q0[:, 0].min() > 2100 or q0[:, 0].max() < -180:
            return
        tex = self.tex[b.side if facing >= 0 else ("back" if b.side == "front" else "front")]
        x0, y0 = np.floor(q0.min(0)).astype(int) - 40
        x1, y1 = np.ceil(q0.max(0)).astype(int) + 40
        x0, y0 = max(x0, -60), max(y0, -60)
        x1, y1 = min(x1, 1980), min(y1, 1140)
        if x1 - x0 < 4 or y1 - y0 < 4:
            return
        acc = None
        n_sub = 3
        for k in range(n_sub):                      # motion blur: average 3 sub-frame positions
            q, _ = b.corners(t - k * 0.011)
            M = cv2.getPerspectiveTransform(src, np.float32(q - [x0, y0]))
            w = cv2.warpPerspective(tex, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.float32)
            acc = w if acc is None else acc + w
        acc /= n_sub
        shade = 0.72 + 0.28 * abs(facing)
        acc[..., :3] *= shade
        if blur > 0.5:
            k = int(blur) * 2 + 1
            acc = cv2.GaussianBlur(acc, (k, k), blur)
        from fx import blend
        blend(frame, acc, x0, y0, 1.0)

    def draw(self, frame, t, layer="all"):
        if not (self.t0 <= t < self.t1):
            return
        if layer in ("all", "far"):
            for b in self.far:
                if t >= b.t0:
                    self._draw(frame, b, t, 2.5 * (1 - b.z))
        if layer in ("all", "near"):
            for b in self.near:
                if t >= b.t0:
                    self._draw(frame, b, t, 9 + 4 * b.z)


@functools.lru_cache(maxsize=2)
def money_pile(seed=5, gen_path=None):
    """A big texture of overlapping $100 bills for the money B-roll (camera moves over it)."""
    if gen_path:
        try:
            return np.asarray(Image.open(gen_path).convert("RGB").resize((3200, 2000), Image.LANCZOS), np.float32)
        except OSError:
            pass
    r = np.random.default_rng(seed)
    Wp, Hp = 3200, 2000
    canvas = np.full((Hp, Wp, 3), (120, 130, 110), np.float32)
    tex = {s: bill(s) for s in ("front", "back")}
    for i in range(170):
        s = r.uniform(0.75, 1.15)
        ang = r.uniform(-40, 40) + (90 if r.uniform() < 0.15 else 0)
        cx, cy = r.uniform(-200, Wp + 200), r.uniform(-200, Hp + 200)
        M = cv2.getRotationMatrix2D((600, 255), ang, s)
        M[:, 2] += [cx - 600, cy - 255]
        t = tex["front" if r.uniform() < 0.7 else "back"]
        w = cv2.warpAffine(t, M, (Wp, Hp), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0)).astype(np.float32)
        a = w[..., 3:4] / 255
        # soft shadow under each bill
        sh = cv2.GaussianBlur(a, (31, 31), 10)
        if sh.ndim == 2:
            sh = sh[..., None]
        canvas *= 1 - 0.25 * np.roll(sh, (10, 10), (0, 1))
        light = 0.85 + 0.3 * r.uniform()
        canvas = canvas * (1 - a) + w[..., :3] * light * a
    # warm light falloff
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    g = 0.65 + 0.45 * np.exp(-(((xx - Wp * 0.45) / (Wp * 0.5)) ** 2 + ((yy - Hp * 0.4) / (Hp * 0.6)) ** 2))
    canvas *= g[..., None]
    canvas *= np.array([1.05, 1.0, 0.9])
    return np.clip(canvas, 0, 255)


class MoneyBroll:
    """Close-up money footage stand-in: the camera glides low over the pile with depth of field, with a quick whip-pan
    at the start like AB's handheld stock clip."""

    def __init__(self, t0, t1, seed=5, gen_path=None, darken=0.0, blur=0.0, whip=True):
        self.t0, self.t1, self.darken, self.blur, self.whip = t0, t1, darken, blur, whip
        self.pile = money_pile(seed, gen_path)
        r = np.random.default_rng(seed)
        self.p0 = np.array([r.uniform(900, 1300), r.uniform(700, 900)])
        self.v = np.array([r.uniform(-60, 60), r.uniform(-30, 30)])

    def draw(self, frame, t):
        dt = t - self.t0
        Hp, Wp = self.pile.shape[:2]
        whip = 0.0
        if self.whip and dt < 0.25:
            whip = (1 - dt / 0.25) ** 2 * 900
        c = self.p0 + self.v * dt + [whip, 0]
        z = 1.25 + 0.06 * dt
        # perspective: looking across the pile (top of frame further away)
        src_w, src_h = 1920 / z, 1080 / z
        x0, y0 = c[0] - src_w / 2, c[1] - src_h / 2
        src = np.float32([[x0 + src_w * 0.12, y0], [x0 + src_w * 0.88, y0], [x0 + src_w, y0 + src_h], [x0, y0 + src_h]])
        dst = np.float32([[0, 0], [1920, 0], [1920, 1080], [0, 1080]])
        M = cv2.getPerspectiveTransform(src, dst)
        img = cv2.warpPerspective(self.pile, M, (1920, 1080), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # depth of field: far (top) and very near (bottom) soft
        small = cv2.GaussianBlur(img, (0, 0), 7 + self.blur)
        yy = np.linspace(0, 1, 1080)[:, None, None]
        focus = np.clip(1 - np.abs(yy - 0.58) / 0.28, 0, 1)
        img = img * focus + small * (1 - focus)
        if whip > 1:
            k = int(min(whip / 6, 80)) * 2 + 1
            img = cv2.blur(img, (k, 1))
        if self.blur > 0:
            img = cv2.GaussianBlur(img, (0, 0), self.blur)
        frame[:] = img * (1 - self.darken)


def fire_frame(t, w=520, h=760, seed=2):
    """Procedural flames (rising turbulent noise through a black-red-orange-yellow ramp), RGBA."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h // 4, 0:w // 4].astype(np.float32)
    n = np.zeros_like(xx)
    for k, (fx_, fy, sp, amp) in enumerate([(0.09, 0.07, 3.2, 1.0), (0.18, 0.15, 5.0, 0.55), (0.37, 0.31, 7.5, 0.3)]):
        ph = r.uniform(0, 6.28, 2)
        n += amp * np.sin(xx * fx_ + ph[0] + np.sin(yy * fy * 1.7 + t * sp) * 1.4) * np.sin(yy * fy + t * sp + ph[1])
    hgt = 1 - yy / (h // 4)                    # stronger at the bottom
    cx = 1 - np.abs(xx / (w // 4) - 0.5) * 2
    v = np.clip(0.55 * hgt + 0.35 * cx + 0.35 * n - 0.25, 0, 1)
    v = cv2.resize(v, (w, h), interpolation=cv2.INTER_CUBIC)
    v = cv2.GaussianBlur(v, (0, 0), 3)
    col = np.stack([np.clip(v * 3, 0, 1) * 255, np.clip(v * 2 - 0.5, 0, 1) * 230, np.clip(v * 3 - 2, 0, 1) * 160], -1)
    a = np.clip(v * 2.2, 0, 1) * 255
    return np.dstack([col, a]).astype(np.float32)
