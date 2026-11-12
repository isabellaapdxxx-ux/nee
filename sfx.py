#!/usr/bin/env python3
"""Synthesise the ad's sound-effects track (sfx.wav, 48 kHz stereo, 15 s).

Every sound is generated from scratch (sines + filtered noise), so there are
no samples to license. Cue times match the CSS animation timings in index.html.
Usage: python3 sfx.py [out.wav]
"""
import math
import sys
import wave

import numpy as np

SR = 48_000
DUR = 15.0
rng = np.random.default_rng(17)
mix = np.zeros((2, int(SR * DUR) + SR))  # 1 s spare for tails, trimmed later


# ---------------------------------------------------------------- helpers
def t_axis(d):
    return np.arange(int(SR * d)) / SR


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def env_exp(d, tau):
    return np.exp(-t_axis(d) / tau)


def fft_filter(x, lo=None, hi=None):
    """Brick-ish band-limit with soft edges in the frequency domain."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def swept_bandpass(x, f0, f1, q=1.4):
    """Time-varying biquad band-pass (exponential sweep f0 -> f1)."""
    n = len(x)
    fc = f0 * (f1 / f0) ** (np.arange(n) / max(n - 1, 1))
    y = np.zeros(n)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(n):
        w = 2 * math.pi * fc[i] / SR
        a = math.sin(w) / (2 * q)
        cw = math.cos(w)
        a0 = 1 + a
        b0, b2 = a / a0, -a / a0
        a1, a2 = -2 * cw / a0, (1 - a) / a0
        xi = x[i]
        yi = b0 * xi + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


def chirp(d, f0, f1, curve=1.0):
    t = t_axis(d)
    k = (t / d) ** curve
    f = f0 * (f1 / f0) ** k
    return np.sin(2 * math.pi * np.cumsum(f) / SR)


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def place(at, mono, gain=1.0, pan=0.0, pan_to=None):
    """Drop a mono sound into the stereo mix; pan -1..1 (optionally swept)."""
    s = int(at * SR)
    n = min(len(mono), mix.shape[1] - s)
    m = mono[:n] * gain
    p = np.full(n, pan) if pan_to is None else np.linspace(pan, pan_to, n)
    ang = (p + 1) * math.pi / 4
    mix[0, s:s + n] += m * np.cos(ang)
    mix[1, s:s + n] += m * np.sin(ang)


# ---------------------------------------------------------------- sounds
def boom(d=1.4, f0=110, f1=38):
    body = chirp(d, f0, f1, 0.35) * env_exp(d, 0.35)
    sub = np.tanh(2.2 * body)
    click = fft_filter(noise(d), lo=1500, hi=12000) * env_exp(d, 0.006)
    thump = fft_filter(noise(d), hi=400) * env_exp(d, 0.06)
    return norm(sub + 0.5 * click + 0.6 * thump)


def impact(d=0.7):
    """Text slam: punchy boom + bright crack."""
    b = boom(d, 150, 45) * 0.9
    crack = fft_filter(noise(d), lo=1800, hi=9000) * env_exp(d, 0.035)
    return norm(b + 0.7 * crack)


def whoosh(d=0.6, f0=400, f1=4000, peak=0.65):
    t = t_axis(d) / d
    e = np.where(t < peak, (t / peak) ** 2, ((1 - t) / (1 - peak)) ** 1.5)
    return norm(swept_bandpass(noise(d), f0, f1, 1.1) * e)


def riser(d=0.6):
    t = t_axis(d) / d
    n = swept_bandpass(noise(d), 300, 7000, 2.0)
    tone = chirp(d, 200, 1600, 2.0) * 0.25
    return norm((n + tone) * t ** 2.2)


def cut_hit():
    """Scene-transition hit: short boom + white-noise flash."""
    d = 0.9
    fl = fft_filter(noise(d), lo=600, hi=11000) * env_exp(d, 0.09)
    return norm(boom(d, 130, 40) + 0.55 * fl)


def ping(f, d=0.5, tau=0.12):
    t = t_axis(d)
    return np.sin(2 * math.pi * f * t) * np.exp(-t / tau)


def sparkle(d=1.0, count=9):
    out = np.zeros(int(SR * d))
    for i in range(count):
        at = int(SR * d * 0.7 * i / count)
        p = ping(rng.uniform(2600, 6200), 0.3, 0.05) * rng.uniform(.4, 1)
        out[at:at + len(p)] += p[:len(out) - at]
    return norm(out)


def tick(f=2400, d=0.05):
    t = t_axis(d)
    return norm(np.sin(2 * math.pi * f * t) * np.exp(-t / 0.008)
                + 0.4 * fft_filter(noise(d), lo=3000) * np.exp(-t / 0.003))


def shutter():
    d = 0.18
    out = np.zeros(int(SR * d))
    for at, f in ((0, 3200), (0.055, 2600)):
        c = fft_filter(noise(0.06), lo=f * .6, hi=f * 1.8) * env_exp(0.06, 0.012)
        s = int(at * SR)
        out[s:s + len(c)] += c
    return norm(out)


def power_up(d=1.1):
    t = t_axis(d)
    f = 70 * (900 / 70) ** ((t / d) ** 1.6)
    ph = 2 * math.pi * np.cumsum(f) / SR
    saw = sum(np.sin(k * ph) / k for k in range(1, 9))
    e = np.minimum(t / 0.05, 1) * np.where(t > d - 0.25, (d - t) / 0.25, 1)
    body = fft_filter(saw, hi=2500) * e
    return norm(body + 0.6 * boom(d, 90, 35))


def bell(f, d=1.6, tau=0.45):
    t = t_axis(d)
    parts = ((1, 1), (2.76, .45), (5.40, .25), (8.93, .12))
    return norm(sum(a * np.sin(2 * math.pi * f * r * t) * np.exp(-t / (tau / r ** .5))
                    for r, a in parts))


def pop(d=0.12):
    t = t_axis(d)
    return norm(chirp(d, 900, 180, 0.4) * np.exp(-t / 0.03)
                + 0.3 * fft_filter(noise(d), lo=2000) * np.exp(-t / 0.004))


def rumble(d=0.35):
    return norm(fft_filter(noise(d), hi=180) * np.hanning(int(SR * d)))


# -------------------------------------------- counter tick timing (39 hrs)
def bezier_progress(x1, y1, x2, y2, u):
    """CSS cubic-bezier: map time fraction u -> progress."""
    s = np.linspace(0, 1, 4001)
    bx = 3 * x1 * s * (1 - s) ** 2 + 3 * x2 * s ** 2 * (1 - s) + s ** 3
    by = 3 * y1 * s * (1 - s) ** 2 + 3 * y2 * s ** 2 * (1 - s) + s ** 3
    return np.interp(u, bx, by)


def counter_ticks(start=9.6, dur=1.5, to=39):
    u = np.linspace(0, 1, 3001)
    vals = np.round(bezier_progress(.2, .7, .2, 1, u) * to)
    return [start + u[i] * dur for i in range(1, len(u)) if vals[i] != vals[i - 1]]


# ---------------------------------------------------------------- cue sheet
def build():
    # S1 hook 0–2s
    place(0.05, impact(), 1.0)                      # WAIT.
    place(0.95, whoosh(0.4, 600, 3000), 0.35, -0.6, 0.6)  # "your phone just got"
    place(1.30, boom(1.6, 160, 32), 1.0)            # OLD.
    place(1.30, impact(), 0.7)
    place(1.60, rumble(), 0.6)                      # shake
    place(1.40, riser(0.55), 0.45)                  # into the cut
    # S2 reveal 2–5s
    place(1.95, cut_hit(), 0.9)
    place(2.05, whoosh(1.3, 200, 2600, 0.45), 0.75, -0.7, 0.3)  # phone swings in
    place(2.30, tick(1800), 0.25)                   # "Introducing"
    place(2.45, whoosh(0.5, 800, 5000), 0.3)        # title rise
    place(3.30, sparkle(1.2), 0.35, -0.5, 0.6)      # light sweep on phone
    place(4.40, riser(0.55), 0.35)
    # S3 camera 5–7.5s
    place(4.95, cut_hit(), 0.85)
    place(5.00, shutter(), 0.8, 0.2)                # camera zoom-in
    place(5.15, impact(), 0.75)                     # 48MP x3
    for i, pd in enumerate((5.9, 6.15, 6.4, 6.65, 6.9)):   # zoom pills
        place(pd + 0.1, tick(1500 * 1.19 ** i), 0.45, -0.6 + 0.3 * i)
    place(6.95, ping(1980, 0.8, 0.2), 0.25)         # 8x lands
    place(7.00, riser(0.45), 0.35)
    # S4 chip 7.5–9.5s
    place(7.45, cut_hit(), 0.85)
    place(7.55, power_up(), 0.7)                    # chip powers up
    place(8.00, whoosh(0.5, 500, 4000), 0.3)        # "Unreal speed."
    place(8.65, sparkle(0.8, 6), 0.25)
    # S5 battery 9.5–11.5s
    place(9.45, whoosh(0.35, 3000, 400), 0.5)
    for i, at in enumerate(counter_ticks()):        # 0 -> 39 counter
        place(at, tick(1700 + 30 * i, 0.04), 0.28, 0.4 * math.sin(i))
    place(9.6, chirp(1.5, 180, 720, 0.6) * np.linspace(0.2, 1, int(SR * 1.5)) ** 2, 0.08)
    place(11.10, bell(1568, 1.4), 0.4)              # fully charged
    place(11.10, bell(2093, 1.2), 0.2)
    # S6 colours 11.5–13s
    place(11.45, cut_hit(), 0.8)
    place(11.50, impact(), 0.5)                     # Pick your flex.
    place(11.55, whoosh(0.55, 300, 3000), 0.55, -1, -0.3)  # Deep Blue
    place(11.65, whoosh(0.55, 250, 2500), 0.55, 0, 0)      # Cosmic Orange
    place(11.75, whoosh(0.55, 300, 3000), 0.55, 1, 0.3)    # Silver
    place(12.10, sparkle(0.9, 7), 0.35)
    place(12.55, riser(0.4), 0.3)
    # S7 CTA 13–15s
    place(12.95, whoosh(0.6, 2500, 300, 0.3), 0.55)
    place(13.00, boom(1.6, 100, 30), 0.6)
    place(13.60, pop(), 0.8)                        # Shop now button
    place(13.65, bell(1046, 1.4), 0.3)
    place(13.85, bell(1568, 1.2), 0.25)
    place(14.20, tick(2600), 0.2)                   # button nudge


def write(path):
    out = mix[:, :int(SR * DUR)]
    out = np.tanh(1.3 * out / (np.max(np.abs(out)) or 1)) / math.tanh(1.3)  # soft limit
    out *= 10 ** (-1 / 20)                                                 # -1 dBFS
    fade = int(0.25 * SR)
    out[:, -fade:] *= np.linspace(1, 0, fade)
    pcm = (out.T * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    build()
    write(sys.argv[1] if len(sys.argv) > 1 else "sfx.wav")
    print("wrote", sys.argv[1] if len(sys.argv) > 1 else "sfx.wav")
