"""Every on-screen element of the AB-style edit. Each one is built from a dict (from edit.json) and draws itself onto a
float32 RGB frame at output time t. ctx["base"] is the cut A-roll frame (uint8) before zoom, ctx["shot"] the zoomed one.
"""
import functools, math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

import fx
import money
from fx import W, H, blend, clamp, ease_out, ease_in_out, ease_out_back

GFX = os.environ.get("JEAN_GFX", "/home/user/work/gfx")
GEN = os.environ.get("JEAN_GEN", "/home/user/work/gen")
SEG_MODEL = "/home/user/work/models/mp/selfie_segmenter.tflite"


def asset(name):
    for d in (GFX, f"{GFX}/crop", GEN):
        for ext in ("", ".png", ".jpg"):
            p = f"{d}/{name}{ext}"
            if os.path.isfile(p):
                return p
    raise FileNotFoundError(name)


class El:
    z = 50

    def __init__(self, d):
        self.d = d
        self.t0, self.t1 = d["t0"], d["t1"]
        self.z = d.get("z", self.z)

    def active(self, t):
        return self.t0 <= t < self.t1

    def close(self):
        pass


class Plate(El):
    z = 10

    def draw(self, frame, t, ctx):
        a = 1.0
        fi, fo = self.d.get("fade_in", 0), self.d.get("fade_out", 0)
        if fi:
            a = min(a, clamp((t - self.t0) / fi))
        if fo:
            a = min(a, clamp((self.t1 - t) / fo))
        rgb = np.array(self.d["rgb"], np.float32)
        if a >= 1:
            frame[:] = rgb
        else:
            frame *= 1 - a
            frame += rgb * a


class Grad(El):
    z = 20

    def draw(self, frame, t, ctx):
        f = self.d.get("fade", 0.2)
        a = 1.0 if f <= 0 else min(clamp((t - self.t0) / f), clamp((self.t1 - t) / f))
        blend(frame, fx.gradient(self.d["kind"], self.d.get("strength", 1.0)), 0, 0, a)


@functools.lru_cache(maxsize=128)
def card_image(name, w, h, border, radius, shadow, border_rgb=(255, 255, 255), bw=False):
    im = Image.open(asset(name)).convert("RGBA")
    s = min(w / im.width if w else 1e9, h / im.height if h else 1e9) if (w or h) else 1.0
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    if bw:
        g = im.convert("L").convert("RGBA")
        g.putalpha(im.split()[3])
        im = g
    if radius == 0 and border == 0 and shadow == 0:
        return np.asarray(im)
    return fx.rounded_card(im, radius, border, tuple(border_rgb), shadow)


