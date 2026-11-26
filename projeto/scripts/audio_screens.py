"""Audio for the 'computer screens' reel: separated voice of each clip + original score + interface sound design.

usage: python3 audio_screens.py <v5 dir> <timeline.json> <out_music.wav> <out_voice.wav>
"""
import json
import subprocess
import sys

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

D, TLP, OUT_M, OUT_V = sys.argv[1:5]
SR = 48000
tl = json.load(open(TLP))
EV, C = tl["ev"], tl["clips"]
TOTAL = tl["total"]
NT = int(TOTAL * SR) + SR
rng = np.random.default_rng(5)
PAD = 0.6


def read(path):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                        capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)


def at(t):
    return int(max(0.0, t) * SR)


def add(buf, t0, sig, g=1.0, pan=0.0):
    o = at(t0)
    if o >= len(buf):
        return
    sig = sig[: len(buf) - o]
    if sig.ndim == 1:
        buf[o:o + len(sig), 0] += sig * g * np.sqrt(.5 * (1 - pan)) * 1.414
        buf[o:o + len(sig), 1] += sig * g * np.sqrt(.5 * (1 + pan)) * 1.414
    else:
        buf[o:o + len(sig)] += sig * g


def lp(x, fc, o=2):
    return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, o=2):
    return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "band", fs=SR, output="sos"), x, axis=0)


tt = lambda d: np.arange(int(d * SR)) / SR
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)

# ---------------- voice (Demucs vocals of each clip) ----------------
voice = np.zeros((NT, 2), np.float32)
CL = {name: (v, rs) for name, v, rs in json.load(open(f"{D}/clips.json"))}
for name, c in C.items():
    v, rs = CL[name]
    parts = []
    for i, (a, b) in enumerate(rs):
        x = read(f"{D}/aud/sep/htdemucs/{name}_{i}/vocals.wav")
        off = min(PAD, a)
        seg = x[at(off):at(off + b - a)].copy()
        f = int(.012 * SR); r = np.linspace(0, 1, f, dtype=np.float32)[:, None]
        seg[:f] *= r; seg[-f:] *= r[::-1]
        parts.append(seg)
    clip = np.concatenate(parts)
    # level match: speech RMS (frames above -45 dBFS) to a common target
    fr = clip[: len(clip) // 480 * 480].mean(1).reshape(-1, 480)
    e = np.sqrt((fr ** 2).mean(1)); act = e[e > 10 ** (-45 / 20)]
    g = 0.1 / (np.sqrt((act ** 2).mean()) + 1e-9) if len(act) else 1.0
    add(voice, c["start"], clip * g)
VCHAIN = ("highpass=f=80,afftdn=nr=8:nf=-45,equalizer=f=300:t=q:w=1.0:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,"
          "deesser=i=0.3,acompressor=threshold=-20dB:ratio=3:attack=6:release=140:makeup=3,alimiter=limit=0.95")
voice = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", VCHAIN,
                                      "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], input=voice.tobytes(), capture_output=True,
                                     check=True).stdout, np.float32).reshape(-1, 2)[:NT]
if len(voice) < NT:
    voice = np.pad(voice, ((0, NT - len(voice)), (0, 0)))

# ---------------- score ----------------
OVER, TURN, END = EV["overload"], EV["turn"], tl["endCard"]
DESK = 1.40
music = np.zeros((NT, 2), np.float32)


def pad_note(f, dur, bright, g=.05):
    t = tt(dur); y = np.zeros((len(t), 2), np.float32)
    for ch, det in ((0, -1), (1, 1)):
        for cents in (-6, 0, 6):
            ff = f * 2 ** ((cents + det * 2) / 1200); ph = rng.uniform(0, 6.28)
            for n in range(1, 7):
                y[:, ch] += np.sin(2 * np.pi * ff * n * t + ph * n) / n ** (1.6 - .5 * bright)
    env = np.minimum(1, t / .6) * np.minimum(1, (dur - t) / .8)
    return (y * env[:, None] * g).astype(np.float32)


