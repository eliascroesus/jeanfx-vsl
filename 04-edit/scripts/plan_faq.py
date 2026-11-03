"""The FAQ videos: each raw FAQ recording cut to its best takes and dressed exactly like the thank-you video v2
(thank-you-edit/README.md): the 3D money set behind every graphic, wide caps blurring in word by word with the neon
accent, handwritten lines, glass icon tiles, screens and result screenshots in glowing frames, word-by-word captions,
light-leak flashes with the shimmer, and push-in / pull-out zooms on the key words. No music (asked for).

    python plan_faq.py KEY cut                  # KEY = 0321, 0322, 0323, 0324 (the camera's clip number)
    python transcribe.py CUT_VOICE.wav faq-edit/KEY/transcript_cut.json "<names>"
    python plan_faq.py KEY plan faq-edit/KEY/edit.json
"""
import json, os, re, subprocess, sys
import numpy as np

from faq_videos import VIDEOS

KEY, MODE = sys.argv[1], sys.argv[2]
FPS = 30
RAW = f"/home/user/work/faq/raw/{VIDEOS[KEY]['file']}"
WORK = f"/home/user/work/faq/{KEY}"
REPO = f"/home/user/jeanfx-vsl/faq-edit/{KEY}"
os.makedirs(WORK, exist_ok=True)
os.makedirs(REPO, exist_ok=True)


def islands():
    """Speech islands in the raw clip (10 ms RMS 9 dB over the room's noise floor), cached in faq-edit/KEY/islands.json."""
    path = f"{REPO}/islands.json"
    if os.path.exists(path):
        return json.load(open(path))
    from scipy.ndimage import binary_closing, binary_opening
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", RAW, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = len(x) // 160
    db = 20 * np.log10(np.sqrt(np.mean(x[:n * 160].reshape(n, 160) ** 2, axis=1) + 1e-12))
    sp = binary_opening(binary_closing(db > np.percentile(db, 20) + 9, np.ones(13)), np.ones(5))
    idx = np.flatnonzero(np.diff(np.r_[0, sp.astype(int), 0]))
    out = [[round(a / 100, 2), round(b / 100, 2)] for a, b in zip(idx[::2], idx[1::2])]
    json.dump(out, open(path, "w"))
    return out


ISL = islands()
TAKES = VIDEOS[KEY]["takes"]
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


if MODE == "cut":
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
        if WORDS and (t.startswith(",") or t.startswith("-") or t.startswith("%") or t.startswith("&") or (t.startswith(".") and len(t) > 1)):
            WORDS[-1] = dict(WORDS[-1], w=WORDS[-1]["w"] + t, e=x["e"])
        else:
            WORDS.append(dict(w=t, s=x["s"], e=x["e"]))


def norm(s):
    return re.sub(r"[^a-z0-9$%]", "", s.lower())


PFIX = VIDEOS[KEY].get("pfix", [])


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
    print("PFIX not found:", old)


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


SCENES = [0]


def scene(a, b, palette="green", text_at=(960, 520), dark=0.55, glow=(1700, 120)):
    """The 3D money set behind a graphic (ty_design.Scene), each one on its own slice of the money clip."""
    SCENES[0] += 1
    add(type="scene", t0=round(a, 3), t1=round(b, 3), palette=palette, off=round((SCENES[0] * 5.3) % 13, 2), text_at=list(text_at),
        dark=dark, glow=list(glow), z=10)
    GRAPHICS.append((a, b))


def title(a, b, lines, **kw):
    """Wide-caps text, word by word on the word: lines = [(words, size, baseline y, options)]."""
    add(type="title", t0=round(a, 3), t1=round(b, 3), z=84,
        lines=[dict({"words": w, "size": size, "y": y}, **(o or {})) for w, size, y, o in lines], **kw)


def graphic(a, b, caps=False, palette="green", leak_in=True, leak_out=True, **kw):
    """A full-screen graphic from a to b with light leaks on both switches."""
    scene(a, b, palette, **kw)
    if not caps:
        NOCAP.append((a, b))
    if leak_in:
        leak(a, False)
    if leak_out:
        leak(b, False)