class Card(El):
    """An image (screenshot, certificate, photo, 3D object) with AB's entrances: pop, fly in from an edge, cut, slide."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        self.img = card_image(d["img"], d.get("w", 0), d.get("h", 0), d.get("border", 0), d.get("radius", 0),
                              d.get("shadow", 0.0), tuple(d.get("border_rgb", (255, 255, 255))), d.get("bw", False))
        self.rot = d.get("rot", 0.0)
        if self.rot:
            pil = Image.fromarray(self.img).rotate(self.rot, resample=Image.BICUBIC, expand=True)
            self.img = np.asarray(pil)
        self.cache = {}

    def draw(self, frame, t, ctx):
        d = self.d
        a = d.get("anim", "pop")
        tin = t - self.t0
        tout = self.t1 - t
        op, sc, dx, dy = 1.0, 1.0, 0.0, 0.0
        if a == "pop":
            k = tin / 0.28
            sc = 0.82 + 0.18 * ease_out_back(k, 1.6)
            op = clamp(k * 2.5)
        elif a == "fly":
            k = ease_out(tin / d.get("dur", 0.4), 3)
            fx_, fy_ = d.get("from", (0, 1300))
            dx, dy = fx_ * (1 - k), fy_ * (1 - k)
        elif a == "fade":
            op = clamp(tin / 0.25)
        elif a == "slide_up":
            k = ease_out(tin / 0.45, 3)
            dy = 900 * (1 - k)
        elif a == "zoom_in":                       # slow push like AB's stills
            sc = 1.0 + d.get("push", 0.06) * clamp(tin / max(self.t1 - self.t0, 0.1))
            op = clamp(tin / 0.12)
        if d.get("drift"):
            sc *= 1 + d["drift"] * clamp(tin / max(self.t1 - self.t0, 0.1))
        if d.get("out") == "fade":
            op *= clamp(tout / 0.2)
        elif d.get("out") == "fly":
            k = 1 - clamp(tout / 0.3)
            ox, oy = d.get("to", (0, -1300))
            dx += ox * ease_in_out(k)
            dy += oy * ease_in_out(k)
        if op <= 0:
            return
        key = round(sc, 3)
        if key not in self.cache:
            if len(self.cache) > 40:
                self.cache.clear()
            self.cache[key] = fx.resize_rgba(self.img, sc)
        im = self.cache[key]
        h, w = im.shape[:2]
        blend(frame, im, d["cx"] + dx - w / 2, d["cy"] + dy - h / 2, op * d.get("alpha", 1.0))


class Text(El):
    z = 80

    def __init__(self, d):
        super().__init__(d)
        self.lines = []
        for L in d["lines"]:
            self.lines.append(fx.Line(L["text"], L.get("kind", "medium"), L["size"], tuple(L.get("rgb", (255, 255, 255))),
                                      L["x"], L["y"], L.get("t_in", self.t0), L.get("t_out", self.t1),
                                      align=L.get("align", "left"), track=L.get("track", -4),
                                      reveal=L.get("reveal", "blur"), shadow=tuple(L["shadow"]) if L.get("shadow") else None,
                                      glow=(tuple(L["glow"][0]), L["glow"][1]) if L.get("glow") else None,
                                      type_cps=L.get("cps"), fade_out=L.get("fade_out", 0.0), alpha=L.get("alpha", 1.0)))

    def draw(self, frame, t, ctx):
        for L in self.lines:
            L.draw(frame, t)


def money_fmt(v, decimals=0, prefix="$", suffix=""):
    s = f"{v:,.{decimals}f}"
    return f"{prefix}{s}{suffix}"


class Counter(El):
    """AB's counters: the number runs up (or down) fast on a log scale with an ease-out and then holds."""
    z = 82

    def draw(self, frame, t, ctx):
        d = self.d
        u = clamp((t - d.get("t_count", self.t0)) / d.get("dur", 1.1))
        v0, v1 = d["v0"], d["v1"]
        k = ease_out(u, d.get("ease", 2.2))
        if v0 > 0 and v1 > 0:
            v = math.exp(math.log(v0) + (math.log(v1) - math.log(v0)) * k)
        else:
            v = v0 + (v1 - v0) * k
        if u >= 1:
            v = v1
        txt = money_fmt(v, d.get("decimals", 0), d.get("prefix", "$"), d.get("suffix", ""))
        y = d["y"]
        if d.get("move"):                              # AB moves the number up when the line under it builds
            tm, dy = d["move"]
            y += dy * ease_out((t - tm) / 0.3, 3) if t >= tm else 0
        x = d["x"]
        if d.get("move_x"):
            tm, dxx = d["move_x"]
            x += dxx * ease_out((t - tm) / 0.35, 3) if t >= tm else 0
        L = fx.Line(txt, d.get("kind", "semibold"), d["size"], tuple(d.get("rgb", fx.BLUE)), x, y, self.t0, self.t1,
                    align=d.get("align", "center"), track=d.get("track", -8), reveal="cut",
                    shadow=tuple(d["shadow"]) if d.get("shadow") else None)
        op = clamp((t - self.t0) / d.get("fade_in", 0.001))
        if op < 1:
            sub = frame.copy()
            L.draw(sub, t)
            frame += (sub - frame) * op
        else:
            L.draw(frame, t)


