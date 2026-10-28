"""The edit: Jean's raw VSL laid out 1:1 in AB Nasdaq's style (01-vsls/reference-vsls/AB-BREAKDOWN.md).

Every visual is anchored to Jean's own words (looked up in 04-edit/transcript.json), so the plan reads like the script.
Writes edit.json (output-time elements, zoom moves, sound effects, cuts) for render.py.

    python plan.py OUT/edit.json
"""
import json, re, sys
import numpy as np

T = "/home/user/jeanfx-vsl/04-edit/transcript.json"
FPS = 30
W, H = 1920, 1080
BLUE = (0, 140, 252)
GLOW = (150, 214, 255)
WHITE, BLACK = (255, 255, 255), (10, 10, 12)
PLATE_WHITE, PLATE_GREY = (253, 253, 253), (229, 229, 229)

# ---------------------------------------------------------------- words
_w = json.load(open(T))["words"]
WORDS = []
for x in _w:
    t = x["w"].strip()
    if WORDS and (t.startswith(",") or t.startswith("-") or (t.startswith(".") and len(t) > 1)):
        WORDS[-1] = dict(WORDS[-1], w=WORDS[-1]["w"] + t, e=x["e"])
    else:
        WORDS.append(dict(x, w=t))


def norm(s):
    return re.sub(r"[^a-z0-9$]", "", s.lower())


NW = [norm(x["w"]) for x in WORDS]


def ph(phrase, after=0.0):
    """(start, end) in raw seconds of the first occurrence of phrase at/after `after`."""
    toks = [norm(t) for t in phrase.split()]
    for i in range(len(WORDS) - len(toks) + 1):
        if WORDS[i]["s"] < after - 1e-6:
            continue
        if NW[i:i + len(toks)] == toks:
            return WORDS[i]["s"], WORDS[i + len(toks) - 1]["e"]
    raise KeyError(f"phrase not found after {after}: {phrase}")


def s(phrase, after=0.0):
    return ph(phrase, after)[0]


def e(phrase, after=0.0):
    return ph(phrase, after)[1]


# ---------------------------------------------------------------- cuts (raw seconds)
CUTS = [
    (e("those other versions") + 0.04, s("My name is") - 0.04),            # "Just start believing it." (AB: "...to stop believing it")
    (e("this is legit", 49) + 0.08, s("But we keep going") - 0.06),        # the garbled "buy it and scan stuff" aside
    (e("which was five thousand dollars") + 0.06, s("but if you go all the way") - 0.04),   # the muddled Alpha Capital old-system aside
    (e("better improve your trading") + 0.06, s("I'm willing to help you master") - 0.04),  # the 90-day/"call every two weeks" line
]
RAW_END = min(WORDS[-1]["e"] + 0.6, 518.9)       # the recording is 8:38.9
# trim pauses longer than 0.3 s down to 0.12 s (AB never pauses)
for a, b in zip(WORDS, WORDS[1:]):
    if b["s"] - a["e"] > 0.30 and not any(c0 - 0.1 <= a["e"] <= c1 + 0.1 for c0, c1 in CUTS):
        CUTS.append((a["e"] + 0.06, b["s"] - 0.06))
CUTS.sort()

keep, t = [], 0.0
for a, b in CUTS:
    keep.append((t, a))
    t = b
keep.append((t, RAW_END))
KEEP_F = [(int(round(a * FPS)), int(round(b * FPS))) for a, b in keep if b - a > 0.05]


def m(x):
    """raw seconds -> output seconds"""
    out = 0.0
    for a, b in KEEP_F:
        a, b = a / FPS, b / FPS
        if x <= a:
            return out
        if x < b:
            return out + x - a
        out += b - a
    return out


TOTAL = sum(b - a for a, b in KEEP_F) / FPS

# ---------------------------------------------------------------- collectors (output time)
EL, SFX, ZOOM = [], [], []
NOCAP = []        # windows without bottom captions
CENTER = []       # windows where captions go to the middle (over B-roll)
DARKCAP = []      # windows where captions are black (over a white chart plate)
PROOF = (m(s("So guys")), m(s("So I was able")))
NOCAP.append(PROOF)


def add(**d):
    EL.append(d)
    return d


def sfx(name, t, db=-20, lead=0.0):
    SFX.append({"name": name, "t": round(t, 3), "db": db, "lead": lead})


_ck = [0]


def click(t, db=-22):
    _ck[0] += 1
    sfx(f"click{_ck[0] % 4}", t, db + ((_ck[0] * 7) % 5 - 2) * 0.6)


def plate(a, b, rgb, z=10, **kw):
    add(type="plate", t0=a, t1=b, rgb=list(rgb), z=z, **kw)
    NOCAP.append((a, b))


def line(text, kind, size, rgb, x, y, t_in, align="left", track=-4, reveal="blur", shadow=None, glow=None, **kw):
    d = dict(text=text, kind=kind, size=size, rgb=list(rgb), x=x, y=y, t_in=t_in, align=align, track=track, reveal=reveal)
    if shadow:
        d["shadow"] = list(shadow)
    if glow:
        d["glow"] = [list(glow[0]), glow[1]]
    d.update(kw)
    return d


def text(a, b, lines, z=80):
    add(type="text", t0=a, t1=b, lines=lines, z=z)


# ---------------------------------------------------------------- AB element recipes
SIDE_STYLE = {"reg": ("medium", 92, -4), "bold": ("black", 128, -6), "blue": ("black", 128, -6), "num": ("black", 170, -8)}


def side(sd, a, b, spec, dark=True, nocap=True):
    """AB's side text: stacked lines beside his head on a fade from that edge, each line on its word.
    spec: [(text, style, anchor phrase)] ; style reg/bold/blue/num."""
    A, B = m(a), m(b)
    SIDES.append((A, B))
    zoom(A, 1.0, ease="cut", drift=0.002, side=True)            # AB puts side text on the wide shot
    add(type="grad", t0=A, t1=B, kind=("left" if sd == "L" else "right") + ("" if dark else "_white"), fade=0.18, z=20)
    if nocap:
        NOCAP.append((A, B))
    import fx
    rows = []
    for txt, st, anc in spec:
        kind, size, tr = SIDE_STYLE[st]
        size = fx.fit_size(kind, size, txt, tr, 560)
        rows.append((txt, st, anc, kind, size, tr))
    # baseline to baseline: this line's descender room + the next line's cap height + a little air (AB's spacing)
    gaps = [r[4] * 0.2 + (rows[i + 1][4] * 0.73 if i + 1 < len(rows) else 0) + 14 for i, r in enumerate(rows)]
    block = sum(gaps[:-1]) + rows[0][4] * 0.73
    y = 520 - block / 2 + rows[0][4] * 0.73
    lines, cursor = [], a - 0.3
    for (txt, st, anc, kind, size, tr), g in zip(rows, gaps):
        try:
            ta = s(anc, cursor) if isinstance(anc, str) else anc
        except KeyError:
            ta = cursor + 0.3
        ta = min(max(ta, a), b - 0.3)
        cursor = ta
        rgb = BLUE if st in ("blue", "num") else (WHITE if dark else BLACK)
        x, al = (110, "left") if sd == "L" else (1810, "right")
        lines.append(line(txt, kind, size, rgb, x, y, m(ta), align=al, track=tr, shadow=(0.35, 4) if dark else None))
        click(m(ta))
        y += g
    text(A, B, lines)


