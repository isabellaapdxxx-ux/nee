# How AirPods Got So Famous — narrated explainer (67s, 9:16)

| File | What it is |
|---|---|
| `how-airpods-got-famous.mp4` | Final video: 1080×1920, 30fps, H.264 + AAC, loudness-normalised to −14 LUFS |
| `index.html` | The animation, pure HTML/CSS. Open it in a browser and click to play with sound |
| `voiceover.py` | Generates the narration with Kokoro (open-weight neural TTS) and writes `timeline.json` / `timeline.js` |
| `audio.py` | Mixes the narration, synthesised SFX (reusing `../sfx.py`) and a synthesised music bed that ducks under the voice, into `mix.wav` |
| `render.mjs` | Renders `index.html` + `mix.wav` to the MP4 |

Every animation is placed on a word of the narration (`data-at="L4:toothbrush"`),
so if you edit the script and regenerate the voice, the visuals and sound effects re-sync on their own.

## Story
| ~Time | Scene | Narration |
|---|---|---|
| 0–6s | Hook | How did tiny white earbuds become one of the most famous gadgets on the planet? |
| 6–15s | 2016 | The headphone jack is removed from the iPhone 7, "courage", people are furious |
| 15–26s | Launch | AirPods revealed at $159, and the internet mocks them (toothbrush heads, "you'll lose them") |
| 26–36s | The magic | Open the case and they connect. No cables, no tangles, the W1 chip |
| 36–44s | Status | The white stems become a status symbol, and the memes are free advertising |
| 44–55s | Growth | AirPods Pro with noise cancellation, then ~60M pairs a year (analyst estimate, 2019) |
| 55–67s | Outro | Perfect timing, effortless design, an iconic look. "Tiny earbuds. Massive impact." |

## Sound
- **Voice:** Kokoro `af_heart`, burned-in karaoke captions highlight each word as it's spoken
- **SFX:** cut hits on every scene change, a "thwip" when the plug is yanked, a stamp boom on "COURAGE", pops for the angry reactions, a cash-register bell on $159, a crowd-laugh texture, a lid click and "connected" chime, a chip power-up, ticks as the crowd fills in, noise that fades out for ANC, a counter run to 60M, and a big boom on "Massive impact."
- **Music:** a synthesised 96 BPM lo-fi bed (pad, bass, plucks, light drums) that drops ~8 dB while the narrator talks

All sound is generated from code, so there's nothing to license.

## Rebuild
```bash
pip install kokoro-onnx numpy
# model files: github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0)
python3 voiceover.py kokoro-v1.0.int8.onnx voices-v1.0.bin   # only if you change the script
node render.mjs                                               # re-mixes audio + renders MP4
```
