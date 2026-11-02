"""Elements for the thank-you video, copied from AB's thank-you (thank-you-vsl-reference/BREAKDOWN.md): green and red
gradient cards, light-leak flashes, white line icons (in dashed circles or on their own), a sliding row of testimonial
screenshots, the application card zooming in, the shot shrinking into a card and sliding up over a scrolling testimonial
wall, a falling chart line, and "guru" thumbnails."""
import functools, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

import fx
from fx import W, H, blend, clamp, ease_out, ease_out_back, ease_in_out
from elements import El, asset

STOPS = {   # vertical gradient stops measured on AB's frames: (position 0..1 from the top, rgb)
    "green": [(0.0, (22, 129, 46)), (0.33, (15, 87, 30)), (0.5, (11, 67, 25)), (0.75, (5, 34, 12)), (1.0, (1, 3, 0))],
    "red": [(0.0, (237, 13, 49)), (0.28, (174, 10, 34)), (0.5, (118, 6, 23)), (0.75, (60, 4, 12)), (1.0, (3, 1, 2))],
}


@functools.lru_cache(maxsize=4)
def gradient_plate(palette):
    st = STOPS[palette]
    y = np.linspace(0, 1, H)
    col = np.zeros((H, 3), np.float32)
    for c in range(3):
        col[:, c] = np.interp(y, [p for p, _ in st], [rgb[c] for _, rgb in st])
    img = np.repeat(col[:, None, :], W, 1)
    r = np.random.default_rng(1)
    img += r.normal(0, 1.6, (H, W, 1)).astype(np.float32)          # a touch of grain, no banding
    return np.clip(img, 0, 255)


class GradPlate(El):
    z = 10

    def draw(self, frame, t, ctx):
        frame[:] = gradient_plate(self.d.get("palette", "green"))


SW, SH = 192, 108


