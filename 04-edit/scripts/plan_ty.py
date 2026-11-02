"""The thank-you edit: Jean's raw thank-you recording cut and dressed 1:1 like AB's thank-you video
(thank-you-vsl-reference/BREAKDOWN.md).

The raw take is 11:21 with retakes and long pauses. TAKES below is the take of each line that goes in (raw seconds);
everything else is cut, and pauses inside a take are trimmed to AB's pace (~0.15 s). Then every visual is anchored to
Jean's words in the cut (transcribed again after cutting, so the times are exact).

    python plan_ty.py cut                    # writes the cut list and the cut voice
    python transcribe.py CUT_VOICE.wav thank-you-edit/transcript_cut.json "<names>"
    python plan_ty.py plan thank-you-edit/edit.json
"""
import json, os, re, subprocess, sys
import numpy as np

FPS = 30
RAW = "/home/user/work/tyj/raw.mp4"
WORK = "/home/user/work/tyj"
REPO = "/home/user/jeanfx-vsl/thank-you-edit"


def islands():
    """Speech islands in the raw take: 10 ms RMS over -41 dBFS, gaps under 0.13 s closed, blips under 0.05 s dropped."""
    path = f"{REPO}/islands.json"
    if os.path.exists(path):
        return json.load(open(path))
    from scipy.ndimage import binary_closing, binary_opening
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", RAW, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = len(x) // 160
    db = 20 * np.log10(np.sqrt(np.mean(x[:n * 160].reshape(n, 160) ** 2, axis=1) + 1e-12))
    sp = binary_opening(binary_closing(db > -41, np.ones(13)), np.ones(5))
    idx = np.flatnonzero(np.diff(np.r_[0, sp.astype(int), 0]))
    out = [[round(a / 100, 2), round(b / 100, 2)] for a, b in zip(idx[::2], idx[1::2])]
    json.dump(out, open(path, "w"))
    return out


ISL = islands()