class Pill(El):
    """AB's frosted-glass pill behind the 'Available Balance' number."""
    z = 81

    def draw(self, frame, t, ctx):
        d = self.d
        x0, y0, x1, y1 = d["box"]
        r = d.get("radius", 70)
        reg = frame[y0:y1, x0:x1]
        blur = cv2.GaussianBlur(reg, (0, 0), 18)
        m = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), r, fill=255)
        a = (np.asarray(m, np.float32) / 255)[..., None]
        glass = blur * 0.75 + 255 * 0.12
        reg[:] = reg * (1 - a) + glass * a
        o = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(o).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), r, outline=255, width=3)
        oa = (np.asarray(o, np.float32) / 255)[..., None] * 0.35
        reg[:] = reg * (1 - oa) + 255 * oa


class Drop(El):
    """AB's money drop. layer 'far' under the text, 'near' (big blurred bills) over it."""
    z = 70
    _cache = {}

    def __init__(self, d):
        super().__init__(d)
        key = (d["t0"], d["t1"], d.get("seed", 3))
        if key not in Drop._cache:
            gp = {}
            if os.path.exists(f"{GEN}/bill_front_cut.png"):
                gp = {"front": f"{GEN}/bill_front_cut.png", "back": f"{GEN}/bill_back_cut.png"}
            Drop._cache[key] = money.MoneyDrop(d["t0"], d["t1"], n=d.get("n", 26), seed=d.get("seed", 3),
                                               near_n=d.get("near_n", 5), gen_paths=gp, rate=d.get("rate", 0.55))
        self.md = Drop._cache[key]

    def draw(self, frame, t, ctx):
        self.md.draw(frame, t, self.d.get("layer", "all"))


class MoneyBG(El):
    z = 15

    def __init__(self, d):
        super().__init__(d)
        gp = d.get("gen")
        self.mb = money.MoneyBroll(d["t0"], d["t1"], seed=d.get("seed", 5), gen_path=asset(gp) if gp else None,
                                   darken=d.get("darken", 0.0), blur=d.get("blur", 0.0), whip=d.get("whip", True))

    def draw(self, frame, t, ctx):
        self.mb.draw(frame, t)