class LightLeak(El):
    """A warm film burn (AB: 25 of these): a saturated yellow/orange field rolls down from the top over the outgoing
    shot with a wavy edge and a hot column, covers the whole frame for a few frames at the cut (yellow at the top,
    orange in the middle, brown-red at the bottom) and washes off the incoming shot."""
    z = 97
    COL = [(0.0, (255, 251, 128)), (0.3, (252, 222, 100)), (0.52, (240, 160, 70)), (0.72, (150, 88, 42)), (1.0, (110, 44, 28))]

    def __init__(self, d):
        super().__init__(d)
        r = np.random.default_rng(d.get("seed", 1))
        self.ph = r.uniform(0, 6.28, 4)
        self.col_x = r.uniform(0.6, 0.95) if r.uniform() < 0.5 else r.uniform(0.05, 0.4)
        self.soft = d.get("soft", False)              # over his face: lets more of the shot through, brighter
        yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
        self.yy, self.xx = yy / SH, xx / SW
        col = np.zeros((SH, SW, 3), np.float32)
        for c in range(3):
            col[..., c] = np.interp(self.yy, [p for p, _ in self.COL], [v[c] for _, v in self.COL])
        self.col = col

    def draw(self, frame, t, ctx):
        u = clamp((t - self.t0) / (self.t1 - self.t0))
        env = clamp(u / 0.32) if u < 0.5 else clamp((1 - u) / 0.45)
        env = env * env * (3 - 2 * env)
        if env <= 0.01:
            return
        x, y = self.xx, self.yy
        front = -0.15 + 2.6 * min(u, 0.55)                                 # the burn rolls down from the top
        edge = front + 0.07 * np.sin(x * 9 + self.ph[0] + 6 * u) + 0.05 * np.sin(x * 23 + self.ph[1])
        cover = np.clip((edge - y) / 0.22, 0, 1)
        flare = np.exp(-((x - self.col_x - 0.15 * (u - 0.5)) / 0.07) ** 2) * np.clip(1.4 - y, 0, 1)   # hot column
        cover = np.clip(np.maximum(cover, flare * 0.9), 0, 1)
        col = self.col * (1 + 0.25 * flare[..., None])
        a = (cover * env * (0.9 if self.soft else 0.95))[..., None].astype(np.float32)
        big_col = cv2.resize(np.clip(col, 0, 255).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        big_a = cv2.GaussianBlur(cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 18)[..., None]
        expo = np.clip(frame * (1 + 0.9 * env * big_a), 0, 255)            # the shot over-exposes under the burn
        scr = 255 - (255 - expo) * (255 - big_col) / 255
        mix = big_col * 0.55 + scr * 0.45 if not self.soft else big_col * 0.5 + scr * 0.5
        frame[:] = expo * (1 - big_a) + mix * big_a


# ------------------------------------------------------------------ line icons
def _icon(name, s=160, lw=7):
    """White line icons drawn at size s (RGBA)."""
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    c = s / 2
    if name == "time":                                   # hourglass
        d.line([(s * .28, s * .14), (s * .72, s * .14)], fill=255, width=lw)
        d.line([(s * .28, s * .86), (s * .72, s * .86)], fill=255, width=lw)
        d.line([(s * .33, s * .14), (s * .33, s * .28), (s * .5, s * .5), (s * .33, s * .72), (s * .33, s * .86)], fill=255, width=lw, joint="curve")
        d.line([(s * .67, s * .14), (s * .67, s * .28), (s * .5, s * .5), (s * .67, s * .72), (s * .67, s * .86)], fill=255, width=lw, joint="curve")
        d.polygon([(s * .38, s * .78), (s * .62, s * .78), (s * .5, s * .66)], fill=255)
    elif name == "location":                             # pin over a ring
        d.ellipse((s * .2, s * .66, s * .8, s * .9), outline=255, width=lw)
        d.ellipse((s * .38, s * .1, s * .62, s * .34), outline=255, width=lw)
        d.line([(s * .5, s * .34), (s * .5, s * .74)], fill=255, width=lw)
    elif name == "freedom":                              # diamond over rising arrows
        d.polygon([(s * .3, s * .26), (s * .4, s * .12), (s * .6, s * .12), (s * .7, s * .26), (s * .5, s * .5)], outline=255, width=lw)
        d.line([(s * .3, s * .26), (s * .7, s * .26)], fill=255, width=lw - 2)
        for x0 in (.3, .5, .7):
            d.line([(s * x0, s * .9), (s * x0, s * .62)], fill=255, width=lw - 1)
            d.line([(s * (x0 - .07), s * .69), (s * x0, s * .6), (s * (x0 + .07), s * .69)], fill=255, width=lw - 1)
    elif name in ("phone", "phone_ring"):                # phone with a handset (and ringing marks)
        d.rounded_rectangle((s * .32, s * .1, s * .68, s * .9), int(s * .06), outline=255, width=lw)
        d.arc((s * .4, s * .38, s * .62, s * .62), 200, 340, fill=255, width=lw - 2)
        d.line([(s * .45, s * .82), (s * .55, s * .82)], fill=255, width=lw - 2)
        if name == "phone_ring":
            for k, rr in enumerate((.1, .17)):
                d.line([(s * (.22 - rr / 2), s * .4), (s * (.22 - rr / 2), s * .6)], fill=255, width=lw - 2)
                d.line([(s * (.78 + rr / 2), s * .4), (s * (.78 + rr / 2), s * .6)], fill=255, width=lw - 2)
    elif name == "shield":                               # bulletproof
        pts = [(c, s * .08), (s * .84, s * .2), (s * .8, s * .58), (c, s * .92), (s * .2, s * .58), (s * .16, s * .2)]
        d.polygon(pts, outline=255, width=lw)
        d.line([(s * .36, s * .5), (s * .47, s * .62), (s * .66, s * .38)], fill=255, width=lw)
    elif name == "chart":
        d.line([(s * .12, s * .86), (s * .88, s * .86)], fill=255, width=lw)
        d.line([(s * .16, s * .72), (s * .38, s * .52), (s * .55, s * .62), (s * .84, s * .24)], fill=255, width=lw, joint="curve")
        d.line([(s * .7, s * .22), (s * .86, s * .22), (s * .86, s * .38)], fill=255, width=lw)
    elif name == "dollar":
        d.ellipse((s * .12, s * .12, s * .88, s * .88), outline=255, width=lw)
        d.arc((s * .34, s * .28, s * .64, s * .52), 90, 300, fill=255, width=lw)
        d.arc((s * .36, s * .48, s * .66, s * .72), 270, 120, fill=255, width=lw)
        d.line([(c, s * .2), (c, s * .8)], fill=255, width=lw - 2)
    elif name == "check":
        d.ellipse((s * .12, s * .12, s * .88, s * .88), outline=255, width=lw)
        d.line([(s * .32, s * .52), (s * .45, s * .65), (s * .7, s * .38)], fill=255, width=lw)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(0.6)), np.float32)
    out = np.zeros((s, s, 4), np.float32)
    out[..., :3] = 255
    out[..., 3] = a
    return out


