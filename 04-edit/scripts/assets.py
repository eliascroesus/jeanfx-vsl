"""Still assets for Jean's AB-style edit, built from the uploads in 02-results-and-b-roll/ (certificates cropped out
of the Discord screenshots) plus a few drawn ones (blurred candle chart, signal card, phone mockup, "account breached"
email, 3D objects recoloured like AB's).

    python assets.py OUT_DIR
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

RES = "/home/user/jeanfx-vsl/02-results-and-b-roll"
FLUENT = "/home/user/work/assets/fluent"
FD = "/usr/share/fonts/opentype/inter"


def shot(t):
    return f"{RES}/Screenshot 2026-10-20 at {t}.png"


# certificate crops: name -> (file, (x0, y0, x1, y1) as fractions of the screenshot)
CROPS = {
    "topstep_19770": (shot("18.09.04"), (0.058, 0.245, 0.322, 0.865)),
    "topstep_email": (shot("18.09.04"), (0.330, 0.245, 0.585, 0.865)),
    "ftmo_26915": (shot("18.08.37"), (0.097, 0.18, 0.415, 0.79)),
    "ftmo_16133": (shot("18.08.37"), (0.425, 0.18, 0.745, 0.79)),
    "alpha_4956": (shot("18.09.24"), (0.125, 0.117, 0.957, 0.888)),
    "bt_withdrawal_2291": (shot("18.11.36"), (0.070, 0.233, 0.336, 0.896)),
    "bt_funded": (shot("18.11.52"), (0.069, 0.207, 0.313, 0.874)),
    "alphatrader_phase1": (shot("18.12.03"), (0.110, 0.262, 0.870, 0.895)),
    "tradex_funded": (shot("18.11.45"), (0.064, 0.200, 0.500, 0.900)),
    "tradex_724": (shot("18.11.24"), (0.425, 0.550, 0.603, 0.905)),
    "ftmo_passed": (shot("18.10.40"), (0.094, 0.147, 0.940, 0.877)),
    "lucid_alpha": (shot("18.09.41"), (0.090, 0.195, 0.856, 0.885)),
    "equityedge_funded": (shot("18.07.04"), (0.096, 0.154, 0.884, 0.900)),
    "desmond_341": (shot("18.07.14"), (0.115, 0.110, 0.935, 0.900)),
    "desmond_277": (shot("18.07.47"), (0.090, 0.130, 0.990, 0.890)),
    "desmond_580": (shot("18.08.13"), (0.100, 0.092, 0.997, 0.530)),
    "desmond_phases": (shot("18.08.13"), (0.115, 0.580, 0.920, 0.930)),
    "desmond_92": (shot("18.08.26"), (0.0625, 0.180, 0.540, 0.866)),
    "desmond_162": (shot("18.08.45"), (0.104, 0.200, 0.995, 0.900)),
    "desmond_406": (shot("18.09.13"), (0.091, 0.104, 0.800, 0.800)),
    "lawrence_6196": (shot("18.10.04"), (0.078, 0.090, 0.5625, 0.877)),
    "kibron_17475": (f"{RES}/IMG_3409.jpeg", (0, 0, 1, 1)),
    "kibron_10028": (f"{RES}/IMG_3410.jpeg", (0, 0, 1, 1)),
    "kibron_7446": (f"{RES}/IMG_3411.jpeg", (0, 0, 1, 1)),
    "equityedge_1680": (f"{RES}/IMG_9100.PNG", (0, 0, 1, 1)),
    "equityedge_email": (f"{RES}/IMG_9099.PNG", (0, 0, 1, 1)),
    "us30_chart": (f"{RES}/IMG_9231.PNG", (0, 0, 1, 1)),
    "us30_pos": (f"{RES}/IMG_9230.PNG", (0, 0, 1, 0.36)),
    "eurusd_chart": (f"{RES}/IMG_9272.PNG", (0, 0, 1, 1)),
    "eurusd_pos": (f"{RES}/IMG_9273.PNG", (0, 0, 1, 0.36)),
    "ftmo_account": (f"{RES}/IMG_9232.PNG", (0, 0, 1, 1)),
}
# whole Discord posts for the "ask them yourself" wall (people thanking Jean)
WALL = ["18.07.30", "18.08.13", "18.07.47", "18.11.10", "18.06.52", "18.08.45", "18.07.14", "18.09.13", "18.10.04",
        "18.07.37", "18.10.55", "18.11.16", "18.06.18", "18.08.02"]


def open_any(p):
    import pillow_heif
    pillow_heif.register_heif_opener()
    return ImageOps.exif_transpose(Image.open(p)).convert("RGB")


def crops(out):
    os.makedirs(f"{out}/crop", exist_ok=True)
    for name, (p, (x0, y0, x1, y1)) in CROPS.items():
        im = open_any(p)
        w, h = im.size
        im.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h))).save(f"{out}/crop/{name}.png")
    for t in WALL:
        open_any(shot(t)).save(f"{out}/crop/wall_{t}.png")


def candle_bg(out, seed=7, w=1920, h=1080):
    """AB's name-card background: a dark, heavily blurred red/green candlestick chart."""
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (w, h), (8, 10, 14))
    d = ImageDraw.Draw(im)
    n, p = 46, 0.0
    ys = []
    for i in range(n):
        p += r.normal(0.6, 3.2)
        ys.append(p)
    ys = np.array(ys)
    ys = (ys - ys.min()) / (ys.max() - ys.min() + 1e-9)
    cw = w / n
    prev = ys[0]
    for i, v in enumerate(ys):
        o, c = prev, v
        hi, lo = max(o, c) + abs(r.normal(0, 0.03)), min(o, c) - abs(r.normal(0, 0.03))
        Y = lambda q: h * 0.9 - q * h * 0.72
        col = (40, 200, 90) if c >= o else (230, 60, 50)
        x = i * cw + cw / 2
        d.line([(x, Y(hi)), (x, Y(lo))], fill=col, width=4)
        d.rectangle([x - cw * 0.3, Y(max(o, c)), x + cw * 0.3, Y(min(o, c)) + 3], fill=col)
        prev = c
    # moving average line
    ma = np.convolve(ys, np.ones(6) / 6, "same")
    d.line([(i * cw + cw / 2, h * 0.9 - v * h * 0.72) for i, v in enumerate(ma)], fill=(40, 170, 90), width=6)
    im = im.filter(ImageFilter.GaussianBlur(22))
    a = np.asarray(im, np.float32) * 0.95
    yy, xx = np.mgrid[0:h, 0:w]
    vig = 1 - 0.55 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
    Image.fromarray(np.clip(a * vig[..., None], 0, 255).astype(np.uint8)).save(f"{out}/candle_bg.png")