def keynote(a, b, rows, rgb=PLATE_WHITE, size=112, dark_text=True, sound=True):
    """White keynote card, black words building in as he says them. rows: [(text, anchor phrase)]."""
    A, B = m(a), m(b)
    plate(A, B, rgb)
    n = len(rows)
    lines, cur = [], a - 0.2
    for i, (txt, anc) in enumerate(rows):
        try:
            ta = s(anc, cur) if isinstance(anc, str) else anc
        except KeyError:
            ta = cur + 0.3
        ta = max(ta, a)
        cur = ta
        y = 540 + (i - (n - 1) / 2) * size * 1.05 + size * 0.36
        lines.append(line(txt, "semibold", size, BLACK if dark_text else WHITE, 960, y, m(ta), align="center", track=-5))
        click(m(ta))
    text(A, B, lines)
    if sound:
        sfx("whoosh", A, -26, 0.15)


def card(img, a, b, cx, cy, w=0, h=0, anim="pop", z=60, **kw):
    add(type="card", img=img, t0=a, t1=b, cx=cx, cy=cy, w=w, h=h, anim=anim, z=z, **kw)


def zoom(t, z, cx=960, cy=470, dur=0.35, ease="out", drift=0.004, side=False):
    ZOOM.append({"t": round(t, 3), "z": z, "cx": cx, "cy": cy, "dur": dur, "ease": ease, "drift": drift, "side": side})


SIDES = []


# ================================================================ THE EDIT
# ---- HOOK ----------------------------------------------------------------------------------------------
side("L", 0.0, s("start up"), [("Every one", "reg", "Every"), ("OF THESE", "bold", "of these"), ("VIDEOS", "blue", "videos")])
side("R", s("start up"), s("It's already"), [("start up", "reg", "start up"), ("THE SAME", "blue", "the same"),
                                              ("exact way", "reg", "exact way")])
# screenshot after screenshot: flashes on AB's light-grey plate, then two big certificates
fa, fb = m(s("It's already")), m(s("But I'm going"))
plate(fa, fb, PLATE_GREY)
sfx("whoosh", fa, -24, 0.12)
flashes = [("us30_chart", 0, 700, 620, 520), ("ftmo_passed", 1000, 0, 1240, 420), ("us30_pos", 640, 0, 1400, 600),
           ("eurusd_chart", 0, 760, 560, 560), ("lucid_alpha", 1050, 0, 960, 600), ("equityedge_funded", 980, 0, 1180, 520),
           ("eurusd_pos", 640, 0, 760, 460), ("tradex_funded", 900, 0, 1260, 560), ("alphatrader_phase1", 960, 0, 820, 500),
           ("ftmo_account", 760, 0, 1220, 580)]
big = [("ftmo_26915", 0, 820), ("topstep_19770", 0, 860)]
span = fb - fa
t_big = fb - 1.3
step = (t_big - fa) / len(flashes)
for i, (img, w, h, cx, cy) in enumerate(flashes):
    a = fa + i * step
    card(img, a, a + step, cx, cy, w=w, h=h or 0, anim="cut", z=60)
    click(a, -26)
for i, (img, w, h) in enumerate(big):
    a = t_big + i * 0.65
    card(img, a, a + 0.65 if i == 0 else fb, 960, 540, w=w, h=h, anim="cut", z=61, radius=16, shadow=0.25)
    click(a, -22)
zoom(m(s("But I'm going")), 1.22, ease="cut")
zoom(m(s("because I think")), 1.0, dur=0.4)

# ---- name card (PIP) + money-drop counter ---------------------------------------------------------------
pa, pb = m(s("My name is")), m(s("$120,000"))
add(type="pip", t0=pa, t1=pb, card=[160, 168, 772, 912], face=[955, 430], dur=0.22, z=30)
NOCAP.append((pa, pb))
sfx("whoosh", pa, -22, 0.1)
import fx as _fx
w_a = _fx.text_width("medium", 100, "My name is ", -4)
w_b = _fx.text_width("medium", 100, "Jean Yvan", -4)
x0 = 1290 - (w_a + w_b) / 2
text(pa, m(s("and I've made")), [line("My name is", "medium", 100, WHITE, x0, 575, pa + 0.05, track=-4),
                                 line("Jean Yvan", "medium", 100, BLUE, x0 + w_a, 575, m(s("Jean Yvan")), track=-4)])
click(pa + 0.05)
click(m(s("Jean Yvan")))
text(m(s("and I've made")), m(s("made over")), [line("and I've", "medium", 100, WHITE, 1290, 575, m(s("and I've made")), align="center")])
text(m(s("made over")), pb, [line("made over", "medium", 100, WHITE, 1290, 575, m(s("made over")), align="center")])
click(m(s("made over")))
ma, mb = pb, m(s("Here's exactly"))
plate(ma, mb, PLATE_WHITE)
add(type="drop", t0=ma, t1=mb + 0.01, layer="far", seed=3, n=24, near_n=5, z=40)
add(type="drop", t0=ma, t1=mb + 0.01, layer="near", seed=3, n=24, near_n=5, z=90)
t_sub1 = m(s("in prop firm payouts"))
t_sub2 = m(s("and live account withdrawals"))
add(type="counter", t0=ma, t1=mb, t_count=ma, dur=1.0, v0=999, v1=120000, x=960, y=625, size=250, kind="semibold",
    rgb=list(BLUE), track=-10, move=[t_sub1, -70], z=80)
text(t_sub1, t_sub2, [line("in prop firm payouts", "medium", 96, BLACK, 960, 680, t_sub1, align="center", track=-4)])
text(t_sub2, mb, [line("& live account withdrawals", "medium", 96, BLACK, 960, 680, t_sub2, align="center", track=-4)])
sfx("whoosh_long", ma, -20, 0.2)
sfx("flutter", ma + 0.1, -22)
click(t_sub1)
click(t_sub2)
zoom(m(s("Here's exactly")), 1.0, ease="cut")
zoom(m(s("how much of that")), 1.2, dur=0.3)

# ---- PROOF (his screen recording; no captions, zooms on the numbers) ----------------------------------------
P = lambda ph_, after=20.0: m(s(ph_, after))
zoom(PROOF[0], 1.0, ease="cut", drift=0)
zoom(P("this is my actual account"), 1.45, cx=1380, cy=360, dur=0.6, ease="inout", drift=0.002)
zoom(P("But if you go to my account"), 1.0, dur=0.5, ease="inout", drift=0)
zoom(P("you can see that I've actually made"), 2.3, cx=960, cy=380, dur=0.6, ease="inout", drift=0.002)
zoom(P("And I've had my two"), 1.6, cx=960, cy=560, dur=0.5, ease="inout", drift=0.002)
zoom(P("this is my actual email account"), 1.9, cx=1030, cy=520, dur=0.6, ease="inout", drift=0.002)
zoom(P("But we keep going"), 1.3, cx=1000, cy=540, dur=0.5, ease="inout", drift=0.002)
zoom(P("next step"), 1.0, dur=0.4, ease="inout", drift=0)
zoom(P("I'm currently already funded"), 1.7, cx=1040, cy=420, dur=0.6, ease="inout", drift=0.002)
zoom(P("I also managed to secure"), 1.5, cx=1040, cy=560, dur=0.5, ease="inout", drift=0.002)
zoom(P("in total we draw"), 1.5, cx=900, cy=600, dur=0.5, ease="inout", drift=0.002)
zoom(P("alpha capital"), 1.9, cx=980, cy=560, dur=0.6, ease="inout", drift=0.002)
zoom(P("they create this"), 1.0, dur=0.4, ease="inout", drift=0)
zoom(P("already requested the payout"), 1.9, cx=820, cy=400, dur=0.6, ease="inout", drift=0.002)
zoom(P("these other emails"), 1.0, dur=0.4, ease="inout", drift=0)
zoom(P("break of the capital"), 1.7, cx=1040, cy=520, dur=0.6, ease="inout", drift=0.002)
zoom(P("which is this right here"), 1.35, cx=960, cy=600, dur=0.5, ease="inout", drift=0.003)   # he opens the certificate himself

