"""Drawing primitives for the AB-style edit: alpha blending, easing, AB's text (per-letter blur-in reveal, soft
shadow, glow), and image caching. Everything works on float32 RGB frames (1920x1080, 0-255)."""
import functools, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
FONT_DIR = "/usr/share/fonts/opentype/inter"
FONTS = {"medium": "InterDisplay-Medium.otf", "regular": "InterDisplay-Regular.otf", "semibold": "InterDisplay-SemiBold.otf",
         "bold": "InterDisplay-Bold.otf", "black": "InterDisplay-Black.otf", "xbold": "InterDisplay-ExtraBold.otf"}
BLUE = (0, 140, 252)          # AB's blue, measured (#008CFC)
GLOW_BLUE = (150, 214, 255)   # the light blue of his glowing caps


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(x, p=3):
    return 1 - (1 - clamp(x)) ** p


def ease_in_out(x):
    x = clamp(x)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out_back(x, s=1.5):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def blend(dst, src, x, y, opacity=1.0):
    """Alpha-composite an RGBA uint8/float array onto a float32 RGB frame at integer (x, y)."""
    if opacity <= 0.003:
        return
    h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4].astype(np.float32) * (opacity / 255.0)
    d = dst[y0:y1, x0:x1]
    d *= 1 - a
    d += s[..., :3].astype(np.float32) * a


def font(kind, size):
    return _font(kind, int(round(size)))


@functools.lru_cache(maxsize=256)
def _font(kind, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[kind]), size)


BLUR_LEVELS = (0, 1.5, 3, 5, 8, 12, 18)


@functools.lru_cache(maxsize=20000)
def glyph(kind, size, ch, rgb, blur_i=0, shadow=False):
    """One letter as an RGBA array plus its top-left offset relative to the pen position on the baseline."""
    f = font(kind, size)
    pad = int(size * 0.35) + 40
    asc, desc = f.getmetrics()
    w = int(f.getlength(ch)) + 2 * pad
    h = asc + desc + 2 * pad
    m = Image.new("L", (max(w, 1), h), 0)
    ImageDraw.Draw(m).text((pad, pad), ch, font=f, fill=255)
    b = BLUR_LEVELS[blur_i]
    if shadow:
        m = m.filter(ImageFilter.GaussianBlur(max(size * 0.07, 4) + b))
    elif b:
        m = m.filter(ImageFilter.GaussianBlur(b))
    a = np.asarray(m, np.uint8)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = a
    return rgba, -pad, -pad - asc


def advances(kind, size, text, track):
    """x of each letter's pen position (with kerning from the font), letter spacing in px added between letters."""
    f = font(kind, size)
    xs = []
    for i in range(len(text)):
        xs.append(f.getlength(text[:i]) + track * i)
    total = f.getlength(text) + track * (len(text) - 1)
    return xs, total


def text_width(kind, size, text, track):
    return advances(kind, size, text, track)[1]


def fit_size(kind, size, text, track, max_w):
    w = text_width(kind, size, text, track)
    return size if w <= max_w else size * max_w / w


