"""Sound design for the opening preview. usage: python3 sfx.py out.wav duration"""
import sys, subprocess
import numpy as np
SR = 48000
OUT, DUR = sys.argv[1], float(sys.argv[2])
N = int(DUR * SR)
mix = np.zeros((N, 2), np.float32)
rng = np.random.default_rng(3)
tt = lambda d: np.arange(int(d * SR)) / SR


def add(t0, sig, g=1.0, pan=0.0):
    o = int(t0 * SR)
    if o >= N: return
    sig = sig[:N - o] * g
    mix[o:o + len(sig), 0] += sig * np.sqrt(.5 * (1 - pan)) * 1.414
    mix[o:o + len(sig), 1] += sig * np.sqrt(.5 * (1 + pan)) * 1.414


def onepole(x, a):
    y = np.zeros_like(x); acc = 0.0
    for i in range(0, len(x), 1):
        acc += a * (x[i] - acc); y[i] = acc
    return y


def lp_noise(d, a):   # cheap filtered noise (vectorised one-pole via cumulative trick is overkill; use convolution)
    n = rng.standard_normal(int(d * SR)); k = int(1 / a); ker = np.ones(k) / k
    return np.convolve(n, ker, 'same')


def whoosh(t0, d, g):
    t = tt(d); x = t / d
    n = rng.standard_normal(len(t))
    lo = np.convolve(n, np.ones(40) / 40, 'same'); hi = n - np.convolve(n, np.ones(6) / 6, 'same')
    y = (lo * (1 - x) * 3 + hi * x) * np.sin(np.pi * x) ** 2
    add(t0, y / (np.abs(y).max() + 1e-6), g)


def boom(t0, g):
    t = tt(1.8); f = 70 * np.exp(-t * 2.5) + 34
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6) + rng.standard_normal(len(t)) * np.exp(-t * 25) * .3
    add(t0, y, g)


def hit(t0, g):
    t = tt(1.2)
    y = (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 110 * t)) * np.exp(-t * 4.5) + (np.sin(2 * np.pi * 1760 * t) * .2 + np.sin(2 * np.pi * 2637 * t) * .1) * np.exp(-t * 3)
    add(t0, y, g)


def click(t0, g, pan=0):
    t = tt(.035); y = rng.standard_normal(len(t)) * np.exp(-t * 220) + np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 150) * .6
    add(t0, y, g, pan)


def pop(t0, g, f=520, pan=0):
    t = tt(.18); y = np.sin(2 * np.pi * (f + 500 * np.exp(-t * 40)) * t) * np.exp(-t * 26)
    add(t0, y, g, pan); click(t0, g * .6, pan)


def ding(t0, g, pan=.4):
    t = tt(.9)
    y = (np.sin(2 * np.pi * 1318.5 * t) * np.exp(-t * 6) + .7 * np.sin(2 * np.pi * 1975.5 * np.maximum(0, t - .09)) * np.exp(-np.maximum(0, t - .09) * 6) * (t > .09))
    add(t0, y, g, pan)


def tick(t0, g):
    t = tt(.02); add(t0, rng.standard_normal(len(t)) * np.exp(-t * 300), g, rng.uniform(-.4, .4))


def chime(t0, g):
    for k, f in enumerate((523.25, 659.25, 783.99, 1046.5)):
        t = tt(2.2); y = np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) * np.minimum(1, t / .01)
        add(t0 + k * .06, y, g * (.8 if k < 3 else .5))


def glitch(t0, d, g):
    t = tt(d); y = np.sign(np.sin(2 * np.pi * 90 * t)) * (rng.random(len(t)) > .5) * np.exp(-t * 6)
    add(t0, y.astype(np.float32), g)


# timeline (matches screens.html)
T = dict(lid0=.15, boot=.75, push0=1.15, desk=1.80, w=[2.00, 2.70, 3.30, 4.10], ntf=[4.50, 4.85, 5.20, 5.55], head1=6.10, head2=6.75, end=8.40)
# lid hinge + boot
whoosh(T['lid0'], .9, .12); click(T['lid0'] + .85, .25)
chime(T['boot'], .10)
whoosh(T['push0'], .75, .30); boom(T['desk'], .55); hit(T['desk'], .2)
for i, w in enumerate(T['w']):
    pop(w, .28, 420 + 90 * i, (-.3, .3, -.2, .25)[i])
for i in range(6):
    tick(T['w'][0] + .18 + i * .16, .12)
for i in range(40):
    tick(T['w'][2] + .15 + i * .03, .05)
for i, n in enumerate(T['ntf']):
    ding(n, .16, .35)
for c in (2.5, 3.1, 3.8, 4.5, 5.3):
    click(c, .2, .2)
# tension pulse under the chaos (heartbeat-like, speeding up)
t = T['desk'] + .1; gap = .62
while t < T['head1']:
    boom(t, .18); boom(t + .16, .1); t += gap; gap = max(.36, gap * .93)
whoosh(T['head1'] - .25, .4, .2); hit(T['head1'], .25)
glitch(T['head2'], .25, .12); boom(T['head2'], .6); hit(T['head2'], .3)
whoosh(T['end'] - .5, .55, .3)
# low drone that rises
t = np.arange(N) / SR
drone = (np.sin(2 * np.pi * 55 * t) + .5 * np.sin(2 * np.pi * 82.4 * t) + .3 * np.sin(2 * np.pi * 110 * t * (1 + .002 * np.sin(t * 3))))
env = np.clip((t - T['desk']) / 4.0, 0, 1) * (1 - np.clip((t - T['head2']) / .2, 0, 1) * .6)
mix += (drone * env * .06)[:, None]
mix /= max(1e-6, np.abs(mix).max()) / 0.8
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'loudnorm=I=-14:TP=-2:LRA=9', '-ar', str(SR), OUT],
               input=mix.astype(np.float32).tobytes(), check=True)
print('ok', OUT)
