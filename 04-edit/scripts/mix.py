"""Audio for Jean's AB-style edit: his voice (cut like the picture, cleaned up), the boom-free "Me And The Devil" bed at a
constant level 15 LU under his voice (what AB does), and the sound effects, mastered to -14 LUFS.

Sound effects are made here from scratch (AB's are library sounds): a crisp click for text, whooshes for switches, a coin
swish, a money flutter and a low impact.
"""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal

SR = 48000
RAW = "/home/user/work/jean/jeanfxvsl.mov"
BED = "/home/user/work/jean/bed"
SONG = "/home/user/work/ref/an/song.wav"
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
VOICE_CHAIN = ("highpass=f=75:poles=2,equalizer=f=220:t=q:w=1.1:g=-2,equalizer=f=3200:t=q:w=1.0:g=2,"
               "treble=g=1.5:f=9000,acompressor=threshold=-26dB:ratio=3:attack=6:release=140:knee=4:makeup=5,"
               "deesser=i=0.35,alimiter=limit=0.89:level=false")


def bp(x, lo, hi, order=4):
    return signal.sosfiltfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def norm(x, peak=0.9):
    return (x / (np.abs(x).max() + 1e-9) * peak).astype(np.float32)


def stereo(x, width=0.0, seed=0):
    if width <= 0:
        return np.stack([x, x], 1)
    r = np.random.default_rng(seed)
    d = int(0.0006 * SR)
    return np.stack([x, np.roll(x, d) * (1 - width * 0.2)], 1)


def make_sfx():
    r = np.random.default_rng(1)
    out = {}
    for k in range(4):                                     # AB's text click: bright, 30-60 ms
        n = int(0.06 * SR)
        t = np.arange(n) / SR
        tick = bp(r.standard_normal(n), 3000, 12000) * np.exp(-t / 0.004)
        body = np.sin(2 * np.pi * (2400 + 300 * k) * t) * np.exp(-t / 0.008) * 0.25
        x = tick / (np.abs(tick).max() + 1e-9) + body
        out[f"click{k}"] = norm(stereo(x, 0.5, k), 0.8)
    for name, dur, f0, f1 in [("whoosh", 0.38, 400, 4000), ("whoosh_long", 0.7, 250, 3000), ("whoosh_up", 0.5, 300, 6000)]:
        n = int(dur * SR)
        t = np.arange(n) / SR
        noise = r.standard_normal(n)
        y = np.zeros(n)
        steps = 24
        for i in range(steps):                             # sweep a band through the noise
            a, b = i * n // steps, (i + 1) * n // steps
            fc = f0 * (f1 / f0) ** (i / steps) if name != "whoosh" else f0 + (f1 - f0) * np.sin(np.pi * i / steps)
            y[a:b] = bp(noise, max(fc * 0.6, 60), min(fc * 1.6, 20000), 2)[a:b]
        shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
        x = y * shape
        L = x * np.linspace(0.6, 1.0, n)
        R = x * np.linspace(1.0, 0.6, n)
        out[name] = norm(np.stack([L, R], 1), 0.7)
    n = int(0.9 * SR)                                       # coin: swish + metallic ring
    t = np.arange(n) / SR
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, d in [(2800, 0.25), (4170, 0.18), (6930, 0.12), (1720, 0.3)])
    sw = np.zeros(n)
    sw[: int(0.3 * SR)] = out["whoosh"][: int(0.3 * SR), 0]
    x = np.roll(ring * 0.5, int(0.22 * SR)) * (np.arange(n) > int(0.22 * SR)) + sw
    out["coin"] = norm(stereo(x, 0.5), 0.8)
    n = int(0.8 * SR)                                       # money flutter: quick paper flaps
    x = np.zeros(n)
    for k in range(18):
        s = int(r.uniform(0, 0.7) * SR)
        m = int(0.03 * SR)
        x[s:s + m] += bp(r.standard_normal(m), 900, 6000) * env(m, 0.002, 0.008)[: len(x[s:s + m])]
    out["flutter"] = norm(stereo(x, 0.7), 0.6)
    for k in range(3):                                      # mouse click: press, then a softer release
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        x = np.zeros(n)
        for at, amp, f in [(0.0, 1.0, 2100 + 150 * k), (0.058 + 0.006 * k, 0.55, 2600 + 150 * k)]:
            s0 = int(at * SR)
            m = int(0.012 * SR)
            tt = np.arange(m) / SR
            burst = bp(r.standard_normal(m), 1500, 9000) * np.exp(-tt / 0.0016)
            body = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.004) * 0.6
            thock = np.sin(2 * np.pi * 380 * tt) * np.exp(-tt / 0.006) * 0.35
            x[s0:s0 + m] += (burst / (np.abs(burst).max() + 1e-9) + body + thock) * amp
        out[f"mclick{k}"] = norm(stereo(x, 0.3), 0.85)
    n = int(0.12 * SR)                                      # pop: a counter lands
    t = np.arange(n) / SR
    f = 900 * np.exp(-t / 0.02) + 260
    out["pop"] = norm(stereo(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035)), 0.8)
    for name, dur in [("roll08", 0.8), ("roll10", 1.0), ("roll14", 1.4)]:  # counter ticks, slowing like the number
        n = int((dur + 0.1) * SR)
        x = np.zeros(n)
        N = 18
        for i in range(N):
            u = i / N
            at = dur * (1 - (1 - u) ** (1 / 2.2))
            s0 = int(at * SR)
            m = int(0.006 * SR)
            tt = np.arange(m) / SR
            x[s0:s0 + m] += bp(r.standard_normal(m), 3500, 11000) * np.exp(-tt / 0.0012) * (1 - 0.4 * u)
        out[name] = norm(stereo(x, 0.4), 0.6)
    for k in range(4):                                      # keyboard tap
        n = int(0.05 * SR)
        t = np.arange(n) / SR
        x = bp(r.standard_normal(n), 800 + 200 * k, 6000) * np.exp(-t / 0.006) + np.sin(2 * np.pi * (240 + 30 * k) * t) * np.exp(-t / 0.01) * 0.5
        out[f"key{k}"] = norm(stereo(x, 0.4), 0.7)
    n = int(0.9 * SR)                                       # notification: two bell tones
    t = np.arange(n) / SR
    bell = lambda f0, a: (np.sin(2 * np.pi * f0 * t) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * t)) * np.exp(-t / 0.22) * a
    x = bell(1318.5, 1.0)
    x[int(0.13 * SR):] += bell(1760, 0.9)[: n - int(0.13 * SR)]
    out["notif"] = norm(stereo(x), 0.75)
    n = int(0.24 * SR)                                      # swish: a short soft whoosh
    t = np.arange(n) / SR
    y = bp(r.standard_normal(n), 900, 7000) * np.sin(np.pi * t / t[-1]) ** 2
    out["swish"] = norm(np.stack([y * np.linspace(0.7, 1, n), y * np.linspace(1, 0.7, n)], 1), 0.6)
    n = int(0.42 * SR)                                      # marker drawing a circle
    t = np.arange(n) / SR
    y = bp(r.standard_normal(n), 1800, 7500) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * np.sin(np.pi * t / t[-1]) ** 0.6
    out["marker"] = norm(stereo(y, 0.2), 0.6)
    n = int(1.0 * SR)                                       # low impact
    t = np.arange(n) / SR
    f = 70 * np.exp(-t / 0.35) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    thump = bp(r.standard_normal(n), 60, 900) * np.exp(-t / 0.05)
    out["impact"] = norm(stereo(boom + thump * 0.4), 0.9)
    return out