def font(name, size):
    return ImageFont.truetype(f"{FD}/{name}", size)


def signal_card(out):
    """A copy-paste 'signal group' message (AB shows a tilted Telegram signal)."""
    W_, H_ = 620, 760
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), 34, fill=(255, 255, 255, 255))
    y = 40
    lines = [("VIP SIGNALS 🚀".replace("🚀", ""), "InterDisplay-Bold.otf", 40, (20, 20, 24)),
             ("XAUUSD  BUY NOW", "InterDisplay-Bold.otf", 46, (20, 20, 24)),
             ("Entry: 2385 - 2382", "InterDisplay-Medium.otf", 36, (40, 40, 46)),
             ("", None, 20, None),
             ("TP1: 2390", "InterDisplay-Medium.otf", 36, (24, 150, 70)),
             ("TP2: 2395", "InterDisplay-Medium.otf", 36, (24, 150, 70)),
             ("TP3: 2405", "InterDisplay-Medium.otf", 36, (24, 150, 70)),
             ("", None, 20, None),
             ("SL: 2375", "InterDisplay-Medium.otf", 36, (220, 50, 50)),
             ("", None, 20, None),
             ("Use proper risk management ⚠", "InterDisplay-Regular.otf", 30, (110, 110, 118)),
             ("👍 214   🔥 98", "InterDisplay-Regular.otf", 30, (110, 110, 118))]
    for text, f, s, col in lines:
        if f:
            d.text((44, y), text.replace("⚠", "!").replace("👍", "+").replace("🔥", "+"), font=font(f, s), fill=col)
        y += s + 22
    im.save(f"{out}/signal_card.png")