# ---- the honesty turn ----------------------------------------------------------------------------------------
zoom(PROOF[1], 1.0, ease="cut")
zoom(m(s("of my trading profits", 110)), 1.2, dur=0.3)
ba, bb = m(s("$30,000")), m(s("I can't even show you"))
plate(ba, bb, PLATE_WHITE)
sfx("whoosh", ba, -22, 0.12)
t_coin = m(s("other", e("$40,000")))
add(type="counter", t0=ba, t1=bb, t_count=ba, dur=1.0, v0=999, v1=40000, x=960, y=625, size=260, kind="semibold",
    rgb=list(BLACK), track=-10, move=[m(s("in payouts", 118)), -70], move_x=[t_coin, -210], z=80)
card("obj_coin", t_coin, bb, 1420, 470, w=330, anim="fly", **{"from": [700, -700], "dur": 0.45}, z=81)
sfx("coin", t_coin, -20, 0.15)
text(m(s("in payouts", 118)), m(s("that I can't currently")),
     [line("in payouts on other prop firms", "medium", 84, BLACK, 750, 690, m(s("in payouts", 118)), align="center", track=-4)])
text(m(s("that I can't currently")), bb,
     [line("that I can't access", "medium", 84, BLACK, 750, 690, m(s("that I can't currently")), align="center", track=-4)])
click(m(s("in payouts", 118)))
click(m(s("that I can't currently")))
zoom(bb, 1.0, ease="cut")
zoom(m(s("Instead of asking")), 1.22, dur=0.3)
ra, rb = m(s("I would rather")), m(s("and tell you straight up"))
add(type="still", t0=ra, t1=rb, img="money_fan_g", push=0.10, pan=[0.6, -0.2], whip=True, darken=0.15, z=15)
NOCAP.append((ra, rb))
CENTER.append((ra, rb))
sfx("whoosh", ra, -22, 0.15)
t76 = m(s("$76,000", 125))
add(type="counter", t0=t76, t1=m(s("that I just showed")), t_count=t76, dur=0.8, v0=999, v1=76000, x=960, y=610, size=230,
    kind="semibold", rgb=list(WHITE), track=-10, shadow=[0.6, 6], z=82)
click(t76)
zoom(rb, 1.0, ease="cut")
zoom(m(s("And that's the whole idea")), 1.2, dur=0.3)
zoom(m(s("I will share")), 1.0, dur=0.35)
zoom(m(s("because I'm so tired")), 1.22, dur=0.3)

# ---- the problem -----------------------------------------------------------------------------------------------
zoom(m(s("So here's the thing")), 1.0, ease="cut")
wa, wb = m(s("that you're not watching")), m(s("You probably already"))
add(type="still", t0=wa, t1=wb, img="trader_screens", push=0.08, darken=0.25, z=15)
NOCAP.append((wa, wb)); CENTER.append((wa, wb))
sfx("whoosh", wa, -24, 0.12)
zoom(wb, 1.2, ease="cut")
zoom(m(s("and I know for a fact")), 1.0, dur=0.35)
ab_, bb_ = m(s("your bank account does not")), m(s("And that's the part"))
add(type="still", t0=ab_, t1=bb_, img="money_fan_g", push=0.05, darken=0.55, blur=9, z=15)
NOCAP.append((ab_, bb_))
add(type="pill", t0=ab_, t1=bb_, box=[500, 360, 1420, 650], radius=80, z=79)
text(ab_, bb_, [line("Available Balance", "medium", 84, WHITE, 960, 300, ab_, align="center", track=-4, reveal="cut")])
add(type="counter", t0=ab_, t1=bb_, t_count=ab_ + 0.1, dur=1.4, v0=429523, v1=10, x=960, y=580, size=200, kind="medium",
    rgb=list(WHITE), track=-8, ease=2.0, z=82)
sfx("whoosh", ab_, -22, 0.12)
zoom(bb_, 1.22, ease="cut")
zoom(m(s("Because it was just")), 1.0, dur=0.35)
la, lb = m(s("You will just go")), m(s("and the money will"))
add(type="still", t0=la, t1=lb, img="chalkboard", push=0.08, darken=0.2, whip=True, z=15)
add(type="still", t0=lb, t1=m(s("So what's actually")), img="cash_counter_g", push=0.08, darken=0.15, whip=True, z=15)
for a_, b_ in [(la, lb), (lb, m(s("So what's actually")))]:
    NOCAP.append((a_, b_)); CENTER.append((a_, b_))
sfx("whoosh", la, -24, 0.12)
sfx("whoosh", lb, -24, 0.12)
keynote(s("So what's actually"), s("The answer is"), [("So what's actually", "So what's actually"), ("going on?", "going on")])
zoom(m(s("The answer is")), 1.0, ease="cut")
zoom(m(s("It's not a better")), 1.22, dur=0.3)
zoom(m(s("It's not more")), 1.0, dur=0.3)
zoom(m(s("And it's not another course")), 1.22, dur=0.3)
ha, hb = m(s("What you're actually trading")), m(s("And what exactly"))
add(type="chart_broll", t0=ha, t1=hb, blur=6, z=15)
NOCAP.append((ha, hb))
sfx("whoosh", ha, -24, 0.12)
t_hp = m(s("human psychology"))
text(ha, t_hp, [line("what you're actually", "medium", 112, WHITE, 960, 520, ha, align="center", track=-5, shadow=(0.6, 5)),
                line("trading against is", "medium", 112, WHITE, 960, 640, m(s("trading against")), align="center", track=-5, shadow=(0.6, 5))])
text(t_hp, hb, [line("Human Psychology", "bold", 150, WHITE, 960, 560, t_hp, align="center", track=-7, shadow=(0.6, 6)),
                line("& instincts", "medium", 84, WHITE, 960, 660, m(s("and instincts")), align="center", track=-4, shadow=(0.6, 5)),
                line("it's not even the charts", "medium", 84, WHITE, 960, 760, m(s("it's not even the charts")), align="center",
                     track=-4, shadow=(0.6, 5))])