def zoom(t, z, cx=960, cy=430, dur=0.45, ease="out", drift=0.0):
    ZOOM.append({"t": round(t, 3), "z": z, "cx": cx, "cy": cy, "dur": dur, "ease": ease, "drift": drift})


ZOOM_CUES = []          # filled per video before zooms() runs


def face_windows():
    face, t = [], 0.0
    for a, b in sorted(GRAPHICS):
        if a - t > 0.3:
            face.append((t, a))
        t = max(t, b)
    if TOTAL - t > 0.3:
        face.append((t, TOTAL))
    return face


def zooms():
    """Push in on the cue word (0.45 s ease-out), pull back out on the next phrase (on the jump cut if there is one,
    otherwise a 0.5 s ease), never two pushes in a row. Every face shot after a graphic starts wide."""
    cues = []
    for ph_, v in ZOOM_CUES:
        toks = ph_.split()
        try:
            i, _ = ph(ph_)
        except KeyError:
            print("zoom cue not found:", ph_)
            continue
        cues.append((WORDS[i]["s"], v))
    cues.sort()
    for n, (a, b) in enumerate(face_windows()):
        if n == 0:
            zoom(0.0, 1.12, ease="cut")                      # opens a touch tight and settles out (AB)
            zoom(0.05, 1.0, dur=0.8, ease="inout")
        else:
            zoom(a, 1.0, ease="cut")
        state = 1.0
        for t, v in cues:
            if not (a + 0.35 <= t <= b - 0.35):
                continue
            if v == "out":
                if state == 1.0:
                    continue
                j = [x for x in JOINS if abs(x - t) < 0.12]
                if j:
                    zoom(j[0], 1.0, ease="cut")
                else:
                    zoom(t - 0.05, 1.0, dur=0.5, ease="inout")
                state = 1.0
            else:
                if state != 1.0:
                    continue
                zoom(t - 0.08, v, dur=0.45, ease="out")
                state = v


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



ACC = {"accent": True}
ACCU = {"accent": True, "underline": True}
HAND = {"face": "hand", "accent": True}
RED = [255, 48, 72]
WALL = ["crop/wall_18.07.30.png", "crop/wall_18.06.18.png", "crop/wall_18.07.37.png", "crop/wall_18.06.52.png",
        "crop/wall_18.08.02.png", "crop/wall_18.10.55.png", "crop/wall_18.11.10.png", "crop/wall_18.11.16.png",
        "crop/wall_18.07.14.png", "crop/wall_18.10.04.png", "crop/wall_18.08.13.png", "crop/wall_18.07.47.png",
        "crop/wall_18.08.45.png", "crop/wall_18.09.13.png"]
RESULTS = ["crop/ftmo_26915.png", "crop/topstep_19770.png", "crop/kibron_17475.png", "crop/alpha_4956.png", "crop/ftmo_16133.png",
           "crop/lawrence_6196.png", "crop/equityedge_1680.png", "crop/kibron_10028.png", "crop/desmond_580.png", "crop/bt_withdrawal_2291.png"]
END = WORDS[-1]["e"]


def until(phrase, after=0.0, pad=0.05):
    return s(phrase, after) - pad


def L(phrase, a, size, y, text=None, **o):
    return (words(phrase, a, text=text), size, y, o)


def card_title(a, b, lines, palette="green", caps=False, leak_in=True, leak_out=True, **kw):
    """A full-screen title card: the money set, then wide caps word by word."""
    graphic(a, b, caps=caps, palette=palette, leak_in=leak_in, leak_out=leak_out)
    title(a, b, lines, **kw)


def proof(a, b, img, w=1100, caps=True, label=None, label_t=None, **kw):
    """A result screenshot in a glowing frame flying in on the money set (captions stay on)."""
    graphic(a, b, caps=caps, dark=0.35, leak_out=kw.get("leak_out", True), **{k: v for k, v in kw.items() if k in ("palette",)})
    add(type="screen", t0=round(a, 3), t1=round(b, 3), img=img, w=w, cx=960, cy=470 if not label else 520, s0=0.25, dur=0.6,
        ax0=22, ay0=-20, ax1=4, ay1=-4, z=60)
    sfx("whoosh", a + 0.02, -19)
    if label:
        title(a, b, [([{"w": t, "t": round(label_t or a + 0.1, 3)} for t in label.split()], 64, 130, {"accent": True})])