def kick(g):
    t = tt(.45); f = 48 + 70 * np.exp(-t * 28)
    return ((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) + .3 * rng.standard_normal(len(t)) * np.exp(-t * 90)) * g).astype(np.float32)


def hat(g):
    t = tt(.06); return (hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * 70) * g).astype(np.float32)


def pluck(f, g):
    t = tt(.5); y = (np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 9)
    return (y * np.minimum(1, t / .004) * g).astype(np.float32)


BEAT = 60 / 108; BAR = 4 * BEAT
DARK = [[45, 52, 55, 60], [41, 48, 53, 57], [43, 50, 55, 58], [40, 47, 52, 56]]       # Am, F, Gm-ish, E (tension)
WARM = [[48, 55, 60, 64, 67], [45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [43, 50, 55, 59, 62]]   # C, Am, F, G
ROOT_D = [33, 29, 31, 28]; ROOT_W = [36, 33, 29, 31]
# tension section (desk -> overload)
b = 0
while DESK + b * BAR < OVER:
    t0 = DESK + b * BAR
    for nn in DARK[b % 4]:
        add(music, t0 - .2, pad_note(hz(nn), BAR + .6, .1, .045))
    f = hz(ROOT_D[b % 4] + 12); t = tt(BAR)
    add(music, t0, ((np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.minimum(1, t / .05) * np.minimum(1, (BAR - t) / .2) * .09).astype(np.float32))
    b += 1
beat = 0
while DESK + beat * BEAT < OVER - .05:
    tb = DESK + beat * BEAT
    intense = tb > tl["clips"]["c2"]["start"]
    add(music, tb, kick(.45 if beat % 2 == 0 else .25))
    for q in range(4 if intense else 2):
        add(music, tb + q * BEAT / (4 if intense else 2), hat(.05 if q % 2 else .07), pan=.3 if q % 2 else -.3)
    if intense and beat % 2 == 1:
        nn = DARK[(beat // 4) % 4][(beat // 2) % 4] + 24
        add(music, tb, pluck(hz(nn), .035), pan=-.3)
    beat += 1
# MRTI section (turn -> end card)
b = 0
while TURN + b * BAR < END + 2.5:
    t0 = TURN + b * BAR
    ch = WARM[b % 4] if t0 < END else [48, 55, 60, 64, 67, 72]
    for nn in ch:
        add(music, t0 - .2, pad_note(hz(nn), BAR + 1.0 if t0 < END else 4.2, .75, .05))
    f = hz(ROOT_W[b % 4] + 12); t = tt(BAR)
    add(music, t0, ((np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)) * np.minimum(1, t / .05) * np.minimum(1, (BAR - t) / .25) * .09).astype(np.float32))
    b += 1
beat = 0
while TURN + .8 + beat * BEAT < END:
    tb = TURN + .8 + beat * BEAT
    add(music, tb, kick(.5 if beat % 2 == 0 else .3)); add(music, tb + BEAT / 2, hat(.06), pan=.25)
    notes = WARM[(int((tb - TURN) // BAR)) % 4][1:]
    for q in range(2):
        add(music, tb + q * BEAT / 2, pluck(hz(notes[(beat * 2 + q) % len(notes)] + 12), .05), pan=-.35 if q else .35)
    beat += 1
ir_t = tt(2.2)
ir = np.stack([rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.8) for _ in range(2)], 1).astype(np.float32); ir /= np.sqrt((ir ** 2).sum(0))
wet = np.stack([fftconvolve(music[:, c], ir[:, c])[:NT] for c in range(2)], 1).astype(np.float32)
music = music + wet * .35
# riser into the overload, drop out during the implode, fade at the end
for t0, dur, g in ((OVER - 2.4, 2.4, .2), (END - 1.8, 1.8, .1), (5.0, 1.8, .12)):
    t = tt(dur); x = t / dur
    y = bp(rng.standard_normal(len(t)), 300, 6000) * x ** 2.2 + np.sin(2 * np.pi * np.cumsum(200 + 900 * x ** 2) / SR) * .25 * x ** 2
    add(music, t0, (y * g).astype(np.float32))
tax = np.arange(NT) / SR
gate = 1 - np.clip((tax - (OVER + .45)) / .05, 0, 1) * (1 - np.clip((tax - TURN + .1) / .3, 0, 1))
music *= gate[:, None]
music *= np.clip((TOTAL - tax) / 1.2, 0, 1)[:, None]

# ---------------- sound design ----------------
sfx = np.zeros((NT, 2), np.float32)


def whoosh(t0, d, g, pan=0):
    t = tt(d); x = t / d; n = rng.standard_normal(len(t))
    y = (bp(n, 250, 2500) * (1 - x) + bp(n, 1800, 9000) * x) * np.sin(np.pi * x) ** 2
    add(sfx, t0, (y / (np.abs(y).max() + 1e-6) * g).astype(np.float32), pan=pan)


def boom(t0, g):
    t = tt(1.8); f = 70 * np.exp(-t * 2.5) + 34
    add(sfx, t0, ((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6) + rng.standard_normal(len(t)) * np.exp(-t * 25) * .3) * g).astype(np.float32))


def hit(t0, g):
    t = tt(1.2)
    y = (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 110 * t)) * np.exp(-t * 4.5) + (np.sin(2 * np.pi * 1760 * t) * .2 + np.sin(2 * np.pi * 2637 * t) * .1) * np.exp(-t * 3)
    add(sfx, t0, (y * g).astype(np.float32))


def click(t0, g, pan=0):
    t = tt(.035); add(sfx, t0, ((rng.standard_normal(len(t)) * np.exp(-t * 220) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 150) * .6) * g).astype(np.float32), pan=pan)


def popsnd(t0, g, f=520, pan=0):
    t = tt(.18); add(sfx, t0, (np.sin(2 * np.pi * (f + 500 * np.exp(-t * 40)) * t) * np.exp(-t * 26) * g).astype(np.float32), pan=pan); click(t0, g * .6, pan)


def ding(t0, g, pan=.35):
    t = tt(.9); t2 = np.maximum(0, t - .09)
    y = np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 6) + .7 * np.sin(2 * np.pi * 1975.5 * t2) * np.exp(-t2 * 6) * (t > .09)
    add(sfx, t0, (y * g).astype(np.float32), pan=pan)


def blip(t0, f, g, pan=0):
    t = tt(.08); add(sfx, t0, (np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * g).astype(np.float32), pan=pan)


def buzz(t0, g, d=.22):
    t = tt(d); y = np.sign(np.sin(2 * np.pi * 110 * t)) * np.exp(-t * 14) * .6 + np.sin(2 * np.pi * 220 * t) * np.exp(-t * 10) * .4
    add(sfx, t0, (lp(y, 2400) * g).astype(np.float32))


def tick(t0, g):
    t = tt(.02); add(sfx, t0, (rng.standard_normal(len(t)) * np.exp(-t * 300) * g).astype(np.float32), pan=rng.uniform(-.4, .4))


def chime(t0, g):
    for k, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        t = tt(2.0); add(sfx, t0 + k * .06, (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) * np.minimum(1, t / .01) * g * (.8 if k < 3 else .5)).astype(np.float32))


