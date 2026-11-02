"""Stills for the thank-you video (written to /home/user/work/gfx/ty/):

- app_card.png: a stand-in for Jean's application page (AB shows his own, blurred). A white form, "JeanFX Elite
  Mentorship Application", the usual fields and a submit button. It's blurred on screen, like AB's; swap in a real
  screenshot of Jean's page when there is one (same file name).
- guru_1..4.png: four "trading guru" YouTube-style thumbnails for "spread with trading gurus". AB flashes four real
  gurus' thumbnails; these are built from scratch (no real people): loud colours, huge numbers, arrows, 3D emoji.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = "/home/user/work/gfx/ty"
GFX = "/home/user/work/gfx"
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-{}.otf"


def font(w, s):
    return ImageFont.truetype(FONT.format(w), s)


def app_card():
    W, H = 1460, 700
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    t = "JeanFX Elite Mentorship Application"
    f = font("Bold", 64)
    d.text(((W - d.textlength(t, font=f)) / 2, 40), t, font=f, fill=(70, 70, 75))
    fl = font("Medium", 26)
    y = 150
    for label in ("Full name", "Email", "Phone number"):
        d.rounded_rectangle((70, y, W - 70, y + 74), 14, outline=(225, 225, 230), width=3, fill=(250, 250, 252))
        d.text((96, y + 22), label, font=fl, fill=(170, 170, 178))
        y += 98
    d.rounded_rectangle((70, y + 8, W - 70, y + 92), 18, fill=(0, 140, 252))
    b = "Submit Application"
    fb = font("Bold", 34)
    d.text(((W - d.textlength(b, font=fb)) / 2, y + 30), b, font=fb, fill=(255, 255, 255))
    s = "Privacy Policy  |  Terms of Service"
    fs = font("Medium", 20)
    d.text(((W - d.textlength(s, font=fs)) / 2, H - 52), s, font=fs, fill=(190, 190, 196))
    im.save(f"{OUT}/app_card.png")


def obj(name, h):
    o = Image.open(f"{GFX}/obj_{name}.png").convert("RGBA")
    return o.resize((round(o.width * h / o.height), h), Image.LANCZOS)


def stroke_text(d, xy, text, f, fill, stroke=10, anchor="la"):
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0), anchor=anchor)


def bg(top, bot, glow=None):
    W, H = 1280, 720
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(top, np.float32)[None, None]
    b = np.array(bot, np.float32)[None, None]
    img = np.repeat(a * (1 - y) + b * y, W, 1)
    if glow:
        yy, xx = np.mgrid[0:H, 0:W]
        g = np.exp(-(((xx - glow[0]) / 380) ** 2 + ((yy - glow[1]) / 300) ** 2))[..., None]
        img = img + g * np.array(glow[2], np.float32)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


def arrow(d, pts, w=34, fill=(255, 255, 255)):
    d.line(pts, fill=fill, width=w, joint="curve")
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    v = np.array([x1 - x0, y1 - y0], float)
    v /= np.linalg.norm(v)
    n = np.array([-v[1], v[0]])
    tip = np.array([x1, y1]) + v * w * 1.6
    a = np.array([x1, y1]) + n * w * 1.5
    b = np.array([x1, y1]) - n * w * 1.5
    d.polygon([tuple(tip), tuple(a), tuple(b)], fill=fill)


def chart(d, box, up=True, n=26, seed=0, drift=0.03):
    r = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    p = 0.08 if up else 0.9
    w = (x1 - x0) / n
    for i in range(n):
        q = min(0.95, max(0.05, p + r.normal(drift if up else -drift, 0.06)))
        o, c = p, q
        hi, lo = max(o, c) + abs(r.normal(0, 0.02)), min(o, c) - abs(r.normal(0, 0.02))
        col = (40, 220, 120) if c >= o else (240, 60, 70)
        X = x0 + i * w + w / 2
        Y = lambda v: y1 - v * (y1 - y0)
        d.line([(X, Y(hi)), (X, Y(lo))], fill=col, width=3)
        d.rectangle((X - w * 0.32, Y(max(o, c)), X + w * 0.32, Y(min(o, c)) + 2), fill=col)
        p = q


def badge(d, text="14:12"):
    f = font("Bold", 30)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((1280 - w - 34, 720 - 58, 1280 - 12, 720 - 14), 8, fill=(0, 0, 0, 210))
    d.text((1280 - w - 23, 720 - 54), text, font=f, fill=(255, 255, 255))


def guru1():                                        # "$20 -> $53,000" on purple, phone with a chart
    im = bg((40, 10, 90), (120, 30, 200), (640, 360, (60, 20, 90)))
    d = ImageDraw.Draw(im, "RGBA")
    chart(d, (60, 380, 820, 690), True, 22, 3, 0.06)
    stroke_text(d, (40, 60), "$20", font("Black", 180), (255, 255, 255), 12)
    arrow(d, [(330, 110), (470, 50), (600, 95)], 26)
    stroke_text(d, (500, 150), "$53,000", font("Black", 128), (60, 240, 90), 11)
    ph = Image.open(f"{GFX}/phone_us30_chart.png").convert("RGBA")
    ph = ph.resize((round(ph.width * 360 / ph.height), 360), Image.LANCZOS).rotate(-8, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(ph, (930, 330))
    badge(d, "14:12")
    return im


def guru2():                                        # "I MADE $1M TRADING" on red/black, money bag and a sports car
    im = bg((150, 0, 10), (20, 0, 0), (950, 300, (120, 40, 0)))
    d = ImageDraw.Draw(im, "RGBA")
    stroke_text(d, (50, 70), "I MADE", font("Black", 130), (255, 255, 255), 10)
    stroke_text(d, (50, 210), "$1M", font("Black", 250), (255, 214, 10), 14)
    stroke_text(d, (54, 480), "TRADING", font("Black", 120), (255, 255, 255), 10)
    im.alpha_composite(obj("money_bag", 330), (840, 40))
    im.alpha_composite(obj("racing_car", 230), (760, 400))
    badge(d, "21:37")
    return im


def guru3():                                        # "100% WIN RATE" on yellow/black, rising chart and fire
    im = bg((255, 200, 0), (255, 120, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((0, 470, 1280, 720), fill=(10, 10, 10))
    stroke_text(d, (640, 70), "THIS STRATEGY", font("Black", 110), (10, 10, 10), 0, "ma")
    stroke_text(d, (640, 220), "100% WIN RATE", font("Black", 150), (255, 255, 255), 14, "ma")
    chart(d, (80, 490, 860, 705), True, 28, 7, 0.05)
    im.alpha_composite(obj("fire", 240), (960, 440))
    badge(d, "9:58")
    return im


def guru4():                                        # "QUIT YOUR 9-5" on blue, laptop and flying money
    im = bg((0, 70, 200), (0, 20, 70), (300, 380, (0, 90, 160)))
    d = ImageDraw.Draw(im, "RGBA")
    stroke_text(d, (680, 90), "QUIT", font("Black", 170), (255, 255, 255), 12)
    stroke_text(d, (680, 270), "YOUR", font("Black", 120), (255, 255, 255), 10)
    stroke_text(d, (680, 400), "9-5", font("Black", 200), (255, 60, 60), 14)
    im.alpha_composite(obj("laptop", 330), (80, 260))
    im.alpha_composite(obj("money_with_wings", 220), (230, 40))
    badge(d, "18:04")
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    app_card()
    for i, g in enumerate((guru1, guru2, guru3, guru4), 1):
        g().convert("RGB").save(f"{OUT}/guru_{i}.png")
    print("ok")