click(t_hp)
click(m(s("it's not even the charts")))
keynote(s("And what exactly"), s("As humans"), [("And what exactly", "And what exactly"), ("do I mean by this?", "do I mean")])
zoom(m(s("As humans")), 1.0, ease="cut")
fa_, fb_ = m(s("Fear, greed")), m(s("And this is not a flaw"))
plate(fa_, fb_, (0, 0, 0))
t_greed = m(s("greed"))
t_need = m(s("and the need"))
card("night_car", fa_, t_greed, 960, 540, w=760, anim="cut", border=4, radius=4, z=60)
text(fa_, t_greed, [line("Fear", "semibold", 120, WHITE, 960, 585, fa_, align="center", track=-5, reveal="cut", shadow=(0.6, 6))])
card("money_fan_g", t_greed, t_need, 960, 540, w=760, anim="cut", border=4, radius=4, z=60)
text(t_greed, t_need, [line("Greed", "semibold", 120, WHITE, 960, 585, t_greed, align="center", track=-5, reveal="cut", shadow=(0.6, 6))])
text(t_need, fb_, [line("and the need", "medium", 100, WHITE, 960, 470, t_need, align="center", track=-4),
                   line("to be right", "medium", 100, WHITE, 960, 580, m(s("to be right")), align="center", track=-4),
                   line("IMMEDIATELY", "black", 150, BLUE, 960, 730, m(s("immediately")), align="center", track=-6)])
for tt in (fa_, t_greed, t_need, m(s("immediately"))):
    click(tt)
zoom(fb_, 1.22, ease="cut")
ga, gb = m(s("how our brain")), m(s("And this is the exact"))
plate(ga, gb, (0, 0, 0))
card("brain", ga, gb, 1380, 540, w=760, anim="fade", drift=0.06, z=60)
text(ga, gb, [line("how our brain is", "medium", 84, WHITE, 540, 500, ga, align="center", track=-4),
              line("designed to think", "bold", 112, WHITE, 540, 620, m(s("designed to think")), align="center", track=-6)])
click(ga)
click(m(s("designed to think")))
sfx("whoosh", ga, -24, 0.12)
aa, abb = m(s("whether you're 18")), m(s("And unfortunately"))
plate(aa, abb, PLATE_WHITE)
t_old = m(s("or 40"))
card("obj_man", aa, abb, 620, 470, w=360, anim="pop", z=60)
text(aa, abb, [line("18–20 years old", "semibold", 70, BLACK, 620, 770, aa, align="center", track=-3)])
card("obj_old_man", t_old, abb, 1300, 470, w=360, anim="pop", z=60)
text(t_old, abb, [line("40–50 years old", "semibold", 70, BLACK, 1300, 770, t_old, align="center", track=-3)])
click(aa); click(t_old)
sfx("whoosh", aa, -24, 0.12)

# ---- the story ---------------------------------------------------------------------------------------------------
zoom(abb, 1.0, ease="cut")
zoom(m(s("I had to find out")), 1.22, dur=0.3)
keynote(s("I came to the United States"), s("After school"), [("I came to the U.S.", "I came to"), ("at 18 years old", "when I was 18")])
da, db_ = m(s("After school")), m(s("Guess what", 200))
plate(da, db_, (0, 0, 0))
card("delivery", da, db_, 1390, 540, w=640, anim="fade", border=6, radius=4, bw=True, z=60)
text(da, db_, [line("DoorDashing", "medium", 84, WHITE, 600, 430, da, align="center", track=-4),
               line("till midnight", "medium", 84, WHITE, 600, 530, m(s("to midnight")), align="center", track=-4),
               line("$500/week", "bold", 140, WHITE, 600, 690, m(s("making $500")), align="center", track=-7)])
for tt in (da, m(s("to midnight")), m(s("making $500"))):
    click(tt)
sfx("whoosh", da, -24, 0.12)
zoom(db_, 1.0, ease="cut")
zoom(m(s("Every dollar went")), 1.22, dur=0.3)
ra2, rb2 = m(s("I kept running")), m(s("And then one moment"))
add(type="grad", t0=ra2, t1=rb2, kind="right", fade=0.18, z=20)
NOCAP.append((ra2, rb2))
items = ["Pass", "Get funded", "Gone", "Pass", "Get funded", "Gone"]
anch = [s("pass my account"), s("get funded"), s("and it's gone"), s("Pass my account", 209), s("get funded", 210), s("and it's gone", 211)]
add(type="rolling", t0=ra2, t1=rb2, items=items, times=[m(x) for x in anch], x=1780, cy=540, size=104, radius=190, z=85)
for x in anch:
    click(m(x))
zoom(ra2, 1.0, ease="cut", drift=0)
oa = m(s("And then one moment"))
sfx("impact", oa, -14, 0.0)
keynote(s("And then one moment"), s("I put over"), [("And then", "And then"), ("one moment", "one moment")], sound=False)
ia, ib = m(s("I put over")), m(s("I knew I don't"))
plate(ia, ib, (0, 0, 0))
add(type="fire", t0=ia, t1=ib, cx=560, cy=540, h=900, z=60)
text(ia, ib, [line("I put", "medium", 92, WHITE, 1340, 410, ia, align="center", track=-4),
              line("$4,000", "bold", 200, WHITE, 1340, 600, m(s("$4,000", 214)), align="center", track=-9),
              line("in a live account", "medium", 92, WHITE, 1340, 720, m(s("in a live")), align="center", track=-4)])
for tt in (ia, m(s("$4,000", 214)), m(s("in a live"))):
    click(tt)
zoom(ib, 1.22, ease="cut")
la2, lb2 = m(s("I lost most")), m(s("My mom ended"))
plate(la2, lb2, PLATE_WHITE)
card("obj_chart_decreasing", la2, lb2, 1340, 540, w=480, anim="pop", z=60)
text(la2, lb2, [line("I lost", "medium", 100, BLACK, 640, 500, la2, align="center", track=-4),
                line("most of it", "bold", 140, BLACK, 640, 640, m(s("most of it")), align="center", track=-6)])
click(la2); click(m(s("most of it")))
sfx("whoosh", la2, -24, 0.1)
zoom(lb2, 1.0, ease="cut")
side("L", s("Quit and go"), s("And then I remember"), [("quit and go", "reg", "Quit and go"), ("TO COLLEGE", "blue", "to college")])
ca2, cb2 = m(s("I sat in my car")), m(s("One thing I learned"))
add(type="still", t0=ca2, t1=cb2, img="night_car", push=0.08, darken=0.2, whip=True, z=15)
NOCAP.append((ca2, cb2)); CENTER.append((ca2, cb2))
sfx("whoosh", ca2, -24, 0.12)
zoom(cb2, 1.22, ease="cut")
zoom(m(s("if you ever broke")), 1.0, dur=0.35)
side("R", s("So I changed two"), s("I know this feeling"), [("I changed", "reg", "I changed"), ("TWO THINGS", "blue", "two things")])

# ---- the two problems ------------------------------------------------------------------------------------------
c1a, c1b = m(s("I know this feeling")), m(s("Or, you finally"))
add(type="chart", t0=c1a, t1=c1b, kind="stophunt", reveal=[c1a + 0.2, m(s("flies exactly")) + 0.6],
    events=[[m(s("mark out your level")), "level"], [m(s("you enter your trade")), "entry"], [m(s("you enter your trade")), "stop"],
            [m(s("stopped by")), "stopped"], [m(s("flies exactly")), "fly"]], z=30)
