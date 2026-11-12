#!/usr/bin/env python3
"""Generate the narration with Kokoro (open-weight neural TTS, Apache-2.0)
and write the scene timeline the animation + sound design are built on.

Outputs: voice.wav (48 kHz mono), timeline.json, timeline.js
Usage: python3 voiceover.py /path/to/kokoro-v1.0.int8.onnx /path/to/voices-v1.0.bin
Model files: github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
"""
import json
import sys

import numpy as np
from kokoro_onnx import Kokoro

SR = 48_000
VOICE, SPEED = "af_heart", 1.05
LEAD_IN = 0.9    # seconds before the first word (hook SFX land here)
GAP = 0.55       # breath between lines inside a scene
SCENE_GAP = 0.85 # pause at scene changes (transition hits land here)
TAIL = 2.6       # end card hold after the last word

# (scene id, [lines])
SCRIPT = [
    ("hook",    ["How did a pair of tiny white earbuds become one of the most famous gadgets on the planet?"]),
    ("jack",    ["September, 2016. Apple pulled the headphone jack out of the iPhone 7,",
                 "and called it courage. People were furious."]),
    ("launch",  ["On the same stage, Apple revealed AirPods. A hundred and fifty-nine dollars.",
                 "The internet laughed. They looked like electric toothbrush heads, and everyone said you'd lose them."]),
    ("magic",   ["Then people actually tried them. Open the case, and they just connect.",
                 "No cables. No tangles. A custom wireless chip made pairing feel like magic."]),
    ("status",  ["And those little white stems were impossible to miss.",
                 "They became a status symbol, and every meme about them was free advertising."]),
    ("growth",  ["Then came AirPods Pro, with active noise cancellation.",
                 "By 2019, analysts estimated around sixty million pairs were sold in a single year."]),
    ("outro",   ["So how did AirPods get so famous? Perfect timing, effortless design, and a look everyone recognises.",
                 "Tiny earbuds. Massive impact."]),
]


def resample(x, sr_in):
    n = int(round(len(x) * SR / sr_in))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(idx[0] - 240, 0): idx[-1] + 2400] if len(idx) else x


def main():
    model, voices = sys.argv[1], sys.argv[2]
    k = Kokoro(model, voices)
    clips, scenes, lines, t = [], [], [], LEAD_IN
    for si, (sid, texts) in enumerate(SCRIPT):
        if si:
            t += SCENE_GAP
        start = t if si else 0.0
        for li, text in enumerate(texts):
            if li:
                t += GAP
            s, sr = k.create(text, voice=VOICE, speed=SPEED, lang="en-us")
            a = trim(resample(np.asarray(s, dtype=np.float64), sr))
            clips.append((t, a))
            lines.append({"scene": sid, "text": text, "start": round(t, 3), "end": round(t + len(a) / SR, 3)})
            t += len(a) / SR
        scenes.append({"id": sid, "start": round(start, 3), "end": None})
    total = t + TAIL
    for i, sc in enumerate(scenes):
        sc["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else round(total, 3)
        sc["start"] = sc["start"] if i == 0 else round(sc["start"] - SCENE_GAP * 0.5, 3)
    for i in range(len(scenes) - 1):
        scenes[i]["end"] = scenes[i + 1]["start"]

    out = np.zeros(int(total * SR) + 1)
    for at, a in clips:
        s = int(at * SR)
        out[s:s + len(a)] += a[:len(out) - s]
    out = out / np.max(np.abs(out)) * 0.89
    import wave
    with wave.open("voice.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype("<i2").tobytes())

    tl = {"duration": round(total, 3), "scenes": scenes, "lines": lines}
    json.dump(tl, open("timeline.json", "w"), indent=2)
    open("timeline.js", "w").write("window.TIMELINE = " + json.dumps(tl) + ";\n")
    for sc in scenes:
        print(f"{sc['id']:8s} {sc['start']:6.2f} -> {sc['end']:6.2f}")
    print(f"total {total:.2f}s")


if __name__ == "__main__":
    main()