def shimmer(t0, g):
    t = tt(1.2); y = np.zeros(len(t))
    for _ in range(9):
        f = rng.uniform(2200, 6500); d = rng.uniform(0, .5); y += np.sin(2 * np.pi * f * t) * np.exp(-np.maximum(0, t - d) * 6) * (t > d)
    add(sfx, t0, (y / 9 * g).astype(np.float32))


def alarm(t0, d, g):
    t = tt(d); f = np.where((t * 6).astype(int) % 2 == 0, 880, 660)
    y = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .5
    add(sfx, t0, (lp(y, 3000) * g).astype(np.float32))


def glitch(t0, d, g):
    t = tt(d); y = np.sign(np.sin(2 * np.pi * 90 * t)) * (rng.random(len(t)) > .5) * np.exp(-t * 6)
    add(sfx, t0, (bp(y, 200, 5000) * g).astype(np.float32))


# opening
whoosh(.05, .8, .12); click(.8, .25); chime(.45, .09)
whoosh(.85, .65, .3); boom(DESK, .55); hit(DESK, .2)
for i, w in enumerate((1.55, 2.05, 2.50)):
    popsnd(w, .28, 420 + 90 * i, (-.3, .3, -.2)[i])
for i in range(7):
    tick(1.67 + i * .1, .12)