class Still(El):
    """A generated stock-style still used like AB's stock clips: fills the frame, slow push-in, optional whip-in, darken."""
    z = 15

    def __init__(self, d):
        super().__init__(d)
        im = Image.open(asset(d["img"])).convert("RGB")
        s = max(W * 1.25 / im.width, H * 1.25 / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        self.img = np.asarray(im, np.float32)

    def draw(self, frame, t, ctx):
        d = self.d
        u = clamp((t - self.t0) / max(self.t1 - self.t0, 0.1))
        z = 1.0 + d.get("push", 0.08) * u
        ih, iw = self.img.shape[:2]
        cw, ch = W * 1.25 / 1.25 / z * (iw / (W * 1.25)) * 1.25, 0
        cw = iw / 1.25 / z
        ch = ih / 1.25 / z
        px, py = d.get("pan", (0.0, 0.0))
        cx = iw / 2 + px * u * iw * 0.08
        cy = ih / 2 + py * u * ih * 0.08
        x0, y0 = cx - cw / 2, cy - ch / 2
        M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        img = cv2.warpAffine(self.img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        tin = t - self.t0
        if d.get("whip", False) and tin < 0.22:
            k = int((1 - tin / 0.22) * 70) * 2 + 1
            img = cv2.blur(img, (k, 1))
        if d.get("blur"):
            img = cv2.GaussianBlur(img, (0, 0), d["blur"])
        frame[:] = img * (1 - d.get("darken", 0.0))


class Fire(El):
    """A $100 bill burning on black (AB 3:34)."""
    z = 60

    def __init__(self, d):
        super().__init__(d)
        p = f"{GEN}/burning_bill.png"
        self.photo = None
        if d.get("photo", True) and os.path.exists(p):
            im = Image.open(p).convert("RGB")
            s = d.get("h", 820) / im.height
            self.photo = np.asarray(im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS), np.float32)
        self.bill = money.bill("front")

    def draw(self, frame, t, ctx):
        d = self.d
        tin = t - self.t0
        if self.photo is not None:
            ph = self.photo
            h, w = ph.shape[:2]
            # screen-blend the photo on black (its own black background disappears), flicker brightness a little
            fl = 0.92 + 0.08 * math.sin(tin * 23) * math.sin(tin * 7.3)
            x0, y0 = int(d["cx"] - w / 2), int(d["cy"] - h / 2 + 30 * (1 - ease_out(tin / 0.4)))
            xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
            src = ph[ya - y0:yb - y0, xa - x0:xb - x0] * fl
            dst = frame[ya:yb, xa:xb]
            dst[:] = 255 - (255 - dst) * (255 - src) / 255
            return
        b = cv2.resize(self.bill, (300, 700))
        blend(frame, b, d["cx"] - 150, d["cy"] - 300, 1)
        f = money.fire_frame(tin)
        blend(frame, f, d["cx"] - 260, d["cy"] - 600, 1)


class Pip(El):
    """AB's name card: the shot shrinks into a rounded card with a thin white border on the left, over a dark blurred chart."""
    z = 30

    def __init__(self, d):
        super().__init__(d)
        self.bg = np.asarray(Image.open(asset(d.get("bg", "candle_bg"))).convert("RGB"), np.float32)

    def draw(self, frame, t, ctx):
        d = self.d
        k = ease_out((t - self.t0) / d.get("dur", 0.22), 3)
        bx0, by0, bx1, by1 = d["card"]
        fcx, fcy = d.get("face", (960, 430))
        cw, ch = bx1 - bx0, by1 - by0
        # source crop: full frame -> a 1:1 crop around his face
        sx0 = 0 + (fcx - cw / 2 - 0) * k
        sy0 = 0 + (fcy - ch / 2 - 0) * k
        sx1 = W + (fcx + cw / 2 - W) * k
        sy1 = H + (fcy + ch / 2 - H) * k
        dx0, dy0 = 0 + (bx0 - 0) * k, 0 + (by0 - 0) * k
        dx1, dy1 = W + (bx1 - W) * k, H + (by1 - H) * k
        frame[:] = self.bg
        base = ctx["base"]
        sx0, sy0 = max(0, sx0), max(0, sy0)
        sx1, sy1 = min(W, sx1), min(H, sy1)
        crop = base[int(sy0):int(sy1), int(sx0):int(sx1)]
        tw, th = max(2, int(round(dx1 - dx0))), max(2, int(round(dy1 - dy0)))
        card = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_AREA).astype(np.float32)
        r = int(10 + 18 * k)
        bd = int(round(5 * k))
        m = Image.new("L", (tw + 2 * bd, th + 2 * bd), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, tw + 2 * bd - 1, th + 2 * bd - 1), r + bd, fill=255)
        mi = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(mi).rounded_rectangle((0, 0, tw - 1, th - 1), r, fill=255)
        rgba_b = np.zeros((th + 2 * bd, tw + 2 * bd, 4), np.float32)
        rgba_b[..., :3] = 245
        rgba_b[..., 3] = np.asarray(m)
        blend(frame, rgba_b, dx0 - bd, dy0 - bd, 1.0 if bd else 0.0)
        rgba = np.dstack([card, np.asarray(mi, np.float32)])
        blend(frame, rgba, dx0, dy0, 1.0)


class Split(El):
    """AB's offer split screen: his shot slides left into a panel; the right side is black (the list builds on it)."""
    z = 30

    def draw(self, frame, t, ctx):
        d = self.d
        k = min(ease_out((t - self.t0) / 0.35, 3), ease_out((self.t1 - t) / 0.3, 3))
        pw = d.get("panel_w", 840)
        fcx = d.get("face_x", 960)
        base = ctx["shot"]
        left = int(round(W - (W - pw) * k))
        shift = int(round((fcx - pw / 2) * k))
        shift = max(0, min(shift, W - left))
        out = np.empty_like(frame)
        out[:, :left] = base[:, shift:shift + left]
        out[:, left:] = np.array(d.get("rgb", (4, 4, 6)), np.float32)
        frame[:] = out


