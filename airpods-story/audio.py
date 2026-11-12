#!/usr/bin/env python3
"""Build the final soundtrack: narration + synthesized SFX + a synthesized
music bed that ducks under the voice. Nothing is sampled, nothing to license.

Reads voice.wav + timeline.json (from voiceover.py), writes mix.wav
(48 kHz stereo). SFX generators are reused from ../sfx.py.
Usage: python3 audio.py
"""
import json
import math
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sfx as fx  # noqa: E402  (sound generators: boom, whoosh, riser, ...)

SR = fx.SR
TL = json.load(open("timeline.json"))
DUR = TL["duration"]
N = int(DUR * SR)
sfx = np.zeros((2, N + SR))
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- cues
def word_time(li, word):
    line = TL["lines"][li]
    i = line["text"].lower().find(word.lower())
    assert i >= 0, (word, line["text"])
    return line["start"] + i / len(line["text"]) * (line["end"] - line["start"])


def L(li, word=None, off=0.0):
    return (word_time(li, word) if word else TL["lines"][li]["start"]) + off


def S(sid):
    return next(s["start"] for s in TL["scenes"] if s["id"] == sid)


def place(at, mono, gain=1.0, pan=0.0, pan_to=None):
    s = max(int(at * SR), 0)
    n = min(len(mono), sfx.shape[1] - s)
    m = mono[:n] * gain
    p = np.full(n, pan) if pan_to is None else np.linspace(pan, pan_to, n)
    ang = (p + 1) * math.pi / 4
    sfx[0, s:s + n] += m * np.cos(ang)
    sfx[1, s:s + n] += m * np.sin(ang)


def unplug():
    """Cartoon 'thwip' as the headphone plug is yanked out."""
    d = 0.35
    t = fx.t_axis(d)
    return fx.norm(fx.chirp(d, 300, 1400, 0.5) * np.exp(-t / 0.08)
                   + 0.5 * fx.fft_filter(fx.noise(d), lo=1500) * np.exp(-t / 0.02))


def notif():
    """Soft two-note 'connected' chime."""
    a = fx.bell(1318, 0.9, 0.3)
    b = fx.bell(1760, 1.0, 0.35)
    out = np.zeros(int(SR * 1.2))
    out[:len(a)] += a
    out[int(.12 * SR):int(.12 * SR) + len(b)] += b
    return fx.norm(out)


def lid_click():
    d = 0.08
    t = fx.t_axis(d)
    return fx.norm(fx.fft_filter(fx.noise(d), lo=1200, hi=6000) * np.exp(-t / 0.006)
                   + 0.6 * np.sin(2 * math.pi * 420 * t) * np.exp(-t / 0.015))


def crowd_laugh(d=2.2):
    """Abstract crowd 'laugh' texture: many short formant-ish 'ha' bursts."""
    out = np.zeros(int(SR * d))
    for _ in range(70):
        at = int(rng.uniform(0, d - 0.25) * SR)
        f = rng.uniform(180, 340)
        hd = rng.uniform(0.08, 0.14)
        for k in range(rng.integers(2, 5)):
            s = at + int(k * hd * 1.25 * SR)
            t = fx.t_axis(hd)
            v = np.sin(2 * math.pi * f * t) + 0.5 * np.sin(2 * math.pi * f * 2.9 * t)
            v *= np.sin(math.pi * t / hd) ** 2
            v = v + 0.25 * fx.noise(hd) * np.sin(math.pi * t / hd)
            if s + len(v) < len(out):
                out[s:s + len(v)] += v * rng.uniform(.3, 1)
    env = np.minimum(fx.t_axis(d) / 0.15, 1) * np.linspace(1, 0, int(SR * d)) ** 0.7
    return fx.norm(fx.fft_filter(out, lo=150, hi=4000) * env)


def cash():
    return fx.norm(fx.bell(2637, 0.8, 0.18) + 0.7 * fx.bell(3520, 0.8, 0.15))


