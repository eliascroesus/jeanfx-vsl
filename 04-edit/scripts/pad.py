"""The thank-you video's music bed: a very soft, warm string pad on G with no beat (AB's thank-you bed is a pad on a G
chord, energy between 80 and 500 Hz, nothing above 2 kHz, ~18 dB under the voice). Built from VSCO 2 CE string
sustains (CC0): a G pedal in the cellos, the upper voices drifting G -> C/G -> G -> Em/G every 8 s with slow
crossfades, endless sustain by overlapping windows of each recording, low-passed and given a long soft reverb.

    python pad.py SECONDS OUT.wav
"""
import sys
import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
VS = "/home/user/work/vsco/repo/Strings"
# real pitch -> file (VSCO names these an octave low)
FILES = {
    "G2": "Cello Section/susvib/susvib_G1_v1_1.wav",
    "D3": "Cello Section/susvib/susvib_D2_v1_1.wav",
    "E3": "Viola Section/susvib/ViolaEns_susvib_E2_v1_1.wav",
    "G3": "Viola Section/susvib/ViolaEns_susvib_G2_v1_1.wav",
    "B3": "Viola Section/susvib/ViolaEns_susvib_B2_v1_1.wav",
    "C4": "Cello Section/susvib/susvib_C3_v1_1.wav",
    "D4": "Violin Section/susVib/VlnEns_susVib_D3_v1.wav",
    "E4": "Cello Section/susvib/susvib_E3_v1_1.wav",
}
CHORDS = [["D3", "G3", "B3", "D4"],           # G
          ["E3", "G3", "C4", "E4"],           # C/G
          ["D3", "G3", "B3", "D4"],           # G
          ["E3", "G3", "B3", "E4"]]           # Em/G
STEP = 8.0                                     # seconds per chord
XF = 3.0                                       # crossfade between chords


def load(rel):
    x, sr = sf.read(f"{VS}/{rel}", always_2d=True)
    x = x.mean(1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr)
    return x / (np.sqrt(np.mean(x[int(SR):int(4 * SR)] ** 2)) + 1e-9)


def sustain(x, dur, seed):
    """Endless sustain: overlapping 3 s Hann windows taken from the steady middle of the recording."""
    r = np.random.default_rng(seed)
    n = int(dur * SR) + 4 * SR
    out = np.zeros(n)
    win = int(3 * SR)
    hop = win // 2
    w = np.hanning(win)
    lo, hi = int(1.2 * SR), len(x) - win - int(1.0 * SR)
    for s in range(0, n - win, hop):
        k = r.integers(lo, max(lo + 1, hi))
        out[s:s + win] += x[k:k + win] * w
    return out[:int(dur * SR)]


def reverb(x, seed=7, t60=3.2):
    r = np.random.default_rng(seed)
    n = int(t60 * SR)
    ir = r.normal(0, 1, n) * np.exp(-6.9 * np.arange(n) / n)
    ir = signal.sosfilt(signal.butter(2, 3000, "low", fs=SR, output="sos"), ir)
    ir /= np.sqrt(np.sum(ir ** 2))
    return signal.fftconvolve(x, ir)[:len(x)]


def build(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    notes = {k: load(v) for k, v in FILES.items()}
    mono = sustain(notes["G2"], dur, 1) * 1.0                       # the G pedal
    for i, name in enumerate(sorted({p for c in CHORDS for p in c})):
        # how much of this note each moment: 1 inside a chord that has it, crossfaded at the changes
        g = np.zeros(n)
        for k in range(int(dur / STEP) + 2):
            chord = CHORDS[k % len(CHORDS)]
            if name in chord:
                a, b = k * STEP - XF / 2, (k + 1) * STEP + XF / 2
                g = np.maximum(g, np.clip(np.minimum((t - a) / XF, (b - t) / XF), 0, 1))
        g = np.sin(g * np.pi / 2) ** 2
        if g.max() > 0:
            mono += sustain(notes[name], dur, 10 + i) * g * (0.55 if name in ("D3", "E3", "G3") else 0.42)
    mono = signal.sosfilt(signal.butter(4, 1200, "low", fs=SR, output="sos"), mono)
    mono = signal.sosfilt(signal.butter(2, 60, "high", fs=SR, output="sos"), mono)
    wet = reverb(mono)
    left = mono * 0.55 + wet * 0.8
    right = np.roll(mono, int(0.011 * SR)) * 0.55 + reverb(mono, 9) * 0.8
    out = np.stack([left, right], 1)
    fade = int(2.0 * SR)
    out[:fade] *= np.linspace(0, 1, fade)[:, None] ** 2
    return out / (np.abs(out).max() + 1e-9) * 0.5


if __name__ == "__main__":
    sf.write(sys.argv[2], build(float(sys.argv[1])).astype(np.float32), SR, subtype="FLOAT")