# ---------------------------------------------------------------- the takes that go in (raw seconds)
TAKES = [
    (3.55, 5.25),                  # Yo, what's up guys? It's Jean here.           (take 2 of 2)
    (10.85, 14.4),                 # I just wanted to thank you for filling out the application to the Elite Mentorship.
    (18.8, 22.5),                  # You have taken actions that 90% of the traders couldn't do.
    (39.0, 42.25),                 # And you're genuinely one step closer to changing your life around.   (take 2)
    (64.18, 67.05),                # Therefore, I want to take this extremely seriously.                   (take 3)
    (69.7, 77.75),                 # So you now have the opportunity to gain the consistency, profitability,
    (82.4, 83.45),                 # and that time,
    (88.4, 93.35),                 # location and financial freedom that you've always been dreaming about.
    (123.0, 125.8),                # There is countless other traders inside the Elite Mentorship.         (after 10 s of restarts)
    (130.5, 132.7),                # They have taken advantage of this opportunity,                         (take 2)
    (138.1, 140.45),               # so there's no reason why you can't as well.                           (take 2)
    (146.3, 147.62),               # So you might be wondering,                                            (take 2)
    (153.93, 157.7),               # what are the next steps to actually be part of the Elite Mentorship program?
    (162.22, 164.3),               # Well, as I speak to you right now,
    (170.77, 174.45),              # one of my best students is currently reviewing your application right now   (take 2)
    (179.62, 181.95),              # to see if you are a good fit to the program.
    (186.53, 189.45),              # And if you are, he will reach out to you personally.
    (193.22, 195.1),               # So make sure you have your phone in your hand,
    (215.97, 219.4),               # because you don't want to miss out on this call as it's super, super important.   (take 3)
    (223.4, 225.38),               # Now, I know what you're probably feeling right now.
    (229.83, 232.4),               # And I know that you're probably a little hesitant.
    (243.43, 246.72),              # And you're probably thinking, man, is this something that I can actually commit to?   (take 2)
    (252.1, 253.78),               # Will this really work out?
    (261.0, 261.66),               # Etc.                                                                   (take 2)
    (267.72, 269.7),               # And honestly, man, I totally get it.                                  (take 3)
    (273.76, 276.72),              # The odds are stacked against most people in trading.
    (293.33, 296.77),              # Especially right now online, where there's a ton of misinformation   (take 3)
    (304.8, 307.7),                # spread with trading gurus,
    (311.93, 314.8),               # constantly trying to push a course into your face,
    (321.1, 324.48),               # or trying to sell you a dream without actually mentoring you,         (take 2)
    (329.74, 332.0),               # holding you accountable and showing you
    (345.15, 347.34),              # every single part of the trading strategy.                            (the clean ending)
    (355.14, 358.3),               # And that is exactly why I built the Elite Mentorship.
    (366.6, 369.95),               # Because I know the difference that it makes when you have real guidance.   (take 2)
    (373.48, 375.67),              # Not just some sort of random strategy.
    (384.9, 386.03),               # But an actual mentorship
    (386.8, 388.12),               # and accountability.
    (406.03, 409.64),              # And the right psychology to bulletproof you against the ups and downs   (take 2)
    (417.56, 418.27),              # in trading.                                                           (take 3)
    (422.54, 425.09),              # And to be honest, you can probably figure out things on your own.
    (428.67, 431.26),              # But in reality, it will take you way longer.
    (436.54, 439.53),              # And you probably won't even get to where you want to be in trading.
    (442.68, 444.47),              # But however, on the flip side,
    (493.24, 497.21),              # you can cut the amount of time that it takes to consistently be profitable   (take 4)
    (519.84, 524.0),               # and prevent yourself from spending thousands of dollars on prop firm challenges.   (take 2)
    (531.2, 532.06),               # And instead,
    (537.2, 538.53),               # build the correct psychology
    (546.27, 548.24),              # that is needed to be a profitable day trader.                         (take 2)
    (567.89, 569.87),              # And if you're still wondering whether this works,                     (take 2)
    (576.2, 579.18),               # scroll down below this video and check out the testimonials          (take 3)
    (585.06, 588.48),              # from the members themselves inside the Elite Mentorship program.
    (591.9, 594.75),               # And remember, these are regular people, by the way.
    (600.25, 602.42),              # They are literally exactly like you.                                  (take 2)
    (606.42, 608.65),              # And these are just people that wanted more freedom,                   (take 2)
    (610.89, 611.78),              # more control,
    (613.5, 614.68),               # and more opportunity.
    (631.68, 635.67),              # And they were able to make this happen by learning the skill the right way.   (take 2)
    (640.9, 647.28),               # So if you want to join the JeanFX Elite Mentorship program and finally become a profitable day trader,
    (652.22, 654.45),              # be on the lookout for that call from my team.
    (664.15, 665.75),              # Thanks once again for applying.                                       (take 3)
    (668.55, 669.62),              # I will see you inside.
]
PRE, POST = 0.06, 0.09                                   # padding kept around each bit of speech


def keep_ranges():
    """Each take, minus any silence over ~0.15 s inside it (AB cuts his pauses out)."""
    out = []
    for a, b in TAKES:
        parts = [(max(a, x - PRE), min(b, y + POST)) for x, y in ISL if y > a and x < b]
        if not parts:
            parts = [(a, b)]
        for x, y in parts:
            if out and x <= out[-1][1] + 0.01:
                out[-1] = (out[-1][0], max(out[-1][1], y))
            else:
                out.append((x, y))
    return out


KEEP = keep_ranges()
KEEP_F = []
for a, b in KEEP:
    fa, fb = int(np.floor(a * FPS)), int(np.ceil(b * FPS))
    if KEEP_F and fa <= KEEP_F[-1][1]:
        KEEP_F[-1] = (KEEP_F[-1][0], max(KEEP_F[-1][1], fb))
    else:
        KEEP_F.append((fa, fb))
TOTAL = sum(b - a for a, b in KEEP_F) / FPS
JOINS = []                                               # output times of every jump cut
_acc = 0
for a, b in KEEP_F[:-1]:
    _acc += b - a
    JOINS.append(_acc / FPS)