def build_sfx():
    # 1 hook
    place(0.0, fx.riser(0.9), 0.35)
    place(L(0, "tiny"), fx.sparkle(1.0, 8), 0.35, -0.4, 0.5)
    place(L(0, "tiny", -0.05), fx.whoosh(0.5, 300, 3500), 0.4)
    place(L(0, "famous"), fx.impact(), 0.75)
    place(L(0, "planet"), fx.impact(), 0.7)
    place(TL["lines"][0]["end"] - 0.2, fx.riser(0.5), 0.3)
    # 2 jack
    place(S("jack"), fx.cut_hit(), 0.8)
    place(L(1, "2016"), fx.impact(), 0.75)
    place(L(1, "Apple"), fx.whoosh(0.5, 2000, 300), 0.4)
    place(L(1, "jack", -0.05), unplug(), 0.6, 0, 0.5)
    place(L(2, "courage", -0.05), fx.boom(1.4, 140, 35), 0.9)
    place(L(2, "courage", -0.05), fx.impact(), 0.6)
    place(L(2, "courage"), fx.rumble(0.4), 0.5)
    for i, w in enumerate(("People", "were", "furious")):
        place(L(2, w), fx.pop(), 0.6, (-0.5, 0.5, -0.2)[i])
    place(L(2, "furious", 0.2), fx.pop(), 0.5, 0.5)
    # 3 launch
    place(S("launch"), fx.cut_hit(), 0.8)
    place(L(3, "revealed", -0.1), fx.whoosh(0.9, 200, 3000, 0.5), 0.6)
    place(L(3, "revealed", 0.2), fx.sparkle(1.3, 10), 0.4, -0.6, 0.6)
    place(L(3, "hundred"), fx.impact(), 0.55)
    place(L(3, "hundred", 0.05), cash(), 0.35)
    place(L(4), fx.boom(0.9, 120, 40), 0.5)
    place(L(4, "laughed", -0.1), crowd_laugh(), 0.32)
    place(L(4, "toothbrush", -0.3), fx.whoosh(0.4, 500, 3000), 0.4, -0.8, 0)
    place(L(4, "everyone"), fx.whoosh(0.4, 500, 3000), 0.4, 0.8, 0)
    place(L(4, "lose"), fx.whoosh(0.4, 500, 3000), 0.4, -0.8, 0)
    # 4 magic
    place(S("magic"), fx.cut_hit(), 0.7)
    place(L(5), fx.pop(), 0.5)
    place(L(5, "Open"), lid_click(), 0.8)
    place(L(5, "case", 0.2), fx.whoosh(0.7, 600, 5000), 0.35)
    place(L(5, "connect", -0.15), notif(), 0.55)
    place(L(5, "connect", -0.1), fx.whoosh(0.5, 3000, 600), 0.3)
    place(L(6, "cables"), fx.impact(), 0.55)
    place(L(6, "cables", 0.25), fx.whoosh(0.25, 2000, 6000), 0.4, -0.6, 0.6)
    place(L(6, "tangles"), fx.impact(), 0.55)
    place(L(6, "tangles", 0.25), fx.whoosh(0.25, 2000, 6000), 0.4, 0.6, -0.6)
    place(L(6, "chip", -0.2), fx.power_up(), 0.55)
    place(L(6, "magic"), fx.sparkle(1.2, 10), 0.45, -0.5, 0.5)
    # 5 status
    place(S("status"), fx.cut_hit(), 0.7)
    place(L(7, "white"), fx.impact(), 0.5)
    for i in range(14):
        place(L(7, "stems", i * 0.11), fx.tick(1600 + 70 * i, 0.05), 0.3, -0.7 + 0.1 * i)
    place(L(8, "status", -0.2), fx.boom(1.2, 130, 38), 0.8)
    place(L(8, "status", -0.15), fx.sparkle(0.9, 7), 0.35)
    place(L(8, "meme", -0.2), fx.whoosh(0.4, 400, 3000), 0.4)
    place(L(8, "free"), fx.impact(), 0.65)
    place(L(8, "free", 0.05), cash(), 0.35)
    # 6 growth
    place(S("growth"), fx.cut_hit(), 0.7)
    place(L(9, "AirPods", -0.05), fx.whoosh(0.6, 300, 4000), 0.4)
    place(L(9, "Pro"), fx.sparkle(1.0, 8), 0.4)
    d = 1.0  # noise collapsing to silence as ANC kicks in
    place(L(9, "cancellation", -0.6), fx.fft_filter(fx.noise(d), lo=200, hi=3000)
          * np.linspace(0.3, 1, int(SR * d)) ** 2 * np.r_[np.ones(int(SR * .6)), np.linspace(1, 0, int(SR * .4))], 0.25)
    place(L(9, "cancellation", 0.3), fx.ping(880, 0.6, 0.18), 0.25)
    for i in range(4):
        place(L(10, None, 0.1 + 0.2 * i) if i < 3 else L(10, "analysts"), fx.tick(1200 * 1.25 ** i, 0.06), 0.45)
    place(L(10, "sixty", -0.1), fx.boom(1.3, 120, 34), 0.85)
    place(L(10, "sixty", -0.1), fx.impact(), 0.5)
    for k in range(18):  # counter ticks, easing out
        place(L(10, "sixty", -0.1) + 1.4 * (k / 18) ** 1.8, fx.tick(1800 + 40 * k, 0.04), 0.2)
    place(L(10, "sixty", 1.3), fx.bell(1568, 1.2), 0.3)
    # 7 outro
    place(S("outro"), fx.cut_hit(), 0.7)
    place(L(11, "timing", -0.2), fx.whoosh(0.45, 400, 3500), 0.45, -0.8, 0)
    place(L(11, "effortless", -0.1), fx.whoosh(0.45, 400, 3500), 0.45, 0.8, 0)
    place(L(11, "look", -0.1), fx.whoosh(0.45, 400, 3500), 0.45, -0.8, 0)
    place(L(12, None, -0.6), fx.riser(0.6), 0.4)
    place(L(12), fx.boom(1.6, 100, 30), 0.75)
    place(L(12), fx.sparkle(1.4, 10), 0.4, -0.5, 0.5)
    place(L(12, "earbuds", -0.25), fx.impact(), 0.5)
    place(L(12, "Massive", -0.05), fx.boom(2.0, 120, 28), 1.0)
    place(L(12, "Massive", -0.05), fx.impact(), 0.7)
    place(L(12, "Massive", 0.3), fx.bell(1046, 2.0, 0.7), 0.3)
    place(L(12, "Massive", 0.45), fx.bell(1568, 1.8, 0.6), 0.22)


