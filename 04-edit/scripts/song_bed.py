"""Jean's music bed: "Me And The Devil" (instrumental) used the way AB Nasdaq uses it, minus the boom.

What AB does (measured in 01-vsls/reference-vsls/AB-BREAKDOWN.md): the song plays untouched at one constant level
(the song at -29 dB while his voice sits at -24 LUFS, so about 15 LU under the voice), starting 5.56 s into the song
(after the intro), and every time it reaches about 1:27-1:53 it jumps straight back to an early part of the song
(0:06 or 0:29). He only ever uses the first 1:53.

What's different here: the boom is gone. The song's boom is its 808 sub-bass, which runs under the whole track, plus
the kick. Everything under 150 Hz is cut (8th-order high-pass) and in the 150-300 Hz band only the tonal part is kept
(harmonic/percussive separation drops the kick's body). Above 300 Hz the song is untouched: hats, snares, melody and
pads all stay. The jumps land on the song's own bar grid (88.99 BPM, a bar every 2.697 s) at points where the music
before and after matches, with a 60 ms crossfade, so they can't be heard.

    python song_bed.py song.wav total_seconds out_dir
"""
import json, sys
import numpy as np, soundfile as sf, librosa
from scipy import signal

SR = 48000
BEAT, BEAT0 = 0.67425, 0.210          # the song's beat grid (88.99 BPM), stable to 15 ms over the whole song
BAR = 4 * BEAT
START = 5.562                         # where AB starts the song
LOOP_LO, LOOP_HI = 5.0, 113.0         # AB only uses this part of the song


def deboom(y):
    hp = signal.butter(8, 150, "high", fs=SR, output="sos")
    band = signal.butter(4, [150, 300], "band", fs=SR, output="sos")
    above = signal.butter(8, 300, "high", fs=SR, output="sos")
    out = np.zeros_like(y)
    for c in range(y.shape[1]):
        x = y[:, c]
        low = signal.sosfiltfilt(band, x)
        D = librosa.stft(low, n_fft=4096, hop_length=1024)
        Hm, _ = librosa.decompose.hpss(D, margin=(1.0, 2.0))
        low_h = librosa.istft(Hm, hop_length=1024, length=len(x))
        out[:, c] = signal.sosfiltfilt(hp, low_h + signal.sosfiltfilt(above, x))
    return out


def bars(t0, t1):
    k0 = int(np.ceil((t0 - BEAT0) / BAR))
    return [BEAT0 + k * BAR for k in range(k0, int((t1 - BEAT0) / BAR) + 1)]


def main():
    src, total, outdir = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    y, sr = sf.read(src, always_2d=True)
    if sr != SR:
        y = librosa.resample(y.T, orig_sr=sr, target_sr=SR).T
    h = deboom(y)
    grid = bars(LOOP_LO, LOOP_HI)
    C = librosa.feature.chroma_cqt(y=librosa.resample(h.mean(1), orig_sr=SR, target_sr=22050), sr=22050, hop_length=512)
    fps = 22050 / 512

    def vec(t):                       # chroma of the bar before t
        a, b = int((t - BAR) * fps), int(t * fps)
        v = C[:, max(a, 0):max(b, a + 1)].mean(1)
        return v / (np.linalg.norm(v) + 1e-9)

    # AB's pattern: play from 0:05.56 to ~1:27, back to ~0:06, on to ~1:53, back to ~0:29, on to ~1:53, back to ~0:06 ...
    targets = [(87.4, 6.1), (113.0, 29.6), (113.0, 6.2), (113.0, 29.6), (113.0, 6.2)]
    plan, pos, made, k = [], START, 0.0, 0
    need = total + 2.0
    while made < need:
        leave, land = targets[min(k, len(targets) - 1)]
        if made + (leave - pos) >= need:
            plan.append((pos, pos + (need - made)))
            break
        # nearest bar lines around AB's jump points, picking the best-matching pair
        cands = [(float(vec(a) @ vec(b)), a, b) for a in grid if abs(a - leave) <= 3 * BAR
                 for b in grid if abs(b - land) <= 3 * BAR and b < a - 10]
        sim, a, b = max(cands)
        plan.append((pos, a))
        made += a - pos
        pos = b
        k += 1
    xf = int(0.06 * SR)
    bed = np.zeros((0, 2))
    for s, e in plan:
        seg = h[int(s * SR):int(e * SR) + xf].copy()
        if len(bed):
            r = np.linspace(0, 1, xf)[:, None]
            bed[-xf:] = bed[-xf:] * np.sqrt(1 - r) + seg[:xf] * np.sqrt(r)
            seg = seg[xf:]
        bed = np.concatenate([bed, seg])
    n = int((total + 1.5) * SR)
    bed = np.concatenate([bed, np.zeros((max(0, n - len(bed)), 2))])[:n]
    fo = int(1.5 * SR)
    bed[n - fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    sf.write(f"{outdir}/stem_song.wav", bed.astype(np.float32), SR, subtype="FLOAT")
    json.dump({"passes_song_seconds": [[round(s, 3), round(e, 3)] for s, e in plan], "length": round(len(bed) / SR, 2),
               "note": "song kept at its own scale; the mixer sets its level relative to the voice like AB (-29 dB at -24 LUFS voice)"},
              open(f"{outdir}/loop_plan.json", "w"), indent=1)
    print("passes:", [(round(s, 1), round(e, 1)) for s, e in plan], "length", round(len(bed) / SR, 1))


if __name__ == "__main__":
    main()