@functools.lru_cache(maxsize=32)
def icon_rgba(name, s):
    return _icon(name, s, max(5, int(s / 15)))


@functools.lru_cache(maxsize=8)
def dashed_circle(r, lw=6, dashes=22):
    s = int(2 * r + 2 * lw + 4)
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    box = (lw + 2, lw + 2, s - lw - 2, s - lw - 2)
    step = 360 / dashes
    for k in range(dashes):
        d.arc(box, k * step, k * step + step * 0.55, fill=255, width=lw)
    out = np.zeros((s, s, 4), np.float32)
    out[..., :3] = 255
    out[..., 3] = np.asarray(im, np.float32)
    return out


def _shadowed(frame, arr, x, y, op):
    sh = arr.copy()
    sh[..., :3] = 0
    sh[..., 3] = cv2.GaussianBlur(arr[..., 3], (0, 0), 4) * 0.5
    blend(frame, sh, x, y + 4, op)
    blend(frame, arr, x, y, op)


class IconCircle(El):
    """A white line icon with its label under it, inside a white dashed circle; pops in (AB: r ~195 px at 1080p, icon
    ~100 px above the centre, label ~64 px bold under it)."""
    z = 80

    def draw(self, frame, t, ctx):
        d = self.d
        k = (t - self.t0) / 0.3
        sc = 0.6 + 0.4 * ease_out_back(k, 1.8)
        op = clamp(k * 2)
        r = d.get("r", 195)
        circ = fx.resize_rgba(dashed_circle(r, 9, 24), sc)
        _shadowed(frame, circ, d["cx"] - circ.shape[1] / 2, d["cy"] - circ.shape[0] / 2, op)
        ic = fx.resize_rgba(icon_rgba(d["icon"], d.get("icon_size", 124)), sc)
        _shadowed(frame, ic, d["cx"] - ic.shape[1] / 2, d["cy"] - 0.3 * r * sc - ic.shape[0] / 2, op)
        if d.get("label"):
            size = d.get("label_size", 64) * sc
            L = fx.Line(d["label"], "bold", size, (255, 255, 255), d["cx"], d["cy"] + 0.33 * r * sc, 0, 1e9, align="center",
                        track=-2, reveal="cut", shadow=(0.6, 4), alpha=op)
            L.draw(frame, t)


class LineIcon(El):
    """A white line icon on its own (above a card's text or a caption); pops in."""
    z = 81

    def draw(self, frame, t, ctx):
        d = self.d
        k = (t - self.t0) / 0.28
        sc = 0.55 + 0.45 * ease_out_back(k, 1.8)
        op = clamp(k * 2) * clamp((self.t1 - t) / 0.12)
        ic = fx.resize_rgba(icon_rgba(d["icon"], d.get("size", 120)), sc)
        _shadowed(frame, ic, d["cx"] - ic.shape[1] / 2, d["cy"] - ic.shape[0] / 2, op)