NOCAP.append((c1a, c1b)); DARKCAP.append((c1a, c1b))
sfx("whoosh", c1a, -24, 0.12)
click(m(s("mark out your level"))); click(m(s("you enter your trade"))); sfx("whoosh", m(s("stopped by")), -26, 0.05)
zoom(c1b, 1.0, ease="cut")
na = m(s("the email lands"))
card("breached", na, m(s("And guess what", 250)), 960, 190, w=1100, anim="fly", **{"from": [0, -420], "dur": 0.4}, out="fade", z=88)
sfx("whoosh", na, -22, 0.1)
zoom(m(s("And guess what", 250)), 1.22, ease="cut")
side("L", s("What I realized"), s("You learned the same"), [("this is not a", "reg", "this is not a"), ("KNOWLEDGE", "bold", "knowledge"),
                                                            ("PROBLEM", "blue", "problem")])
c2a, c2b = m(s("You learned the same")), m(s("You was not wrong"))
add(type="chart", t0=c2a, t1=c2b, kind="sweep", reveal=[c2a + 0.2, m(s("takes the stop losses")) + 0.9],
    events=[[m(s("you enter where everyone")), "level"], [m(s("your stop loss sits")), "stops"],
            [m(s("takes the stop losses")) + 0.5, "sweep"]], z=30)
NOCAP.append((c2a, c2b)); DARKCAP.append((c2a, c2b))
sfx("whoosh", c2a, -24, 0.12)
click(m(s("your stop loss sits")))
side("R", s("You was not wrong"), s("And remember"), [("you were not wrong", "reg", "You was not"), ("you were just", "reg", "You was just"),
                                                      ("THE LIQUIDITY", "blue", "deliquidity")])
zoom(m(s("And remember")), 1.22, ease="cut")
side("L", s("Everyone teaches you"), s("In one minute"), [("everyone teaches you", "reg", "Everyone teaches"), ("HOW TO PASS", "bold", "how to pass"),
                                                          ("nobody teaches you", "reg", "nobody teaches"), ("HOW TO KEEP IT", "blue", "how to keep")])
zoom(m(s("In one minute")), 1.0, ease="cut")
zoom(m(s("how I managed to fix")), 1.22, dur=0.3)

# ---- how it started --------------------------------------------------------------------------------------------
zoom(m(s("But first")), 1.0, ease="cut")
keynote(s("February 2025"), s("is when I managed"), [("In February 2025", "February")])
fa2, fb2 = m(s("is when I managed")), m(s("You guys can go on"))
zoom(fa2, 1.0, ease="cut", drift=0)
add(type="counter", t0=m(s("first 10k")), t1=fb2, t_count=m(s("first 10k")), dur=0.9, v0=999, v1=10000, x=960, y=330, size=200,
    kind="semibold", rgb=list(WHITE), track=-8, shadow=[0.6, 6], z=82)
text(fa2, fb2, [line("I hit my first", "medium", 76, WHITE, 960, 140, fa2, align="center", track=-4, shadow=(0.6, 5)),
                line("month", "medium", 76, WHITE, 960, 430, m(s("month", 294)), align="center", track=-4, shadow=(0.6, 5))])
add(type="grad", t0=fa2, t1=fb2, kind="bottom", fade=0, z=19)
NOCAP.append((fa2, fb2))
click(fa2); click(m(s("first 10k")))
zoom(fb2, 1.22, ease="cut")
keynote(s("Two months later"), s("I ended up buying"), [("Two months later", "Two months later")])
side("R", s("I ended up buying"), s("I literally went"), [("I bought my", "reg", "buying"), ("DREAM CAR", "blue", "dream car")])
zoom(m(s("I literally went")), 1.0, ease="cut")
zoom(m(s("to living in a")), 1.22, dur=0.3)

# ---- the fix ---------------------------------------------------------------------------------------------------
zoom(m(s("So here is what changed")), 1.0, ease="cut")
zoom(m(s("I was entering trades")), 1.22, dur=0.3)
oa_, ob_ = m(s("one setup that")), m(s("This is where price"))
zoom(m(s("So instead of hunting")), 1.0, ease="cut", drift=0.002)
add(type="behind", t0=oa_, t1=m(s("I call it")), lines=[{"text": "ONE SETUP", "size": 330, "x": 960, "y": 360, "track": -16}], z=55)
add(type="behind", t0=m(s("the inducement setup")), t1=ob_, lines=[{"text": "INDUCEMENT", "size": 300, "x": 960, "y": 350, "track": -14}], z=55)
NOCAP.append((oa_, ob_))
sfx("whoosh", oa_, -22, 0.1); click(oa_)
sfx("whoosh", m(s("the inducement setup")), -22, 0.1)
c3a, c3b = m(s("This is where price")), m(s("So this is where you stop"))
add(type="chart", t0=c3a, t1=c3b, kind="inducement", reveal=[c3a + 0.2, m(s("after it has already taken")) + 0.5],
    events=[[c3a + 0.3, "stops"], [m(s("sweeps your liquidity")), "sweep"], [m(s("sweeps your liquidity")), "liq"],
            [m(s("charge of reconstruction")), "choch"], [m(s("that's when you enter")), "entry2"], [m(s("This strategy only")), "fly"]], z=30)
NOCAP.append((c3a, c3b)); DARKCAP.append((c3a, c3b))
sfx("whoosh", c3a, -24, 0.12)
click(m(s("sweeps your liquidity"))); click(m(s("charge of reconstruction"))); click(m(s("that's when you enter")))
side("L", s("So this is where you stop"), s("No setups"), [("stop being", "reg", "stop being"), ("THE LIQUIDITY", "bold", "the liquidity"),
                                                         ("START TRADING", "blue", "start trading"), ("with it", "reg", "with it")])
zoom(m(s("No setups")), 1.22, ease="cut")
zoom(m(s("And this setup comes")), 1.0, dur=0.35)
pa2 = m(s("So the account you pass"))
card("ftmo_account", pa2, m(s("This is my student")), 1450, 520, w=640, anim="pop", border=8, radius=18, shadow=0.5, z=60)
add(type="grad", t0=pa2, t1=m(s("This is my student")), kind="right", fade=0.15, strength=0.8, z=20)
sfx("whoosh", pa2, -22, 0.1); click(pa2 + 0.05)

# ---- students --------------------------------------------------------------------------------------------------
ka, kb = m(s("This is my student")), m(s("He was literally"))
plate(ka, kb, (0, 0, 0))
card("kibron_17475", ka, kb, 600, 540, w=600, anim="fade", border=6, radius=4, z=60)
text(ka, kb, [line("this is my student", "medium", 84, WHITE, 1300, 500, ka, align="center", track=-4),
              line("KIBRON", "black", 150, WHITE, 1300, 650, m(s("Kibron")), align="center", track=-6)])
click(ka); click(m(s("Kibron")))
sfx("whoosh", ka, -24, 0.12)
wa2, wb2 = m(s("He was literally")), m(s("And I showed him"))
plate(wa2, wb2, (0, 0, 0))
card("warehouse", wa2, wb2, 1390, 540, w=640, anim="fade", border=6, radius=4, bw=True, z=60)
text(wa2, wb2, [line("working 9 to 5", "medium", 84, WHITE, 600, 430, wa2, align="center", track=-4),
                line("WAREHOUSE JOBS", "black", 112, WHITE, 600, 570, m(s("warehouse jobs")), align="center", track=-5),
                line("for 2–3 years", "medium", 84, WHITE, 600, 680, m(s("for over two")), align="center", track=-4)])
for tt in (wa2, m(s("warehouse jobs")), m(s("for over two"))):
    click(tt)