def proofs(a, b, cues, w=1000):
    """Several screenshots, each flying in on its own word and replacing the last."""
    graphic(a, b, caps=True, dark=0.35)
    for k, (img, t) in enumerate(cues):
        t1 = cues[k + 1][1] if k + 1 < len(cues) else b
        add(type="screen", t0=round(t, 3), t1=round(t1, 3), img=img, w=w, cx=960, cy=470, s0=0.3, dur=0.5,
            ax0=18 if k % 2 else -18, ay0=-22 if k % 2 else 22, ax1=3, ay1=-3 if k % 2 else 3, z=60 + k)
        sfx("whoosh", t + 0.02, -20)


def results_wall(a, b, imgs=None, caps=True):
    graphic(a, b, caps=caps, dark=0.3)
    add(type="carousel3d", t0=round(a, 3), t1=round(b, 3), imgs=imgs or RESULTS + WALL[:4], w=560, seed=int(a) % 9, z=40)
    sfx("whoosh_long", a + 0.05, -22)


def tiles(a, b, items, y=470, size=270):
    """Icon tiles popping in on their words: items = [(word, icon, label)]."""
    n = len(items)
    for k, (w, ic, lb) in enumerate(items):
        t = s(w, a) - 0.04
        add(type="icontile", t0=round(t, 3), t1=round(b, 3), icon=ic, label=lb, cx=int(960 + (k - (n - 1) / 2) * 400), cy=y,
            size=size, phase=k, z=82)
        sfx("pop", t, -17)


def application(a, b):
    """The application in its glowing frame (the thank-you video's card)."""
    graphic(a, b, caps=True, dark=0.35)
    add(type="screen", t0=round(a, 3), t1=round(b, 3), img="ty/app_card.png", w=1300, blur=6, cx=960, cy=470, z=60)
    sfx("whoosh", a + 0.02, -18)


def phone_call(a, b, line1, line2):
    graphic(a, b, text_at=(960, 700))
    add(type="ripple", t0=round(a, 3), t1=round(b, 3), cx=960, cy=310, r0=150, travel=150, z=81)
    add(type="icontile", t0=round(a + 0.02, 3), t1=round(b, 3), icon="phone_ring", cx=960, cy=310, size=230, z=82)
    sfx("pop", a + 0.02, -17)
    title(a, b, [line1, line2])


def photo(name, a, b, cx, cy, h=640, rot=0.0, z=60):
    """One of Jean's own photos as a white-bordered print (like the VSL's story section)."""
    add(type="card", img=f"struggle/{name}.png", t0=round(a, 3), t1=round(b, 3), cx=cx, cy=cy, h=h, anim="pop", z=z, border=14,
        radius=10, shadow=0.5, rot=rot)
    sfx(f"mclick{int(a * 10) % 3}", a + 0.01, -15)


def main():
    out = sys.argv[3]
    import faq_beats
    faq_beats.BEATS[KEY](sys.modules[__name__])
    zooms()
    captions()
    edit = {"raw": RAW, "raw_fps_fix": True, "total": round(TOTAL, 3), "keep_frames": KEEP_F, "elements": EL,
            "sfx": sorted(SFX, key=lambda x: x["t"]), "zoom": sorted(ZOOM, key=lambda x: x["t"]),
            "music": "none", "music_end": round(END, 3), "sfx_gain_db": 0.0,
            "takes_raw": [[round(a, 3), round(b, 3)] for a, b in TAKES]}
    json.dump(edit, open(out, "w"), indent=0)
    n_cap = sum(1 for d in EL if d["type"] == "wordcap" and d.get("z") == 86)
    print(f"{KEY}: total {TOTAL:.1f}s, {len(EL)} elements, {n_cap} captions, {len(GRAPHICS)} graphics, {len(ZOOM)} zoom moves")


if __name__ == "__main__" and MODE == "plan":
    main()