@functools.lru_cache(maxsize=64)
def _card(name, h, radius=14):
    im = Image.open(asset(name)).convert("RGB")
    s = h / im.height
    im = im.resize((max(1, round(im.width * s)), h), Image.LANCZOS)
    return fx.rounded_card(im, radius, 0, (255, 255, 255), 0.45, 18, 8).astype(np.float32)


class Carousel(El):
    """Testimonial screenshots in a row, sliding left (fast at first, then easing), with motion blur."""
    z = 40

    def __init__(self, d):
        super().__init__(d)
        r = np.random.default_rng(d.get("seed", 5))
        # like AB's: the posts at a few different sizes and heights, as if at different depths
        self.cards = [_card(n, int(d.get("h", 420) * r.uniform(0.72, 1.0))) for n in d["imgs"]]
        self.dys = [float(r.uniform(-70, 70)) for _ in d["imgs"]]
        self.gap = d.get("gap", 70)
        self.total = sum(c.shape[1] for c in self.cards) + self.gap * len(self.cards)

    def draw(self, frame, t, ctx):
        d = self.d
        dur = self.t1 - self.t0
        u = clamp((t - self.t0) / dur)
        travel = d.get("travel", 900)
        x = d.get("x0", 1500) - travel * u                          # slides left continuously (AB)
        v = travel / dur                                            # px/s
        blur = int(min(v / 60, 30))
        layer = np.zeros((H, W, 4), np.float32)
        cx = x
        for c, dy in zip(self.cards, self.dys):
            ch, cw = c.shape[:2]
            if cx < W + 50 and cx + cw > -50:
                yy = int(d.get("cy", 600) - ch / 2 + dy)
                x0, y0 = int(cx), yy
                xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + cw), min(H, y0 + ch)
                if xa < xb and ya < yb:
                    src = c[ya - y0:yb - y0, xa - x0:xb - x0]
                    dst = layer[ya:yb, xa:xb]
                    a = src[..., 3:4] / 255
                    dst[..., :3] = dst[..., :3] * (1 - a) + src[..., :3] * a
                    dst[..., 3:4] = np.maximum(dst[..., 3:4], src[..., 3:4])
            cx += cw + self.gap
        if blur > 1:
            layer = cv2.blur(layer, (blur * 2 + 1, 1))
        op = clamp((t - self.t0) / 0.15)
        a = layer[..., 3:4] / 255 * op
        frame[:] = frame * (1 - a) + layer[..., :3] * a