class SlideUp(El):
    """His shot slides up off the frame, revealing what's under it (AB 5:54.8). Draw over the next scene."""
    z = 95

    def draw(self, frame, t, ctx):
        k = ease_in_out((t - self.t0) / (self.t1 - self.t0))
        dy = int(round(H * k))
        if dy >= H:
            return
        shot = ctx["shot"]
        frame[: H - dy] = shot[dy:]


class Behind(El):
    """Giant text behind his head (AB's 'ONE SETUP'). His outline from MediaPipe selfie segmentation each frame."""
    z = 55
    _seg = None

    def __init__(self, d):
        super().__init__(d)
        self.lines = [fx.Line(L["text"], L.get("kind", "black"), L["size"], tuple(L.get("rgb", (255, 255, 255))), L["x"], L["y"],
                              L.get("t_in", self.t0), self.t1, align="center", track=L.get("track", -10), reveal=L.get("reveal", "blur"),
                              shadow=(0.45, 8)) for L in d["lines"]]

    def mask(self, shot):
        if Behind._seg is None:
            from mediapipe.tasks.python import vision, BaseOptions
            opts = vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=SEG_MODEL),
                                                output_confidence_masks=True)
            Behind._seg = vision.ImageSegmenter.create_from_options(opts)
        import mediapipe as mp
        small = np.ascontiguousarray(cv2.resize(shot, (512, 288), interpolation=cv2.INTER_AREA).astype(np.uint8))
        r = Behind._seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=small))
        m = r.confidence_masks[0].numpy_view().astype(np.float32)
        m = cv2.GaussianBlur(cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 2.0)
        return np.clip((m - 0.3) / 0.35, 0, 1)[..., None]

    def draw(self, frame, t, ctx):
        layer = frame.copy()
        for L in self.lines:
            L.draw(layer, t)
        if np.abs(layer - frame).max() < 1:
            return
        m = self.mask(ctx["shot"])
        frame[:] = layer * (1 - m) + frame * m


class Rolling(El):
    """AB's rolling list ('Get you in / Get Consistent / Get you out'): a drum that rolls up, current item white with an
    arrow, the others grey and smaller."""
    z = 85

    def draw(self, frame, t, ctx):
        d = self.d
        items, times = d["items"], d["times"]
        cur = 0.0
        for i, ti in enumerate(times):
            if t >= ti and i > 0:
                cur = (i - 1) + ease_out((t - ti) / 0.3, 3)
        op_all = min(clamp((t - self.t0) / 0.2), clamp((self.t1 - t) / 0.2))
        for i, text in enumerate(items):
            dd = i - cur
            if abs(dd) > 1.6:
                continue
            ang = dd * 0.62
            y = d["cy"] + math.sin(ang) * d.get("radius", 190)
            sc = 0.70 + 0.30 * math.cos(ang)
            focus = clamp(1 - abs(dd))
            rgb = tuple(int(150 + 105 * focus) for _ in range(3))
            size = d.get("size", 96) * sc
            arrow = "  ←" if focus > 0.5 else ""
            L = fx.Line(text + arrow, "semibold" if focus > 0.5 else "medium", size, rgb, d["x"], y + size * 0.35,
                        0, 1e9, align=d.get("align", "right"), track=-4, reveal="cut", shadow=(0.4, 4),
                        alpha=op_all * (0.45 + 0.55 * focus) * clamp(1.6 - abs(dd)))
            L.draw(frame, t)