def cut_voice(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", RAW, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    y = np.concatenate([x[a * 1600:b * 1600] for a, b in KEEP_F])
    import soundfile as sf
    sf.write(path, y, 48000)


if len(sys.argv) > 1 and sys.argv[1] == "cut":
    cut_voice(f"{WORK}/cut_voice.wav")
    print(f"{len(KEEP_F)} pieces, {TOTAL:.1f} s")
    sys.exit(0)

# ---------------------------------------------------------------- words (output time)
FIX = {"jin": "Jean", "genfx": "JeanFX", "gfx": "JeanFX", "genefx": "JeanFX", "jeanfx": "JeanFX"}
_t = json.load(open(f"{REPO}/transcript_cut.json"))
WORDS = []
for seg in _t:
    for x in seg["words"]:
        t = x["w"].strip()
        if not t:
            continue
        if WORDS and (t.startswith(",") or t.startswith("-") or t.startswith("%") or (t.startswith(".") and len(t) > 1)):
            WORDS[-1] = dict(WORDS[-1], w=WORDS[-1]["w"] + t, e=x["e"])
        else:
            WORDS.append(dict(w=t, s=x["s"], e=x["e"]))


def norm(s):
    return re.sub(r"[^a-z0-9$%]", "", s.lower())


# what Whisper misheard in the cut (checked against the takes one by one)
PFIX = [("genuinely want to step", "genuinely one step"), ("actual mentality", "actual mentorship"),
        ("the rights encourage you", "the right psychology"), ("can count the", "can cut the"),
        ("pro-form challenges", "prop firm challenges"), ("JunFX", "JeanFX"), ("ETC,", "Etc."),
        ("for Dark Call on my team", "for that call from my team"), ("of that trading", "of the trading")]


def _fix(old, new):
    ot = [norm(t) for t in old.split()]
    for i in range(len(WORDS) - len(ot) + 1):
        if [norm(x["w"]) for x in WORDS[i:i + len(ot)]] == ot:
            src = WORDS[i:i + len(ot)]
            nw = new.split()
            rep = []
            for k, w in enumerate(nw):
                a = src[min(k, len(src) - 1)]
                rep.append(dict(w=w, s=a["s"], e=a["e"]))
            rep[-1]["e"] = src[-1]["e"]
            WORDS[i:i + len(ot)] = rep
            return
    raise KeyError(old)


for _o, _n in PFIX:
    _fix(_o, _n)
NW = [norm(x["w"]) for x in WORDS]


def ph(phrase, after=0.0):
    toks = [norm(t) for t in phrase.split()]
    for i in range(len(WORDS) - len(toks) + 1):
        if WORDS[i]["s"] < after - 1e-6:
            continue
        if NW[i:i + len(toks)] == toks:
            return i, i + len(toks) - 1
    raise KeyError(f"phrase not found after {after}: {phrase}")


def s(phrase, after=0.0):
    return WORDS[ph(phrase, after)[0]]["s"]


def e(phrase, after=0.0):
    return WORDS[ph(phrase, after)[1]]["e"]


def words(phrase, after=0.0, text=None):
    """[{w, t}] for the words of a phrase, as they should read on screen."""
    i, j = ph(phrase, after)
    shown = (text or phrase).split()
    src = WORDS[i:j + 1]
    if len(shown) == len(src):
        return [{"w": w, "t": round(x["s"], 3)} for w, x in zip(shown, src)]
    # different word count on screen: spread them over the spoken span
    t0, t1 = src[0]["s"], src[-1]["s"]
    return [{"w": w, "t": round(t0 + (t1 - t0) * k / max(1, len(shown) - 1), 3)} for k, w in enumerate(shown)]


# ---------------------------------------------------------------- building blocks
EL, SFX, ZOOM = [], [], []
GRAPHICS = []          # (t0, t1) windows when a full-screen graphic is up (no face)
NOCAP = []             # windows with no captions (text cards)


def add(**d):
    EL.append(d)
    return d


def sfx(name, t, db=-20, lead=0.0):
    SFX.append({"name": name, "t": round(t, 3), "db": db, "lead": lead})


def leak(t, on_face=False, seed=None):
    """AB's light-leak flash centred on a switch (~0.33 s), with the airy shimmer starting with it."""
    add(type="leak", t0=round(t - 0.16, 3), t1=round(t + 0.18, 3), soft=on_face, seed=seed if seed is not None else int(t * 7) % 97)
    sfx("shimmer", t - 0.14, -9)


def green(a, b, palette="green"):
    add(type="gradplate", t0=round(a, 3), t1=round(b, 3), palette=palette, z=10)
    GRAPHICS.append((a, b))


def card_text(a, b, lines):
    """A text card's lines: [(words, size, baseline y)], each word rising in on its own time."""
    add(type="wordcap", t0=round(a, 3), t1=round(b, 3), z=84,
        lines=[{"words": w, "size": size, "y": y, "track": -3 if size < 120 else -5} for w, size, y in lines])


def graphic(a, b, caps=False, palette="green", leak_in=True, leak_out=True):
    """A full-screen graphic from a to b with light leaks on both switches."""
    green(a, b, palette)
    if not caps:
        NOCAP.append((a, b))
    if leak_in:
        leak(a, False)
    if leak_out:
        leak(b, False)


def zoom(t, z, cx=960, cy=455, dur=0.3, ease="out", drift=0.0):
    ZOOM.append({"t": round(t, 3), "z": z, "cx": cx, "cy": cy, "dur": dur, "ease": ease, "drift": drift})




def staircases():
    """AB's zoom on the face: hold, step in ~10-15% (0.3 s ease), hold, step... every 1.5-3 s up to ~1.45x, then back to
    wide on a light-leak flash and climb again. Steps land on the jump cuts where possible (it hides them)."""
    face, t = [], 0.0
    for a, b in sorted(GRAPHICS):
        if a - t > 0.3:
            face.append((t, a))
        t = max(t, b)
    if TOTAL - t > 0.3:
        face.append((t, TOTAL))
    incs = [0.08, 0.10, 0.06, 0.09, 0.12, 0.07]
    starts = [w["s"] for w in WORDS]
    for n, (a, b) in enumerate(face):
        if n == 0:                                       # the first shot opens tight and pulls out
            zoom(0.0, 1.6, ease="cut")
            zoom(0.05, 1.0, dur=0.6, ease="inout")
        else:
            zoom(a, 1.0, ease="cut")
        z, last, k = 1.0, a + (0.6 if n == 0 else 0.0), 0
        while True:
            lo, hi = last + 1.5, last + 3.0
            if hi > b - 0.6 and lo > b - 0.8:
                break
            joins = [j for j in JOINS if lo <= j <= min(hi, b - 0.6)]
            if joins:
                t = joins[0]
            else:
                cand = [x for x in starts if last + 2.2 <= x <= min(hi, b - 0.6)]
                if not cand:
                    break
                t = cand[0]
            nz = z + incs[k % len(incs)]
            k += 1
            if nz > 1.46:                                # top of the staircase: reset to wide on a flash
                leak(t, on_face=True)
                zoom(t, 1.0, ease="cut")
                z = 1.0
            else:
                zoom(t, round(nz, 3), dur=0.3)
                z = nz
            last = t


def captions():
    """Captions: 1-4 words, laid out at full width, each word rising in on the word; next caption replaces the last
    when the phrase ends. Off on the text cards."""
    def hidden(t):
        return any(a - 0.02 <= t < b for a, b in NOCAP)

    seq = []
    for w in WORDS:
        txt = re.sub(r"^[.,!?;:\"]+|[.,!?;:\"]+$", "", w["w"]).strip()
        low = norm(txt)
        if low in FIX:
            txt = FIX[low]
        if not txt or hidden(w["s"]):
            seq.append(None)
            continue
        seq.append(dict(w=txt, s=w["s"], e=w["e"], end=bool(re.search(r"[.,!?]$", w["w"]))))
    groups, cur = [], []
    for i, wd in enumerate(seq):
        if wd is None:
            if cur:
                groups.append(cur)
                cur = []
            continue
        if cur:
            chars = sum(len(x["w"]) + 1 for x in cur) + len(wd["w"])
            gap = wd["s"] - cur[-1]["e"]
            if (len(cur) >= 4 or chars > 17 or gap > 0.3 or cur[-1]["end"] or
                    (len(cur) >= 2 and norm(wd["w"]) in ("and", "but", "because", "so", "that", "to", "or", "which", "when", "where"))):
                groups.append(cur)
                cur = []
        cur.append(wd)
    if cur:
        groups.append(cur)
    for gi, g in enumerate(groups):
        t0 = g[0]["s"]
        nxt = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else 1e9
        t1 = min(nxt, g[-1]["e"] + 0.5)
        for a, b in NOCAP:                              # never over a text card
            if t0 < a < t1:
                t1 = a
        if g[0]["w"][:1].islower() and gi == 0:
            g[0]["w"] = g[0]["w"][:1].upper() + g[0]["w"][1:]
        add(type="wordcap", t0=round(t0, 3), t1=round(t1, 3), z=86,
            lines=[{"words": [{"w": x["w"], "t": round(x["s"], 3)} for x in g], "size": 83, "y": 1023, "track": -3}])


def cap_icon(phrase, icon, after=0.0, size=130):
    t = s(phrase, after)
    add(type="lineicon", t0=round(t, 3), t1=round(e(phrase, after) + 0.5, 3), icon=icon, cx=960, cy=905, size=size, z=87)


# ---------------------------------------------------------------- the edit: AB's beats, on Jean's words
WALL = ["crop/wall_18.07.30.png", "crop/wall_18.06.18.png", "crop/wall_18.07.37.png", "crop/wall_18.06.52.png",
        "crop/wall_18.08.02.png", "crop/wall_18.10.55.png", "crop/wall_18.11.10.png", "crop/wall_18.11.16.png",
        "crop/wall_18.07.14.png", "crop/wall_18.10.04.png", "crop/wall_18.08.13.png", "crop/wall_18.07.47.png",
        "crop/wall_18.08.45.png", "crop/wall_18.09.13.png"]
END = WORDS[-1]["e"]


def until(phrase, after=0.0, pad=0.05):
    return s(phrase, after) - pad


def beats():
    # 0:00 face, opens tight and pulls out (staircases() does the zoom); captions
    # "that 90% of the traders couldn't do": green card, headline + sub-line
    a, b = s("that 90%") - 0.1, until("and you genuinely")
    graphic(a, b)
    card_text(a, b, [(words("that 90%", a, text="That 90%"), 170, 450), (words("of the traders couldn't do", a), 72, 540)])
    # "the consistency, profitability, and that time, location and financial freedom": list card, then three icons
    a, mid, b = s("consistency") - 0.15, until("and that time"), until("that you've always")
    graphic(a, b)
    card_text(a, mid, [(words("consistency", a, text="Consistency"), 94, 528), (words("profitability", a, text="Profitability"), 94, 630)])
    leak(mid)
    for k, (w, ic, lb) in enumerate([("time", "time", "Time"), ("location", "location", "Location"), ("freedom", "freedom", "Freedom")]):
        add(type="iconcircle", t0=round(s(w, mid) - 0.04, 3), t1=round(b, 3), icon=ic, label=lb, cx=504 + 456 * k, cy=525)
    # "there's countless other traders inside the Elite Mentorship that have taken advantage of this opportunity":
    # testimonial posts sliding left on the green plate, captions on top
    a, b = s("there's countless") - 0.08, until("so there's no reason")
    graphic(a, b, caps=True)
    add(type="carousel", t0=round(a, 3), t1=round(b, 3), imgs=WALL[:9], h=560, x0=60, travel=round(520 * (b - a)), cy=470,
        z=40, seed=4)
    # "what are the next steps to actually be part of the Elite Mentorship program?": four lines building
    a, b = s("what are the next") - 0.1, until("well as i speak")
    graphic(a, b)
    card_text(a, b, [(words("what are the", a, text="What are the"), 88, 400), (words("next steps to actually", a), 88, 496),
                     (words("be part of the", a), 88, 592), (words("elite mentorship program", a, text="Elite Mentorship program?"), 88, 688)])
    # "is currently reviewing your application": the application page as a white card, blurred, scaling up
    a, b = s("is currently reviewing") - 0.05, until("and if you are")
    graphic(a, b, caps=True)
    add(type="zoomcard", t0=round(a, 3), t1=round(b, 3), img="ty/app_card.png", w=1460, blur=7, radius=40, cx=952, cy=540,
        **{"from": [960, 540]}, s0=0.06, dur=0.6, z=60)
    # face: phone in hand and the call get a small line icon over the caption
    cap_icon("your phone in your hand", "phone", 46)
    cap_icon("this call", "phone_ring", 46)
    # "is this something that I can actually commit to? Will this really work out?": two lines, the second bigger
    a, b = s("is this something") - 0.1, until("etc")
    graphic(a, b)
    card_text(a, b, [(words("is this something that i can actually commit to", a, text="Is this something that I can actually commit to?"), 64, 515),
                     (words("will this really work out", a, text="Will this really work out?"), 104, 632)])
    # "the odds are stacked against most people in trading": the red card with the falling line
    a, b = s("the odds are stacked") - 0.1, until("especially right now")
    graphic(a, b, palette="red")
    add(type="jagline", t0=round(a, 3), t1=round(b, 3), dur=1.1, z=30)
    card_text(a, b, [(words("the odds are stacked", a, text="The odds are Stacked"), 100, 515),
                     (words("against most people in trading", a, text="Against Most People In Trading"), 100, 618)])
    # "with trading gurus": four guru thumbnails one after another, captions on
    a, b = s("with trading gurus") - 0.05, until("constantly trying", pad=0.06)
    graphic(a, b, caps=True, leak_out=False)
    add(type="seq", t0=round(a, 3), t1=round(b, 3), imgs=[f"ty/guru_{k}.png" for k in (1, 2, 3, 4)], w=1230,
        each=round(min(0.6, max(0.25, (b - a) / 4)), 3), cx=960, cy=500, z=60)
    # "constantly trying to push a course into your face": two lines
    a, b = s("constantly trying") - 0.06, until("or trying to sell")
    graphic(a, b, leak_in=True)
    card_text(a, b, [(words("constantly trying to push", a, text="Constantly trying to push"), 94, 520),
                     (words("a course into your face", a), 94, 622)])
    # "to bulletproof you against the ups and downs in trading": shield icon over two lines
    a, b = s("to bulletproof you") - 0.06, until("and to be honest")
    graphic(a, b)
    add(type="lineicon", t0=round(a + 0.05, 3), t1=round(b, 3), icon="shield", cx=960, cy=400, size=170, z=81)
    card_text(a, b, [(words("to bulletproof you", a, text="To Bulletproof You"), 86, 560),
                     (words("against the ups and downs in trading", a), 86, 650)])
    # "scroll down below this video and check out the testimonials from the members themselves inside the Elite
    # Mentorship program": the shot shrinks into a card and slides up off the top over a wall of posts scrolling up,
    # then the title builds over the wall
    a, b = s("scroll down below") - 0.05, until("and remember these")
    green(a, b)
    add(type="wallup", t0=round(a, 3), t1=round(b + 0.4, 3), imgs=WALL + WALL[:4], cols=3, card_w=520, y_start=1150,
        y_end=-1500, ease=False, z=15, seed=6)
    add(type="shrinkup", t0=round(a, 3), t1=round(a + 2.0, 3), shrink=0.6, hold=0.55, slide=0.7, scale=0.52, cy=492, z=70)
    zoom(a, 1.0, dur=0.55, ease="inout")
    ti = s("inside the elite mentorship", a) - 0.05
    card_text(ti, b, [(words("inside the", ti, text="Inside the"), 94, 795), (words("elite mentorship", ti, text="Elite Mentorship"), 94, 885)])
    NOCAP.append((ti, b))
    leak(b)
    # "be on the lookout for that call from my team": ringing phone over two lines
    a, b = s("be on the lookout") - 0.06, until("thanks once again")
    graphic(a, b)
    add(type="lineicon", t0=round(a + 0.05, 3), t1=round(b, 3), icon="phone_ring", cx=960, cy=400, size=170, z=81)
    card_text(a, b, [(words("be on the lookout", a, text="Be on the lookout"), 88, 560),
                     (words("for that call from my team", a), 88, 650)])
    # "Thanks once again for applying. I will see you inside." face, ends on the last word


def main():
    out = sys.argv[2]
    beats()
    staircases()
    captions()
    edit = {"raw": RAW, "raw_fps_fix": True, "total": round(TOTAL, 3), "keep_frames": KEEP_F, "elements": EL,
            "sfx": sorted(SFX, key=lambda x: x["t"]), "zoom": sorted(ZOOM, key=lambda x: x["t"]),
            "music": "pad", "music_under_lu": 18.0, "music_lift": {"t": round(TOTAL - 40, 2), "db": 3.5, "ramp": 6.0},
            "music_end": round(END, 3), "sfx_gain_db": 0.0,
            "takes_raw": [[round(a, 3), round(b, 3)] for a, b in TAKES]}
    json.dump(edit, open(out, "w"), indent=0)
    n_cap = sum(1 for d in EL if d["type"] == "wordcap" and d.get("z") == 86)
    n_leak = sum(1 for d in EL if d["type"] == "leak")
    print(f"total {TOTAL:.1f}s, {len(EL)} elements, {n_cap} captions, {n_leak} light leaks, {len(ZOOM)} zoom moves")


if __name__ == "__main__":
    main()