class Line:
    """One line of text in AB's style.

    kind/size/track: font, px size, letter spacing; rgb: colour; (x, y): anchor on the baseline, align left/center/right;
    t_in: when it appears; reveal: "blur" (AB's letters coming in left to right, blurred and spread), "type"
    (typewriter), "cut" (just there), "pop" (whole line scales in); shadow: soft dark drop shadow; glow: (rgb, radius).
    """

    def __init__(self, text, kind, size, rgb, x, y, t_in, t_out, align="left", track=-4, reveal="blur",
                 shadow=None, glow=None, reveal_dur=0.15, type_cps=None, fade_out=0.0, dy_in=0.0, alpha=1.0):
        self.text, self.kind, self.size, self.rgb = text, kind, size, tuple(int(c) for c in rgb)
        self.t_in, self.t_out, self.reveal = t_in, t_out, reveal
        self.shadow, self.glow, self.track = shadow, glow, track
        self.xs, self.w = advances(kind, size, text, track)
        x0 = x if align == "left" else x - self.w / 2 if align == "center" else x - self.w
        self.x0, self.y = x0, y
        self.reveal_dur, self.type_cps, self.fade_out, self.dy_in, self.alpha = reveal_dur, type_cps, fade_out, dy_in, alpha
        self.n = max(1, sum(1 for c in text if c != " "))

    def letter_state(self, i, t):
        """(opacity, blur px, dx) for letter i at time t."""
        dt = t - self.t_in
        if self.reveal == "cut":
            return 1.0, 0.0, 0.0
        if self.reveal == "type":
            cps = self.type_cps or 28
            return (1.0 if dt >= i / cps else 0.0), 0.0, 0.0
        if self.reveal == "fade":
            return ease_out(dt / 0.25), 0.0, 0.0
        # blur: letters start staggered left to right over ~60% of the reveal; each takes ~0.16 s
        st = (self.reveal_dur * 0.55) * (i / max(len(self.text) - 1, 1))
        k = ease_out((dt - st) / max(self.reveal_dur * 0.62, 0.05), 3)
        spread = (1 - k) * self.size * 0.55 * (0.25 + i / max(len(self.text), 1))
        return clamp(k * 1.4), (1 - k) * 12.0, spread

    def draw(self, frame, t):
        if t < self.t_in or t >= self.t_out:
            return
        op_all = self.alpha
        if self.fade_out > 0:
            op_all *= clamp((self.t_out - t) / self.fade_out)
        dy = self.dy_in * (1 - ease_out((t - self.t_in) / 0.3)) if self.dy_in else 0.0
        size = int(round(self.size))
        for pass_ in ("glow", "shadow", "text"):
            if pass_ == "glow" and not self.glow:
                continue
            if pass_ == "shadow" and not self.shadow:
                continue
            for i, ch in enumerate(self.text):
                if ch == " ":
                    continue
                op, bl, dx = self.letter_state(i, t)
                if op <= 0.01:
                    continue
                bi = min(range(len(BLUR_LEVELS)), key=lambda j: abs(BLUR_LEVELS[j] - bl))
                if pass_ == "text":
                    g, ox, oy = glyph(self.kind, size, ch, self.rgb, bi)
                    blend(frame, g, self.x0 + self.xs[i] + dx + ox, self.y + dy + oy, op * op_all)
                elif pass_ == "shadow":
                    sop, soff = self.shadow if isinstance(self.shadow, tuple) else (0.55, 4)
                    g, ox, oy = glyph(self.kind, size, ch, (0, 0, 0), bi, True)
                    blend(frame, g, self.x0 + self.xs[i] + dx + ox, self.y + dy + oy + soff, op * op_all * sop)
                else:
                    grgb, gop = self.glow
                    g, ox, oy = glyph(self.kind, size, ch, grgb, 5)
                    blend(frame, g, self.x0 + self.xs[i] + dx + ox, self.y + dy + oy, op * op_all * gop)
                    g, ox, oy = glyph(self.kind, size, ch, grgb, 6)
                    blend(frame, g, self.x0 + self.xs[i] + dx + ox, self.y + dy + oy, op * op_all * gop)


@functools.lru_cache(maxsize=512)
def load_rgba(path, max_w=None, max_h=None):
    im = Image.open(path).convert("RGBA")
    if max_w or max_h:
        s = min((max_w or 1e9) / im.width, (max_h or 1e9) / im.height)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    return np.asarray(im)


def resize_rgba(arr, s):
    if abs(s - 1) < 1e-3:
        return arr
    h, w = arr.shape[:2]
    import cv2
    nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
    return cv2.resize(arr, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)


def gradient(kind, strength=1.0):
    """AB's fades as RGBA full frames: 'bottom' (dark fade behind captions), 'left'/'right' dark side fades for side
    text on a dark shot, 'left_white'/'right_white' for a bright shot."""
    return _gradient(kind, round(strength, 3))


@functools.lru_cache(maxsize=32)
def _gradient(kind, strength):
    a = np.zeros((H, W), np.float32)
    if kind == "bottom":
        y = np.arange(H) / H
        r = np.clip((y - 0.55) / 0.45, 0, 1)
        a[:] = ((r * r * (3 - 2 * r)) * 0.62)[:, None]
        rgb = (0, 0, 0)
    else:
        x = np.arange(W) / W
        d = x if kind.startswith("left") else 1 - x
        r = np.clip(1 - d / 0.58, 0, 1)
        a[:] = (r * r * (3 - 2 * r)) * (0.93 if "white" in kind else 0.80)
        rgb = (255, 255, 255) if "white" in kind else (6, 6, 8)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.clip(a * strength * 255, 0, 255).astype(np.uint8)
    return out


def rounded_card(img, radius=26, border=0, border_rgb=(255, 255, 255), shadow=0.0, shadow_blur=24, shadow_dy=12):
    """PIL image -> RGBA array with rounded corners, an optional solid border and a soft drop shadow."""
    img = img.convert("RGBA")
    w, h = img.width + 2 * border, img.height + 2 * border
    card = Image.new("RGBA", (w, h), border_rgb + (255,))
    card.alpha_composite(img, (border, border))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    card.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(card.split()[3]))))
    if shadow <= 0:
        return np.asarray(card)
    pad = shadow_blur * 3
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("L", out.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + shadow_dy, pad + w, pad + h + shadow_dy), radius, fill=int(255 * shadow))
    out.putalpha(sh.filter(ImageFilter.GaussianBlur(shadow_blur)))
    out.alpha_composite(card, (pad, pad))
    return np.asarray(out)


def warp_rgba(arr, M, size):
    import cv2
    return cv2.warpPerspective(arr, M, size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