def phone_mockup(out, src="us30_chart"):
    """A phone frame around one of Jean's chart screenshots (AB's 'or an indicator' phone)."""
    scr = Image.open(f"{out}/crop/{src}.png").convert("RGB")
    sw, sh = 520, int(520 * scr.height / scr.width)
    scr = scr.resize((sw, sh), Image.LANCZOS)
    bez = 22
    W_, H_ = sw + 2 * bez, sh + 2 * bez
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), 78, fill=(30, 30, 34, 255), outline=(150, 150, 160, 255), width=4)
    m = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, sh - 1), 60, fill=255)
    im.paste(scr, (bez, bez), m)
    d.rounded_rectangle((W_ / 2 - 80, bez + 14, W_ / 2 + 80, bez + 50), 18, fill=(0, 0, 0, 255))
    im.save(f"{out}/phone_{src}.png")


def breached_email(out):
    """'Account breached' email, as an iPhone notification card (the email that lands one bad day later)."""
    W_, H_ = 1100, 250
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), 44, fill=(245, 245, 247, 245))
    d.rounded_rectangle((36, 40, 136, 140), 24, fill=(234, 67, 53, 255))
    d.text((62, 52), "M", font=font("InterDisplay-Bold.otf", 66), fill=(255, 255, 255))
    d.text((170, 40), "MAIL", font=font("InterDisplay-SemiBold.otf", 30), fill=(120, 120, 128))
    d.text((W_ - 140, 40), "now", font=font("InterDisplay-Regular.otf", 30), fill=(120, 120, 128))
    d.text((170, 84), "Account Breached", font=font("InterDisplay-Bold.otf", 50), fill=(20, 20, 24))
    d.text((170, 150), "Your funded account has violated the daily", font=font("InterDisplay-Regular.otf", 36), fill=(70, 70, 76))
    d.text((170, 194), "loss limit and has been closed.", font=font("InterDisplay-Regular.otf", 36), fill=(70, 70, 76))
    im.save(f"{out}/breached.png")


def xray_brain(out):
    """AB's glowing blue brain: the 3D brain recoloured to a blue X-ray look."""
    b = Image.open(f"{FLUENT}/brain_3d.png").convert("RGBA").resize((760, 760), Image.LANCZOS)
    a = np.asarray(b, np.float32)
    lum = a[..., :3].mean(2) / 255.0
    edges = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES), np.float32) / 255
    v = np.clip(0.25 + lum * 0.9 + edges * 2.5, 0, 1)
    rgb = np.stack([v * 40, v * 120 + 30, v * 255], -1)
    out_a = np.concatenate([rgb, a[..., 3:4]], -1)
    im = Image.fromarray(np.clip(out_a, 0, 255).astype(np.uint8), "RGBA")
    glow = im.filter(ImageFilter.GaussianBlur(26))
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    canvas.alpha_composite(glow)
    canvas.alpha_composite(im)
    canvas.save(f"{out}/brain_xray.png")


def big_3d(out):
    """The 3D objects at the size AB uses them (upscaled smoothly, with a little sharpening)."""
    for n in ["trophy", "alarm_clock", "magnifying_glass_tilted_left", "coin", "money_bag", "chart_decreasing",
              "delivery_truck", "package", "graduation_cap", "fire", "dollar_banknote", "money_with_wings",
              "stopwatch", "face_with_spiral_eyes", "warning", "racing_car", "bullseye", "laptop", "mobile_phone",
              "thinking_face", "check_mark_button", "cross_mark", "chart_increasing", "calendar", "man", "old_man", "airplane"]:
        p = f"{FLUENT}/{n}_3d.png"
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA").resize((640, 640), Image.LANCZOS)
            im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
            im.save(f"{out}/obj_{n}.png")