class Wall(El):
    """The 'ask them yourself' wall: Discord posts thanking Jean, tiled and slightly tilted on a dark plate, the camera
    gliding across them."""
    z = 15

    def __init__(self, d):
        super().__init__(d)
        r = np.random.default_rng(d.get("seed", 4))
        cw, ch = 3400, 2000
        canvas = Image.new("RGB", (cw, ch), (10, 10, 12))
        x, y, row_h = 60, 60, 0
        for name in d["imgs"]:
            im = Image.open(asset(name)).convert("RGB")
            s = 560 / im.width if im.width / im.height > 1.0 else 420 / im.width
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            card = Image.fromarray(fx.rounded_card(im, 18, 0, (255, 255, 255), 0.5))
            card = card.rotate(r.uniform(-3, 3), resample=Image.BICUBIC, expand=True)
            if x + card.width > cw - 40:
                x, y = 60, y + row_h + 20
                row_h = 0
            canvas.paste(card, (x, y), card)
            x += card.width + 10
            row_h = max(row_h, card.height - 60)
        self.canvas = np.asarray(canvas, np.float32)
        self.used_h = min(ch, y + row_h + 200)

    def draw(self, frame, t, ctx):
        u = clamp((t - self.t0) / max(self.t1 - self.t0, 0.1))
        z = 1.55 - 0.35 * ease_in_out(u)
        cw, ch = W * z, H * z
        cx = 900 + 1500 * ease_in_out(u)
        cy = self.used_h / 2
        x0, y0 = cx - cw / 2, cy - ch / 2
        M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        img = cv2.warpAffine(self.canvas, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(10, 10, 12))
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.5 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
        frame[:] = img * vig[..., None]


# ---------------------------------------------------------------- charts
GREEN, RED = (8, 153, 129), (242, 54, 69)


def candles_series(kind, seed=1):
    """OHLC lists for the chart animations. kind: 'stophunt' (level, stop run, then the move), 'sweep' (many stops under
    a low get taken, then reversal), 'inducement' (sweep, change of character, entry, run)."""
    r = np.random.default_rng(seed)
    pts = []
    if kind in ("stophunt", "sweep", "inducement"):
        path = list(np.linspace(100, 70, 9) + r.normal(0, 2.5, 9))          # down into the level
        path += list(np.linspace(72, 80, 4) + r.normal(0, 1.5, 4))          # bounce
        path += list(np.linspace(79, 71, 4) + r.normal(0, 1.2, 4))          # back to the level
        path += [62]                                                       # the stop run (wick)
        path += list(np.linspace(78, 132, 12) + r.normal(0, 2.5, 12))       # flies
    o = path[0]
    for i, c in enumerate(path[1:]):
        hi = max(o, c) + abs(r.normal(0, 2))
        lo = min(o, c) - abs(r.normal(0, 2))
        if i == 16:                                       # the stop-run candle: long lower wick, closes back above
            lo, c = 60.0, 75.0
        pts.append((o, hi, lo, c))
        o = c
    return pts