# ---------------------------------------------------------------- music bed
BPM = 96
BEAT = 60 / BPM


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def music():
    out = np.zeros((2, N + SR))
    # Fmaj7 - Am7 - Dm9 - Bbmaj7 (one bar each, 4 beats)
    chords = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 57, 60, 64], [46, 53, 57, 62]]
    bar = 4 * BEAT
    nbars = int(DUR / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        ch = chords[b % 4]
        # warm pad
        d = bar + 0.6
        t = fx.t_axis(d)
        env = np.minimum(t / 0.5, 1) * np.minimum((d - t) / 0.6, 1)
        pad = sum(np.sin(2 * math.pi * note(m + 12) * t + i) * (0.6 if i else 1) +
                  0.3 * np.sin(2 * math.pi * note(m + 12) * 1.003 * t) for i, m in enumerate(ch))
        pad = fx.fft_filter(pad, hi=2200) * env * 0.06
        s = int(t0 * SR)
        n = min(len(pad), out.shape[1] - s)
        if n <= 0:
            break
        out[0, s:s + n] += pad[:n]
        out[1, s:s + n] += np.roll(pad, 240)[:n]
        # bass
        for k in (0, 2.5):
            bd = 1.2
            bt = fx.t_axis(bd)
            bs = np.tanh(1.5 * np.sin(2 * math.pi * note(ch[0] - 12) * bt)) * np.exp(-bt / 0.5) * 0.16
            ss = int((t0 + k * BEAT) * SR)
            nn = min(len(bs), out.shape[1] - ss)
            if nn > 0:
                out[:, ss:ss + nn] += bs[:nn]
        # pluck arpeggio on 8ths
        for k in range(8):
            m = ch[[0, 1, 2, 3, 2, 1, 3, 2][k]] + 24
            pd = 0.35
            pt = fx.t_axis(pd)
            pl = (np.sin(2 * math.pi * note(m) * pt) + 0.3 * np.sin(4 * math.pi * note(m) * pt)) * np.exp(-pt / 0.09) * 0.035
            ss = int((t0 + k * BEAT / 2) * SR)
            nn = min(len(pl), out.shape[1] - ss)
            pan = 0.5 * math.sin(k * 1.3)
            if nn > 0:
                out[0, ss:ss + nn] += pl[:nn] * (1 - pan) * 0.7
                out[1, ss:ss + nn] += pl[:nn] * (1 + pan) * 0.7
        # drums (start after the hook)
        if t0 >= S("jack") - 0.1:
            for k in range(4):
                bt = t0 + k * BEAT
                kd = fx.boom(0.35, 120, 45) * 0.22
                ss = int(bt * SR)
                nn = min(len(kd), out.shape[1] - ss)
                if nn > 0 and k in (0, 2):
                    out[:, ss:ss + nn] += kd[:nn]
                if k in (1, 3):  # soft clap/snare
                    sd = 0.2
                    sn = fx.fft_filter(fx.noise(sd), lo=900, hi=7000) * fx.env_exp(sd, 0.045) * 0.09
                    nn = min(len(sn), out.shape[1] - ss)
                    if nn > 0:
                        out[:, ss:ss + nn] += sn[:nn]
                for h in (0, 0.5):  # hats
                    hd = 0.05
                    hh = fx.fft_filter(fx.noise(hd), lo=7000) * fx.env_exp(hd, 0.01) * 0.04
                    ss = int((bt + h * BEAT) * SR)
                    nn = min(len(hh), out.shape[1] - ss)
                    if nn > 0:
                        out[0, ss:ss + nn] += hh[:nn] * 0.8
                        out[1, ss:ss + nn] += hh[:nn]
    return out[:, :N]


def read_mono(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768
    y = np.zeros(N)
    y[:min(N, len(x))] = x[:N]
    return y


def smooth_env(x, attack=0.02, release=0.35):
    """Envelope follower used to duck the music under the narration."""
    a = np.abs(x)
    blk = int(0.01 * SR)
    nb = len(a) // blk + 1
    pk = np.array([a[i * blk:(i + 1) * blk].max() if i * blk < len(a) else 0 for i in range(nb)])
    env = np.zeros(nb)
    ca, cr = math.exp(-0.01 / attack), math.exp(-0.01 / release)
    v = 0.0
    for i, p in enumerate(pk):
        v = ca * v + (1 - ca) * p if p > v else cr * v + (1 - cr) * p
        env[i] = v
    return np.repeat(env, blk)[:len(a)]


def main():
    build_sfx()
    voice = read_mono("voice.wav")
    mus = music()
    env = smooth_env(voice)
    duck = 1 - 0.6 * np.clip(env / 0.15, 0, 1)          # ~-8 dB under speech
    mus *= duck
    fade = int(1.0 * SR)
    mus[:, -fade:] *= np.linspace(1, 0, fade)
    s = sfx[:, :N] * 0.42
    v = np.vstack([voice, voice]) * 1.0
    mix = v + s + mus * 0.32
    mix = np.tanh(1.2 * mix / (np.max(np.abs(mix)) or 1)) / math.tanh(1.2)
    mix *= 10 ** (-1 / 20)
    f = int(0.4 * SR)
    mix[:, -f:] *= np.linspace(1, 0, f)
    with wave.open("mix.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype("<i2").tobytes())
    print(f"wrote mix.wav ({DUR:.1f}s)")


if __name__ == "__main__":
    main()
