# iPhone 17 Pro Max — TikTok ad (15s, 9:16)

| File | What it is |
|---|---|
| `index.html` | The ad itself: 1080×1920, pure HTML/CSS, loops in any browser |
| `render.mjs` | Renders the ad to a TikTok-ready MP4 (H.264, 30fps) |
| `iphone17promax-tiktok.mp4` | Pre-rendered video, ready to upload |

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
Open `index.html` in a browser. **Space** pauses, **←/→** scrubs, **S** shows TikTok's UI safe zones.

## Re-render the MP4
```bash
node render.mjs            # needs Playwright + ffmpeg
```

Tip: the video has no audio, so add a trending sound in TikTok's editor. Beat drops line up with the cuts at 2s, 5s, 7.5s and 11.5s.