class ChartAnim(El):
    """A clean white trading chart (TradingView colours) that builds candle by candle in time with what Jean says.
    events: list of [t, what] with what in level / entry / stops / sweep / choch / fly / label."""
    z = 30

    def __init__(self, d):
        super().__init__(d)
        self.c = candles_series(d.get("kind", "stophunt"), d.get("seed", 1))
        self.font_b = fx.font("semibold", 30)
        self.font_s = fx.font("medium", 26)

    def draw(self, frame, t, ctx):
        d = self.d
        n_all = len(self.c)
        times = d["reveal"]            # [t_start, t_end] for candles 0..n-1
        k = clamp((t - times[0]) / max(times[1] - times[0], 0.1))
        n = int(round(1 + k * (n_all - 1)))
        fl = d.get("focus_len", None)
        im = Image.new("RGB", (W, H), (255, 255, 255))
        dr = ImageDraw.Draw(im, "RGBA")
        x0, x1, y0, y1 = 170, 1750, 150, 930
        for gy in range(y0, y1 + 1, 130):
            dr.line([(x0, gy), (x1, gy)], fill=(236, 238, 242), width=2)
        for gx in range(x0, x1 + 1, 158):
            dr.line([(gx, y0), (gx, y1)], fill=(236, 238, 242), width=2)
        # auto-scale to the candles on screen, like TradingView (eased so it glides as new candles come in)
        vis = self.c[:max(n, 8)]
        lo_v, hi_v = min(c[2] for c in vis), max(c[1] for c in vis)
        lo_all = min(c[2] for c in self.c) - 6
        hi_all = max(c[1] for c in self.c) + 6
        if not hasattr(self, "_rng"):
            self._rng = (lo_v - 8, hi_v + 8)
        tgt = (min(lo_v - 8, 58.0), hi_v + 10)
        self._rng = (self._rng[0] + (tgt[0] - self._rng[0]) * 0.25, self._rng[1] + (tgt[1] - self._rng[1]) * 0.25)
        lo_all, hi_all = self._rng
        Y = lambda v: y1 - (v - lo_all) / (hi_all - lo_all) * (y1 - y0)
        cw = (x1 - x0) / (n_all + 4)
        X = lambda i: x0 + (i + 2) * cw
        ev = {e[1]: e[0] for e in d.get("events", [])}

        def on(name):
            return name in ev and t >= ev[name]

        level = 71.5
        if on("level"):
            a = clamp((t - ev["level"]) / 0.3)
            dr.line([(x0, Y(level)), (x0 + (x1 - x0) * a, Y(level))], fill=(41, 98, 255, 255), width=4)
            dr.text((x0 + 10, Y(level) - 44), "YOUR LEVEL", font=self.font_b, fill=(41, 98, 255))
        if on("stops"):
            a = clamp((t - ev["stops"]) / 0.6)
            gone = on("sweep")
            for j in range(9):
                if j / 9 > a:
                    break
                xs = X(10 + j * 0.8)
                ys = Y(66.5 - (j % 3) * 0.9)
                fade = 255 if not gone else int(255 * (1 - clamp((t - ev["sweep"] - j * 0.03) / 0.15)))
                if fade <= 0:
                    continue
                dr.rounded_rectangle((xs - 30, ys - 16, xs + 30, ys + 16), 6, fill=(242, 54, 69, fade))
                dr.text((xs - 18, ys - 15), "SL", font=self.font_s, fill=(255, 255, 255, fade))
        elif on("stop"):
            dr.line([(X(13), Y(66.5)), (x1, Y(66.5))], fill=(242, 54, 69, 255), width=3)
            dr.text((x1 - 200, Y(66.5) + 6), "STOP LOSS", font=self.font_b, fill=(242, 54, 69))
        if on("entry"):
            ei = 15
            dr.polygon([(X(ei) - 18, Y(73) + 60), (X(ei) + 18, Y(73) + 60), (X(ei), Y(73) + 28)], fill=(41, 98, 255))
            dr.text((X(ei) - 40, Y(73) + 64), "BUY", font=self.font_b, fill=(41, 98, 255))
        for i in range(min(n, n_all)):
            o, hi, lo, c = self.c[i]
            col = GREEN if c >= o else RED
            dr.line([(X(i), Y(hi)), (X(i), Y(lo))], fill=col, width=3)
            top, bot = Y(max(o, c)), Y(min(o, c))
            dr.rectangle((X(i) - cw * 0.32, top, X(i) + cw * 0.32, max(bot, top + 2)), fill=col)
        if on("stopped") and n > 16:
            dr.rounded_rectangle((X(16) + 30, Y(60) - 10, X(16) + 300, Y(60) + 44), 8, fill=(242, 54, 69, 235))
            dr.text((X(16) + 44, Y(60) - 6), "STOPPED OUT", font=self.font_b, fill=(255, 255, 255))
        if on("liq") and n > 16:
            dr.rounded_rectangle((X(16) + 30, Y(60) - 10, X(16) + 360, Y(60) + 44), 8, fill=(255, 255, 255, 235), outline=(41, 98, 255), width=3)
            dr.text((X(16) + 44, Y(60) - 6), "LIQUIDITY SWEPT", font=self.font_b, fill=(41, 98, 255))
        if on("choch") and n > 20:
            yc = Y(80)
            dr.line([(X(10), yc), (X(21), yc)], fill=(20, 20, 24), width=3)
            dr.text((X(10), yc - 40), "CHoCH", font=self.font_b, fill=(20, 20, 24))
        if on("entry2") and n > 21:
            ei = 21
            dr.polygon([(X(ei) - 18, Y(self.c[ei][2]) + 60), (X(ei) + 18, Y(self.c[ei][2]) + 60), (X(ei), Y(self.c[ei][2]) + 28)], fill=(41, 98, 255))
            dr.text((X(ei) - 60, Y(self.c[ei][2]) + 64), "ENTRY", font=self.font_b, fill=(41, 98, 255))
        if on("fly") and n > 25:
            dr.text((X(n - 1) - 160, Y(self.c[n - 1][1]) - 70), "+ the move", font=self.font_b, fill=GREEN)
        arr = np.asarray(im, np.float32)
        op = min(clamp((t - self.t0) / 0.15), 1.0)
        z = 1.0 + d.get("push", 0.05) * clamp((t - self.t0) / max(self.t1 - self.t0, 0.1))
        if z != 1.0:
            M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z)
            arr = cv2.warpAffine(arr, M, (W, H), borderValue=(255, 255, 255))
        frame[:] = frame * (1 - op) + arr * op