xa, xb = m(s("where he managed")), m(s("And this keeps going"))
plate(xa, xb, PLATE_WHITE)
text(xa, xb, [line("he made over", "medium", 84, BLACK, 960, 170, xa, align="center", track=-4),
              line("in one month", "medium", 84, BLACK, 960, 1010, m(s("within one single")), align="center", track=-4)])
card("kibron_10028", xa + 0.1, xb, 560, 560, w=560, anim="pop", radius=16, shadow=0.35, rot=4, z=60)
card("kibron_7446", xa + 0.45, xb, 1360, 560, w=560, anim="pop", radius=16, shadow=0.35, rot=-4, z=61)
card("kibron_17475", m(s("$20,000", 360)), xb, 960, 560, w=600, anim="pop", radius=16, shadow=0.45, z=62)
for tt in (xa + 0.1, xa + 0.45, m(s("$20,000", 360))):
    click(tt)
sfx("whoosh", xa, -24, 0.12)
lwa, lwb = m(s("I have Lawrence")), m(s("Like, look at"))
plate(lwa, lwb, (0, 0, 0))
card("lawrence_6196", lwa, lwb, 600, 540, w=640, anim="fade", border=6, radius=4, z=60)
text(lwa, lwb, [line("I have", "medium", 84, WHITE, 1320, 470, lwa, align="center", track=-4),
                line("LAWRENCE", "black", 140, WHITE, 1320, 610, m(s("Lawrence")), align="center", track=-6),
                line("over $6,000 in payouts", "medium", 72, WHITE, 1320, 710, m(s("making over")), align="center", track=-3)])
for tt in (lwa, m(s("Lawrence")), m(s("making over"))):
    click(tt)
zoom(lwb, 1.0, ease="cut")
zoom(m(s("When he joined")), 1.22, dur=0.3)
zoom(m(s("Once we hopped")), 1.0, dur=0.35)
oa3, ob3 = m(s("This enabled him")), m(s("This can be you"))
plate(oa3, ob3, PLATE_WHITE)
des = [("desmond_406", 520, 330, -5), ("desmond_162", 1400, 320, 4), ("desmond_92", 560, 760, 3), ("desmond_580", 1380, 760, -3),
       ("desmond_277", 960, 300, -2), ("desmond_341", 960, 780, 2)]
anc = [s("consistent payouts"), s("over and over"), s("and over", s("over and over") + 0.1), s("and over again"), s("again", s("and over again")) ]
times_d = [m(x) for x in anc] + [m(s("again", s("and over again"))) + 0.25]
for (img, cx, cy, r), tt in zip(des, times_d):
    card(img, tt, ob3, cx, cy, w=620, anim="pop", radius=14, shadow=0.35, rot=r, z=60)
    click(tt)
sfx("whoosh", oa3, -24, 0.1)
zoom(ob3, 1.22, ease="cut")
wla, wlb = m(s("These are the same students")), m(s("And that's what I teach"))
add(type="wall", t0=wla, t1=wlb, imgs=["wall_18.07.30", "wall_18.08.13", "wall_18.07.47", "wall_18.11.10", "wall_18.06.52",
                                        "wall_18.08.45", "wall_18.07.14", "wall_18.09.13", "wall_18.10.04", "wall_18.07.37",
                                        "wall_18.10.55", "wall_18.11.16", "wall_18.06.18", "wall_18.08.02"], z=15)
NOCAP.append((wla, wlb)); CENTER.append((wla, wlb))
sfx("whoosh_long", wla, -22, 0.15)

# ---- the offer -------------------------------------------------------------------------------------------------
zoom(wlb, 1.0, ease="cut")
side("R", s("My one-on-one mentorship"), s("of which this includes"), [("my 1-on-1", "reg", "My one"), ("MENTORSHIP", "blue", "mentorship")])
side("L", s("two times every single week"), s("One-on-one mentorship with"), [("two times", "reg", "two times"), ("EVERY WEEK", "blue", "every single week")])
zoom(m(s("trying to figure out", 405)), 1.22, dur=0.3)
zoom(m(s("I'm willing to help you master")), 1.0, ease="cut")
sa, sb = m(s("having somebody by your side")), m(s("to make sure that a mistake"))
plate(sa, sb, PLATE_WHITE)
card("trader_screens", sa, sb, 560, 540, w=760, anim="fade", border=0, radius=6, shadow=0.3, z=60)
t_rev = m(s("to review what you did"))
text(sa, t_rev, [line("having someone", "bold", 96, BLACK, 1000, 500, sa, track=-5),
                 line("by your side", "medium", 96, BLACK, 1000, 610, m(s("by your side")), track=-4)])
text(t_rev, sb, [line("to review", "bold", 96, BLACK, 1000, 440, t_rev, track=-5),
                 line("what you did", "medium", 96, BLACK, 1000, 550, m(s("what you did", 423)), track=-4),
                 line("every single day", "medium", 96, BLACK, 1000, 660, m(s("every single day", 424)), track=-4)])
for tt in (sa, m(s("by your side")), t_rev, m(s("what you did", 423)), m(s("every single day", 424))):
    click(tt)
sfx("whoosh", sa, -24, 0.12)
zoom(sb, 1.0, ease="cut")
zoom(m(s("and not three days later")), 1.22, dur=0.3)
zoom(m(s("And that's literally it")), 1.0, ease="cut")
zoom(m(s("to catch the mistakes")), 1.22, dur=0.3)
r90a, r90b = m(s("This private mentorship runs")), m(s("and the whole goal"))
zoom(r90a, 1.0, ease="cut", drift=0.002)
side("R", s("This private mentorship runs"), s("and the whole goal"), [("This mentorship runs", "reg", "This private"),
                                                                       ("FOR 90 DAYS", "bold", "for 90 days")])
gia, gib = m(s("and the whole goal")), m(s("Now, if you're looking"))
add(type="grad", t0=gia, t1=gib, kind="right", fade=0.18, z=20)
NOCAP.append((m(s("get you in")) - 0.1, gib))
add(type="rolling", t0=m(s("get you in")) - 0.05, t1=gib, items=["Get you in", "Get consistent", "Get you out"],
    times=[m(s("get you in")), m(s("get consistent")), m(s("and get you out"))], x=1760, cy=540, size=100, radius=170, z=85)
for x in ("get you in", "get consistent", "and get you out"):
    click(m(s(x)))
sga, sgb = m(s("Now, if you're looking")), m(s("this isn't it"))
plate(sga, sgb, (0, 0, 0))
t_ind = m(s("or indicator"))
card("signal_card", sga, t_ind, 1340, 540, w=520, anim="fly", rot=-8, **{"from": [500, 0], "dur": 0.4}, z=60)
text(sga, t_ind, [line("Now if you're looking", "medium", 84, WHITE, 640, 500, sga, align="center", track=-4),
                  line("for a signal group", "bold", 100, WHITE, 640, 610, m(s("for a signal group")), align="center", track=-5)])
card("phone_us30_chart", t_ind, sgb, 560, 560, h=880, anim="fly", rot=6, **{"from": [-600, 0], "dur": 0.4}, z=60)
text(t_ind, sgb, [line("or an indicator", "bold", 100, WHITE, 1300, 500, t_ind, align="center", track=-5),
                  line("to copy and paste", "medium", 84, WHITE, 1300, 610, m(s("to copy and paste")), align="center", track=-4)])