class ZoomCard(El):
    """A card that scales up from a small thumbnail to its full size (AB's application card)."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        im = Image.open(asset(d["img"])).convert("RGBA")
        s = d["w"] / im.width
        im = im.resize((d["w"], round(im.height * s)), Image.LANCZOS)
        if d.get("blur"):
            im = im.filter(ImageFilter.GaussianBlur(d["blur"]))
        self.img = fx.rounded_card(im, d.get("radius", 36), 0, (255, 255, 255), 0.45, 26, 12).astype(np.float32)

    def draw(self, frame, t, ctx):
        d = self.d
        k = ease_out((t - self.t0) / d.get("dur", 0.6), 3)
        sc = d.get("s0", 0.08) + (1 - d.get("s0", 0.08)) * k
        x0, y0 = d.get("from", (640, 300))
        cx = x0 + (d["cx"] - x0) * k
        cy = y0 + (d["cy"] - y0) * k
        im = fx.resize_rgba(self.img, sc)
        blend(frame, im, cx - im.shape[1] / 2, cy - im.shape[0] / 2, clamp((t - self.t0) / 0.1))


class WallUp(El):
    """Testimonial screenshots in a grid on the green plate, scrolling up (the wall under AB's sliding-up shot)."""
    z = 15

    def __init__(self, d):
        super().__init__(d)
        cols = d.get("cols", 3)
        cw = d.get("card_w", 520)
        gap = 60
        heights = [0] * cols
        canvas_h = 3200
        layer = np.zeros((canvas_h, W, 4), np.float32)
        r = np.random.default_rng(d.get("seed", 3))
        x_left = (W - (cols * cw + (cols - 1) * gap)) / 2
        for i, n in enumerate(d["imgs"]):
            im = Image.open(asset(n)).convert("RGB")
            s = cw / im.width
            im = im.resize((cw, max(1, round(im.height * s))), Image.LANCZOS)
            card = fx.rounded_card(im, 12, 0, (255, 255, 255), 0.4, 16, 8).astype(np.float32)
            c = int(np.argmin(heights))
            hh, ww = card.shape[:2]
            x = int(min(max(0, x_left + c * (cw + gap) + r.uniform(-30, 30)), W - ww))
            y = int(heights[c] + r.uniform(0, 40))
            if y + hh < canvas_h:
                dst = layer[y:y + hh, x:x + ww]
                a = card[..., 3:4] / 255
                dst[..., :3] = dst[..., :3] * (1 - a) + card[..., :3] * a
                dst[..., 3:4] = np.maximum(dst[..., 3:4], card[..., 3:4])
            heights[c] = y + hh + gap
        self.layer = layer
        self.used = min(canvas_h, max(heights))

    def draw(self, frame, t, ctx):
        d = self.d
        u = clamp((t - self.t0) / (self.t1 - self.t0))
        start, end = d.get("y_start", 700), d.get("y_end", -(self.used - 900))
        off = start + (end - start) * ease_in_out(u) if d.get("ease", True) else start + (end - start) * u
        y0 = int(off)
        a_l = max(0, -y0)
        b_l = min(self.used, H - y0)
        if b_l <= a_l:
            return
        seg = self.layer[a_l:b_l]
        ys = y0 + a_l
        v = abs(end - start) / max(self.t1 - self.t0, 0.1)
        if v > 300:
            seg = cv2.blur(seg, (1, int(min(v / 120, 21)) * 2 + 1))
        dst = frame[ys:ys + seg.shape[0]]
        a = seg[..., 3:4] / 255
        dst[:] = dst * (1 - a) + seg[..., :3] * a


class ShrinkUp(El):
    """His shot shrinks into a rounded card and slides up off the frame, revealing what's under it."""
    z = 70

    def draw(self, frame, t, ctx):
        d = self.d
        dt = t - self.t0
        k1 = ease_in_out(dt / d.get("shrink", 0.6))
        k2 = ease_in_out((dt - d.get("shrink", 0.6) - d.get("hold", 0.9)) / d.get("slide", 0.7))
        sc = 1 - (1 - d.get("scale", 0.58)) * k1
        cy = 540 - (540 - d.get("cy", 330)) * k1 - (d.get("cy", 330) + 700) * k2
        shot = ctx["shot"]
        w, h = int(W * sc), int(H * sc)
        small = cv2.resize(shot, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)
        rad = int(30 * k1)
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), rad, fill=255)
        rgba = np.dstack([small, np.asarray(m, np.float32)])
        if k1 > 0.02:
            sh = np.zeros((h + 80, w + 80, 4), np.float32)
            sh[40:40 + h, 40:40 + w, 3] = 255 * 0.5 * k1
            sh[..., 3] = cv2.GaussianBlur(sh[..., 3], (0, 0), 20)
            blend(frame, sh, 960 - w / 2 - 40, cy - h / 2 - 40 + 14, 1)
        blend(frame, rgba, 960 - w / 2, cy - h / 2, 1)