class ChartBroll(El):
    """Dark, moody chart footage stand-in: candles scrolling on a dark screen, out of focus, like AB's stock clips."""
    z = 15

    def __init__(self, d):
        super().__init__(d)
        r = np.random.default_rng(d.get("seed", 9))
        p, self.c = 100.0, []
        for i in range(140):
            o = p
            p += r.normal(0.15, 2.2)
            self.c.append((o, max(o, p) + abs(r.normal(0, 1.2)), min(o, p) - abs(r.normal(0, 1.2)), p))

    def draw(self, frame, t, ctx):
        tin = t - self.t0
        sw, sh = 960, 540
        im = Image.new("RGB", (sw, sh), (6, 8, 12))
        dr = ImageDraw.Draw(im)
        off = tin * 18
        i0 = int(off)
        vis = self.c[i0:i0 + 60]
        lo = min(c[2] for c in vis) - 5
        hi = max(c[1] for c in vis) + 5
        for j, (o, h_, l_, c) in enumerate(vis):
            x = (j - (off - i0)) * 17 + 20
            Y = lambda v: sh - 60 - (v - lo) / (hi - lo) * (sh - 140)
            col = (30, 210, 120) if c >= o else (240, 60, 70)
            dr.line([(x, Y(h_)), (x, Y(l_))], fill=col, width=2)
            dr.rectangle((x - 5, Y(max(o, c)), x + 5, Y(min(o, c)) + 1), fill=col)
        arr = np.asarray(im, np.float32)
        arr = cv2.resize(arr, (W, H), interpolation=cv2.INTER_CUBIC)
        arr = cv2.GaussianBlur(arr, (0, 0), self.d.get("blur", 5))
        glow = cv2.GaussianBlur(arr, (0, 0), 25)
        arr = arr * 0.8 + glow * 0.9
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.6 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
        frame[:] = np.clip(arr * vig[..., None], 0, 255)


TYPES = {"plate": Plate, "grad": Grad, "card": Card, "text": Text, "counter": Counter, "pill": Pill, "drop": Drop,
         "money_bg": MoneyBG, "still": Still, "fire": Fire, "pip": Pip, "split": Split, "slide_up": SlideUp,
         "behind": Behind, "rolling": Rolling, "wall": Wall, "chart": ChartAnim, "chart_broll": ChartBroll}


def build(d):
    if d["type"] not in TYPES:
        import motion
        TYPES.update(motion.TYPES)
    return TYPES[d["type"]](d)
