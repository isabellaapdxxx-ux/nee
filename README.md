# iPhone 17 Pro Max — TikTok ad (15s, 9:16)

| File | What it is |
|---|---|
| `index.html` | The ad itself: 1080×1920, pure HTML/CSS, loops in any browser |
| `sfx.py` | Synthesises the sound-effects track `sfx.wav` from scratch (no samples, nothing to license) |
| `sfx.wav` | The generated SFX track (also played by the browser preview) |
| `render.mjs` | Renders the ad + SFX to a TikTok-ready MP4 (H.264 + AAC, 30fps) |
| `iphone17promax-tiktok.mp4` | Pre-rendered video with sound, ready to upload |

## Storyboard
| Time | Scene |
|---|---|
| 0–2s | Hook: **"WAIT. your phone just got OLD."** |
| 2–5s | Phone reveal in Cosmic Orange |
| 5–7.5s | 48MP ×3 Pro Fusion cameras, 0.5×→8× zoom |
| 7.5–9.5s | A19 Pro chip, vapor-chamber cooling |
| 9.5–11.5s | Up to 39 hrs video playback, battery fill |
| 11.5–13s | Colours: Deep Blue / Cosmic Orange / Silver |
| 13–15s | CTA: From $1,199 · **Shop now** |

## Preview
Open `index.html` in a browser and **click** to play with sound. **M** mutes, **Space** pauses, **←/→** scrubs, **S** shows TikTok's UI safe zones.

## Re-render the MP4
```bash
node render.mjs            # needs Playwright, ffmpeg, python3 + numpy
python3 sfx.py             # just regenerate the audio
```

## Sound design
| Time | SFX |
|---|---|
| 0.05s / 1.3s | Slam impacts on "WAIT." and "OLD." + rumble on the shake |
| 1.4s | Riser into the first cut |
| 2, 5, 7.5, 11.5s | Boom + white-flash hit on every scene cut |
| 2.05s | Long whoosh as the phone swings in, sparkle on the light sweep |
| 5.0s | Camera shutter, then rising UI ticks on each zoom pill (.5× → 8×) |
| 7.55s | Synth power-up as the A19 Pro chip lights |
| 9.6–11.1s | One tick per number as the counter runs 0 → 39, then a "charged" bell |
| 11.55s | Three panned whooshes as the colour phones fly in |
| 13.6s | Pop on the Shop now button + two-note chime |

Mastered to about −13 LUFS with peaks around −1 dBFS. To add a trending sound on top, lower "Original sound" in TikTok's volume settings so the effects sit under the music.