def gen_post(out, gen="/home/user/work/gen"):
    """Cut-outs from the generated stills: the bill (cropped to the note and tinted the green-beige of a real one) and
    the trophy (white background keyed out)."""
    for side in ("front", "back"):
        p = f"{gen}/bill_{side}.png"
        if not os.path.exists(p):
            continue
        a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
        m = a.mean(2) < 235
        ys, xs = np.where(m)
        y0, y1 = np.percentile(ys, [1, 99]).astype(int)
        x0, x1 = np.percentile(xs, [1, 99]).astype(int)
        c = a[y0:y1, x0:x1]
        lum = c.mean(2, keepdims=True)
        tint = np.array([0.86, 1.0, 0.86]) * lum * 0.92 + np.array([18, 26, 12])
        im = Image.fromarray(np.clip(tint * 0.85 + c * 0.15, 0, 255).astype(np.uint8)).resize((1200, 510), Image.LANCZOS)
        im.putalpha(255)
        im.save(f"{gen}/bill_{side}_cut.png")
    from PIL import ImageEnhance, ImageOps as IO
    for n in ("money_fan", "cash_counter", "money_pile"):
        p = f"{gen}/{n}.png"
        if os.path.exists(p):
            im = IO.autocontrast(Image.open(p).convert("RGB"), cutoff=1)
            im = ImageEnhance.Color(im).enhance(1.7)
            a = np.asarray(im, np.float32) * np.array([1.04, 1.03, 0.92])
            Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(f"{gen}/{n}_g.png")
    p = f"{gen}/trophy_white.png"
    if os.path.exists(p):
        a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
        dist = 255 - a.min(2)
        alpha = np.clip((dist - 18) / 40, 0, 1)
        im = Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")
        im.save(f"{gen}/trophy_cut.png")


def review_bubble(out):
    """The chat bubble that pops up next to the marked chart: the mistake and the fix, caught the same day."""
    W_, H_ = 640, 250
    im = Image.new("RGBA", (W_ + 60, H_ + 60), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, 30 + W_, 40 + H_), 36, fill=90)
    im.putalpha(sh.filter(ImageFilter.GaussianBlur(16)))
    card = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, W_ - 1, H_ - 1), 36, fill=(255, 255, 255, 255), outline=(225, 225, 230, 255), width=2)
    d.ellipse((34, 40, 84, 90), fill=(242, 54, 69))
    d.line([(48, 54), (70, 76)], fill=(255, 255, 255), width=6)
    d.line([(70, 54), (48, 76)], fill=(255, 255, 255), width=6)
    d.text((108, 40), "Entered before the sweep", font=font("InterDisplay-SemiBold.otf", 40), fill=(20, 20, 24))
    d.ellipse((34, 150, 84, 200), fill=(8, 153, 129))
    d.line([(46, 176), (56, 188)], fill=(255, 255, 255), width=6)
    d.line([(56, 188), (74, 162)], fill=(255, 255, 255), width=6)
    d.text((108, 150), "Wait for the CHoCH", font=font("InterDisplay-SemiBold.otf", 40), fill=(20, 20, 24))
    d.text((108, 104), "caught today, not 3 days later", font=font("InterDisplay-Medium.otf", 28), fill=(120, 120, 128))
    im.alpha_composite(card, (30, 30))
    im.save(f"{out}/review_bubble.png")


def rule(out):
    im = Image.new("RGBA", (460, 4), (255, 255, 255, 140))
    im.save(f"{out}/rule.png")


def main():
    out = sys.argv[1]
    rule(out)
    review_bubble(out)
    gen_post(out)
    os.makedirs(out, exist_ok=True)
    crops(out)
    candle_bg(out)
    signal_card(out)
    phone_mockup(out, "us30_chart")
    breached_email(out)
    xray_brain(out)
    big_3d(out)
    print("assets in", out)


if __name__ == "__main__":
    main()