for tt in (sga, m(s("for a signal group")), t_ind, m(s("to copy and paste"))):
    click(tt)
sfx("whoosh", sga, -24, 0.12)
sfx("whoosh", t_ind, -24, 0.12)
zoom(sgb, 1.22, ease="cut")
zoom(m(s("or if you're somebody", 452)), 1.0, dur=0.35)
zoom(m(s("that's exactly who")), 1.22, dur=0.3)

# ---- what's included (split screen, typed as he says it) -----------------------------------------------------------
spa, spb = m(s("let's go ahead and actually talk")), m(s("With all the resources"))
zoom(spa, 1.05, ease="cut", drift=0)
add(type="split", t0=spa, t1=spb, panel_w=840, face_x=955, z=30)
NOCAP.append((spa, spb))
sfx("whoosh", spa, -22, 0.1)
t_title = m(s("what's included"))
import fx as _fx2
wA = _fx2.text_width("black", 58, "INSIDE ", -2)
wB = _fx2.text_width("black", 58, "JEANFX", -2)
xA = 1380 - (wA + wB) / 2
title = [line("WHAT'S INCLUDED", "black", 58, WHITE, 1380, 150, t_title, align="center", track=-2),
         line("INSIDE", "black", 58, WHITE, xA, 220, t_title + 0.1, track=-2),
         line("JEANFX", "black", 58, BLUE, xA + wA, 220, t_title + 0.15, track=-2)]
text(t_title, spb - 0.25, title)
add(type="card", img="rule", t0=t_title + 0.2, t1=spb - 0.25, cx=1380, cy=250, w=0, h=0, anim="fade", z=81)
click(t_title)


def wrap(txt, n=33):
    out, cur = [], ""
    for wd in txt.split():
        if len(cur) + len(wd) + 1 > n and cur:
            out.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    out.append(cur)
    return out


inc = [("1.", "40 hours+ of video modules going over my exact strategy and how I trade from A to Z", "Number one", "A to Z"),
       ("2.", "The market recap calls that happen Monday - Friday at 11 am Eastern", "Number two", "Eastern Time"),
       ("3.", "You have 24/7 access to me to review what you did every single day", "number three", "every single day")]
y = 340
inc_lines = []
for num, txt, a_, b_ in inc:
    ta = m(s(a_, 465))
    tb = m(e(b_, ta and s(a_, 465)))
    rows = wrap(txt)
    nchar = sum(len(r) for r in rows)
    cps = max(nchar / max(tb - ta, 0.8), 12)
    inc_lines.append(line(num, "bold", 52, WHITE, 985, y, ta, track=-2, reveal="cut"))
    done = 0
    for r in rows:
        inc_lines.append(line(r, "medium", 50, WHITE, 1040, y, ta + done / cps, track=-2, reveal="type", cps=cps))
        done += len(r)
        y += 64
    y += 46
    click(ta)
text(t_title, spb - 0.25, inc_lines, z=82)

# ---- guarantee + call to action -------------------------------------------------------------------------------------
zoom(spb, 1.0, ease="cut")
zoom(m(s("I'm super confident")), 1.22, dur=0.3)
ua, ub = m(s("that you will be able")), m(s("In fact, I'm so"))
plate(ua, ub, PLATE_WHITE, z=10)
add(type="slide_up", t0=ua, t1=ua + 0.35, z=95)
card("obj_trophy", ua + 0.1, ub, 560, 560, h=640, anim="fly", **{"from": [0, 300], "dur": 0.45}, z=60)
t_succ = m(s("success in this program"))
text(ua + 0.15, t_succ, [line("that you will be", "medium", 96, BLACK, 1300, 470, ua + 0.15, align="center", track=-4),
                         line("able to see", "bold", 120, BLACK, 1300, 600, m(s("able to see")), align="center", track=-5)])
text(t_succ, ub, [line("SUCCESS", "black", 190, BLACK, 1300, 560, t_succ, align="center", track=-8),
                  line("in the program", "medium", 96, BLACK, 1300, 680, m(s("in this program", 499)), align="center", track=-4)])
sfx("whoosh_up", ua, -20, 0.05)
for tt in (ua + 0.15, m(s("able to see")), t_succ, m(s("in this program", 499))):
    click(tt)
zoom(ub, 1.0, ease="cut")
ka2, kb2 = m(s("that if you don't")), m(s("get a pair"))
keynote(s("that if you don't"), s("get a pair"), [("that if you don't", "that if you don't"), ("go ahead and", "ahead and")])
gpa, gpb = kb2, m(s("I'll go ahead and work"))
plate(gpa, gpb, PLATE_WHITE)
add(type="drop", t0=gpa, t1=gpb + 0.01, layer="far", seed=11, n=14, near_n=4, z=40)
add(type="drop", t0=gpa, t1=gpb + 0.01, layer="near", seed=11, n=14, near_n=4, z=90)
card("topstep_19770", gpa + 0.1, gpb, 1360, 540, h=760, anim="fly", **{"from": [0, 500], "dur": 0.45}, radius=18, shadow=0.45, z=60)
text(gpa, gpb, [line("Get a Payout", "bold", 120, BLACK, 560, 520, gpa, align="center", track=-5),
                line("within 90 days", "medium", 92, BLACK, 560, 630, m(s("within those 90")), align="center", track=-4)])
sfx("whoosh", gpa, -22, 0.1); sfx("flutter", gpa + 0.1, -22)
click(gpa); click(m(s("within those 90")))
zoom(gpb, 1.22, ease="cut")
t_ww = m(s("work with you", 504))
t_ff = m(s("for free until"))
t_ud = m(s("until you do"))
gl = (GLOW, 0.55)
text(gpb, t_ww, [line("I'll go ahead and", "medium", 96, WHITE, 962, 925, gpb, align="center", track=-5, shadow=(0.5, 4))])
text(t_ww, t_ff, [line("WORK WITH YOU", "black", 124, GLOW, 962, 925, t_ww, align="center", track=-5, glow=gl)])
text(t_ff, m(s("So if this sounds")), [line("FOR FREE", "black", 130, GLOW, 962, 830, t_ff, align="center", track=-5, glow=gl),
                                         line("until you do", "medium", 96, WHITE, 962, 945, t_ud, align="center", track=-5, shadow=(0.5, 4))])
add(type="grad", t0=gpb, t1=m(s("So if this sounds")), kind="bottom", fade=0, z=19)
NOCAP.append((gpb, m(s("So if this sounds"))))
click(t_ww); click(t_ff)
t_app = m(s("the application is down"))
t_db = m(s("down below", 509))
text(t_app, m(s("And if it's not")), [line("THE APPLICATION", "black", 124, GLOW, 962, 830, t_app, align="center", track=-5, glow=gl),
                                      line("is down below", "medium", 96, WHITE, 962, 945, t_db, align="center", track=-5, shadow=(0.5, 4))])
add(type="grad", t0=t_app, t1=m(s("And if it's not")), kind="bottom", fade=0, z=19)
NOCAP.append((t_app, m(s("And if it's not"))))
click(t_app)
zoom(m(s("And if it's not")), 1.0, ease="cut")
zoom(m(s("Just go ahead, fill")), 1.22, dur=0.3)