for i in range(40):
    tick(2.62 + i * .022, .05)
for n in (2.80, 3.05, 3.30, 3.55):
    ding(n, .14)
for c_ in (2.05, 2.5, 3.0, 3.5):
    click(c_, .2, .2)
c1 = C["c1"]
popsnd(c1["start"] - .12, .3, 640)
whoosh(EV["c1Expand"] - .12, .35, .25); glitch(EV["c1Expand"], .2, .1); hit(EV["c1Expand"] + .05, .14)
hit(EV["c1Punch"], .16)
whoosh(EV["head1"] - .25, .4, .2); hit(EV["head1"], .22); glitch(EV["head2"], .25, .12); boom(EV["head2"], .55); hit(EV["head2"], .25)
# pains
for i, n in enumerate(tl["order"]):
    c = C[n]
    whoosh(c["start"] - .3, .35, .16, pan=(-.3 if i % 2 else .3)); popsnd(c["start"] - .14, .26, 480 + 40 * i); buzz(c["start"] - .1, .05)
    blip(c["start"] + .25, 1500, .04)
for t_ in EV["w_c2"]:
    blip(t_, 900, .05)
for j, t_ in enumerate(EV["w_c3"]):
    (buzz if j == 1 else blip)(t_, .06) if j == 1 else blip(t_, 1200, .05)
for j, t_ in enumerate(EV["w_c4"]):
    if j == 2:
        buzz(t_, .07); hit(t_, .08)
    else:
        blip(t_, 1400, .05)
for t_ in EV["w_c5"]:
    blip(t_, 700, .06); tick(t_, .1)
for t_ in EV["w_c6"]:
    blip(t_, 600, .06)
for j, t_ in enumerate(EV["w_c7"]):
    blip(t_, 1600 + 120 * j, .045)
for k in range(8):
    click(EV["w_c7"][2] + .3 + k * .09, .1, rng.uniform(-.4, .4))
# overload + implode + turn
alarm(OVER - .6, 1.05, .07); glitch(OVER, .3, .14)
whoosh(OVER + .2, .3, .25); boom(OVER + .45, .7); hit(OVER + .45, .3)
shimmer(TURN, .1); chime(TURN + .05, .07); popsnd(TURN - .1, .25, 700)
hit(EV["processo"], .12)
hit(EV["six"], .15); shimmer(EV["six"], .08)
for t_ in EV["mods"]:
    blip(t_, 2200, .05); shimmer(t_, .025)
popsnd(C["c10"]["start"] - .12, .25, 680)
click(EV["chama"], .3); ding(EV["chama"] + .05, .12, 0)
whoosh(END - .15, .6, .14); hit(END + .95, .12)

# ---------------- mix ----------------
env = lp(np.abs(voice).mean(1), 8, 1)
active = lp(np.clip((env - .004) / .01, 0, 1), 2.5, 1)
duck = 1 - .62 * np.clip(active, 0, 1)
v_rms = np.sqrt(np.mean(voice ** 2) + 1e-12); m_rms = np.sqrt(np.mean(music ** 2) + 1e-12)
music_g = music / m_rms * v_rms * .5
mix_m = voice + sfx * (v_rms / .05) * .9 + music_g * duck[:, None]
mix_v = voice + sfx * (v_rms / .05) * .9
for arr, out in ((mix_m, OUT_M), (mix_v, OUT_V)):
    arr = arr[: int(TOTAL * SR)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-2.0:LRA=11,alimiter=limit=0.8:level=disabled", "-ar", str(SR), out],
                   input=np.clip(arr, -4, 4).astype(np.float32).tobytes(), check=True)
print("audio done")