def load_audio(path, ss=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.4f}", "-i", path]
    if dur:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    p = subprocess.run(cmd, capture_output=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def place(buf, x, at):
    s = int(round(at * SR))
    if s < 0:
        x, s = x[-s:], 0
    n = min(len(x), len(buf) - s)
    if n > 0:
        buf[s:s + n] += x[:n]


def db(v):
    return 10 ** (v / 20)


def mix(edit, out_path):
    total = edit["total"]
    n = int(round(total * SR))
    # voice: same cuts as the picture (frame boundaries), 6 ms fades at each join
    src = load_audio(RAW)
    voice = np.zeros((n + SR, 2))
    pos = 0
    fade = int(0.006 * SR)
    for a, b in edit["keep_frames"]:
        seg = src[a * 1600:b * 1600].copy()
        seg[:fade] *= np.linspace(0, 1, fade)[:, None]
        seg[-fade:] *= np.linspace(1, 0, fade)[:, None]
        voice[pos:pos + len(seg)] += seg
        pos += len(seg)
    tmp = out_path + ".voice_raw.wav"
    sf.write(tmp, voice[:n].astype(np.float32), SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", VOICE_CHAIN, "-ar", str(SR), "-c:a", "pcm_f32le",
                    out_path + ".voice.wav"], check=True)
    voice, _ = sf.read(out_path + ".voice.wav", always_2d=True)
    meter = pyln.Meter(SR)
    lv = meter.integrated_loudness(voice)
    # music: AB's song level, 15 LU under the voice, constant (no ducking)
    bed_path = f"{BED}/stem_song.wav"
    need = total + 1.6
    if (not os.path.exists(bed_path)) or sf.info(bed_path).duration < need:
        subprocess.run([sys.executable, f"{SCRIPTS}/song_bed.py", SONG, str(total + 0.1), BED], check=True)
    bed, _ = sf.read(bed_path, always_2d=True)
    bed = bed[:n]
    lb = meter.integrated_loudness(bed[: min(len(bed), 120 * SR)])
    music = bed * db(lv - edit.get("music_under_lu", 15.0) - lb)
    if len(music) < n:
        music = np.concatenate([music, np.zeros((n - len(music), 2))])
    # end: AB's music just stops with the picture; we let it ring 0.6 s under the last word then stop
    sfx_lib = make_sfx()
    fx = np.zeros((n + SR, 2))
    for s in edit.get("sfx", []):
        x = sfx_lib[s["name"]].astype(np.float64) * db(lv + 12 + s.get("db", -20))   # dB relative to the voice level
        place(fx, x, s["t"] - s.get("lead", 0.0))
    mixd = voice[:n] + music[:n] + fx[:n]
    pre = out_path + ".pre.wav"
    sf.write(pre, mixd.astype(np.float32), SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-v", "info", "-hide_banner", "-i", pre, "-af",
                        "loudnorm=I=-14:TP=-1.2:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    st = json.loads(r.stderr[r.stderr.rindex("{"):])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", pre, "-af",
                    f"loudnorm=I=-14:TP=-1.2:LRA=9:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
                    f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true",
                    "-ar", str(SR), "-c:a", "pcm_s24le", out_path], check=True)
    for p in (tmp, pre):
        os.remove(p)
    print(f"voice {lv:.1f} LUFS, music set {edit.get('music_under_lu', 15.0)} LU under it; mastered to -14 LUFS")


if __name__ == "__main__":
    mix(json.load(open(sys.argv[1])), sys.argv[2])