# ---------------------------------------------------------------- captions
FIX = [("Ivan", "Yvan"), ("do-dash", "DoorDash"), ("door-dashing", "DoorDashing"), ("GFX", "JeanFX"), ("GeneFX", "JeanFX"),
       ("discourse", "Discord"), ("deliquidity", "the liquidity"), ("You was", "you were"), ("sack", "cycle"), ("being down", "being dumb"),
       ("stock loss", "stop loss"), ("charge of reconstruction", "change of character"), ("is called the same", "is caught the same"),
       ("completely wrong", "completely blown"), ("get a pair", "get a payout"), ("don't ahead", "don't go ahead"),
       ("pro-form pairs", "prop firm payouts"), ("pro-form accounts", "prop firm accounts"), ("Payout Farm Accounts Bank", "prop firm accounts"),
       ("take a number for a word", "take my word for a number"), ("what's trading", "what's true"), ("go line one", "go learn one"),
       ("Because it was just", "because if it was just"), ("As humans deal", "as humans we deal"), ("nine or five", "9 to 5"),
       ("on the ball.", ""), ("market recap course that happened", "market recap calls that happen"), ("with the same videos", "it's in the same videos"),
       ("challenge for you", "challenge fee"), ("into something that is not", "into something that it's not"), ("That's more,", ""),
       ("No setups,", "no setup"), ("they're restricted", "they restricted"), ("one-on-one", "1-on-1"), ("24 by 7", "24/7"), ("the answers are", "both answers are"), ("will just go", "would just go"),
       ("the money will roll", "the money would roll"), ("start up", "starts up"), ("you will just", "you would just")]
PROPER = {"i", "i'm", "i've", "i'll", "i'd", "jean", "yvan", "topstep", "ftmo", "jeanfx", "discord", "kibron", "lawrence", "monday",
          "friday", "eastern", "youtube", "doordash", "doordashing", "united", "states", "february", "a", "z", "ivan", "u.s."}

caps_words = [dict(x) for x in WORDS]
# apply fixes on the word stream
txt_all = [x["w"] for x in caps_words]
for bad, good in FIX:
    bt = bad.split()
    for i in range(len(caps_words) - len(bt) + 1):
        if [norm(caps_words[i + k]["w"]) for k in range(len(bt))] == [norm(z) for z in bt] and all(norm(z) for z in bt):
            gw = good.split()
            for k in range(len(bt)):           # spread the fixed words over the original words (keeps timing)
                if k < len(bt) - 1:
                    caps_words[i + k]["w"] = gw[k] if k < len(gw) else ""
                else:
                    caps_words[i + k]["w"] = " ".join(gw[k:])


def clean(wd):
    t = re.sub(r"^[.,!?;:\"]+|[.,!?;:\"]+$", "", wd.strip()).strip()
    if not t:
        return ""
    if t.lower() in PROPER or t.startswith("$") or any(c.isdigit() for c in t) or (t.isupper() and len(t) > 1):
        return t if t.lower() not in ("a", "z") else t.lower() if t.lower() == "a" else t
    return t[:1].lower() + t[1:]


def hidden(o):
    return any(a - 0.02 <= o < b for a, b in NOCAP)


def in_win(o, wins):
    return any(a <= o < b for a, b in wins)


def raw_in_cut(x):
    return any(a <= x < b for a, b in CUTS)


groups, cur = [], []
seq = [w for w in caps_words if not raw_in_cut(w["s"]) and w["w"]]
for i, wd in enumerate(seq):
    o = m(wd["s"])
    mode = "center" if in_win(o, CENTER) else "dark" if in_win(o, DARKCAP) else "bottom"
    if hidden(o) and mode == "bottom":
        if cur:
            groups.append(cur)
            cur = []
        continue
    if cur and cur[0]["mode"] != mode:
        groups.append(cur)
        cur = []
    cur.append(dict(wd, mode=mode, o=o))
    nxt = seq[i + 1] if i + 1 < len(seq) else None
    chars = len(" ".join(clean(x["w"]) for x in cur))
    brk = (nxt is None or re.search(r"[.?!,]$", wd["w"]) or len(cur) >= 4 or chars >= 18
           or (nxt and m(nxt["s"]) - m(wd["e"]) > 0.25))
    if nxt is not None and len(cur) < 2 and not re.search(r"[.?!]$", wd["w"]) and chars < 10:
        brk = False
    if brk:
        groups.append(cur)
        cur = []
if cur:
    groups.append(cur)

prev_end = -1.0
for gi, g in enumerate(groups):
    words_txt = " ".join(t for t in (clean(x["w"]) for x in g) if t)
    if not words_txt:
        continue
    a = g[0]["o"]
    nxt_a = groups[gi + 1][0]["o"] if gi + 1 < len(groups) else a + 3
    b = min(nxt_a, m(g[-1]["e"]) + 0.35)
    # stop at the next graphic
    for c0, c1 in NOCAP:
        if a < c0 < b:
            b = c0
    if b - a < 0.08:
        continue
    fresh = (a - prev_end) > 0.05
    mode = g[0]["mode"]
    if mode == "center":
        L = line(words_txt, "medium", 112, WHITE, 960, 580, a, align="center", track=-5, reveal="blur" if fresh else "cut", shadow=(0.6, 6))
    elif mode == "dark":
        L = line(words_txt, "medium", 76, BLACK, 960, 1035, a, align="center", track=-3, reveal="blur" if fresh else "cut")
    else:
        L = line(words_txt, "medium", 96, WHITE, 962, 925, a, align="center", track=-5, reveal="blur" if fresh else "cut", shadow=(0.5, 4))
    add(type="text", t0=a, t1=b, lines=[L], z=84)
    prev_end = b

# AB's dark fade along the bottom under the captions on face shots (everywhere a face shot carries captions)
face_ok = [(a, b) for a, b in [(0, TOTAL)]]
cov = sorted([(d["t0"], d["t1"]) for d in EL if d["type"] in ("plate", "still", "money_bg", "chart", "chart_broll", "wall", "pip", "split")]
             + [PROOF])
t_ = 0.0
for a, b in cov:
    if a - t_ > 0.3:
        add(type="grad", t0=t_, t1=a, kind="bottom", fade=0, z=19)
    t_ = max(t_, b)
if TOTAL - t_ > 0.3:
    add(type="grad", t0=t_, t1=TOTAL, kind="bottom", fade=0, z=19)


def main():
    out = sys.argv[1]
    # no punch-ins while side text is up (the forced wide framing at its start stays)
    global ZOOM
    ZOOM = [z for z in ZOOM if z["side"] or not any(a < z["t"] < b - 0.05 for a, b in SIDES)]
    for z in ZOOM:
        z.pop("side", None)
    edit = {"total": round(TOTAL, 3), "keep_frames": KEEP_F, "elements": EL, "sfx": sorted(SFX, key=lambda x: x["t"]),
            "zoom": sorted(ZOOM, key=lambda x: x["t"]), "music_under_lu": 15.0,
            "cuts_raw": [[round(a, 3), round(b, 3)] for a, b in CUTS]}
    json.dump(edit, open(out, "w"), indent=0)
    n_cap = sum(1 for d in EL if d["type"] == "text" and d.get("z") == 84)
    print(f"total {TOTAL:.1f}s (raw {RAW_END:.1f}s), {len(EL)} elements, {n_cap} captions, {len(SFX)} sfx, {len(ZOOM)} zoom moves")


if __name__ == "__main__":
    main()