class JagLine(El):
    """A jagged chart line falling across the frame, drawing itself (AB's red card): thick, dark maroon where it
    crosses the bright top of the card, bright crimson low down, with a soft dark shadow."""
    z = 30
    PTS = [(-30, -20), (480, 294), (390, 600), (1080, 666), (1026, 861), (1950, 1100)]

    def draw(self, frame, t, ctx):
        d = self.d
        u = clamp((t - self.t0) / d.get("dur", 1.0))
        pts = [tuple(p) for p in d.get("pts", self.PTS)]
        segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        L = sum(segs) * ease_out(u, 2)
        out, acc = [pts[0]], 0
        for (a, b), sl in zip(zip(pts, pts[1:]), segs):
            if acc + sl <= L:
                out.append(b)
                acc += sl
            else:
                f = (L - acc) / sl
                out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                break
        if len(out) < 2:
            return
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).line(out, fill=255, width=d.get("width", 20), joint="curve")
        a = np.asarray(im, np.float32)[..., None] / 255
        sh = np.roll(cv2.GaussianBlur(a, (0, 0), 9)[..., None], 10, axis=0) * 0.55
        frame[:] = frame * (1 - sh) + np.array([25, 0, 5], np.float32) * sh
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        top, bot = np.array(d.get("rgb_top", (95, 4, 22)), np.float32), np.array(d.get("rgb_bot", (236, 18, 64)), np.float32)
        col = top * (1 - y) + bot * y
        frame[:] = frame * (1 - a) + col * a


class WordCap(El):
    """AB's thank-you text, captions and cards alike: each line is laid out at its full width (centred) first, then every
    word comes in on its own time, rising ~15 px from below, blurred, grey and half see-through, sharp and white after
    0.25 s. Earlier words stay. Soft dark shadow straight down."""
    z = 84

    def __init__(self, d):
        super().__init__(d)
        self.items = []
        for L in d["lines"]:
            size, kind, track = L.get("size", 83), L.get("kind", "bold"), L.get("track", -3)
            text = " ".join(w["w"] for w in L["words"])
            xs, wtot = fx.advances(kind, size, text, track)
            x0 = L.get("x", 960) - wtot / 2
            pos = 0
            for w in L["words"]:
                i = text.index(w["w"], pos)
                pos = i + len(w["w"])
                self.items.append(fx.Line(w["w"], kind, size, tuple(L.get("rgb", (255, 255, 255))), x0 + xs[i], L["y"],
                                          w["t"], self.t1, align="left", track=track, reveal=L.get("reveal", "rise"),
                                          shadow=tuple(L.get("shadow", (0.6, max(3, size * 0.05))))))

    def draw(self, frame, t, ctx):
        for L in self.items:
            L.draw(frame, t)


class Seq(El):
    """Pictures one after another, each held a moment, in a frame (AB's four guru thumbnails in about a second)."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        self.imgs = []
        for n in d["imgs"]:
            im = Image.open(asset(n)).convert("RGB")
            s = d["w"] / im.width
            im = im.resize((d["w"], round(im.height * s)), Image.LANCZOS)
            self.imgs.append(fx.rounded_card(im, d.get("radius", 10), d.get("border", 0), (255, 255, 255), 0.5, 24, 12)
                             .astype(np.float32))

    def draw(self, frame, t, ctx):
        d = self.d
        k = min(len(self.imgs) - 1, int((t - self.t0) / d.get("each", 0.25)))
        im = self.imgs[k]
        tin = t - self.t0 - k * d.get("each", 0.25)
        sc = 1.04 - 0.04 * ease_out(tin / 0.2, 3)                     # each one lands with a tiny settle
        im = fx.resize_rgba(im, sc)
        blend(frame, im, d.get("cx", 960) - im.shape[1] / 2, d.get("cy", 525) - im.shape[0] / 2, 1.0)


TYPES = {"gradplate": GradPlate, "leak": LightLeak, "iconcircle": IconCircle, "lineicon": LineIcon, "carousel": Carousel,
         "zoomcard": ZoomCard, "wallup": WallUp, "shrinkup": ShrinkUp, "jagline": JagLine,
         "wordcap": WordCap, "seq": Seq}
