// Renders index.html + mix.wav to an MP4 (1080x1920, 30fps, H.264 + AAC, ~-14 LUFS).
// Usage: node render.mjs [out.mp4]   (run voiceover.py once first; this re-runs audio.py)
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn, execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const FPS = 30;
const out = process.argv[2] || 'how-airpods-got-famous.mp4';
const url = pathToFileURL(path.resolve('index.html')).href + '?capture';

execFileSync('python3', ['audio.py'], { stdio: 'inherit' });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(url, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
const dur = await page.evaluate(() => window.AD_DURATION);
const frames = Math.round((dur / 1000) * FPS);

const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-i', 'mix.wav', '-map', '0:v', '-map', '1:a',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
  '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000',
  '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
  { stdio: ['pipe', 'inherit', 'inherit'] });

for (let i = 0; i < frames; i++) {
  await page.evaluate(ms => window.seek(ms), (i * 1000) / FPS);
  const png = await page.screenshot({ type: 'png' });
  if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % 60 === 0) process.stdout.write(`\rframe ${i}/${frames}`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log(`\nwrote ${out}`);
