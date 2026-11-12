// Renders index.html to a TikTok-ready MP4 (1080x1920, 30fps, H.264).
// Usage: node render.mjs [out.mp4]
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const FPS = 30;
const out = process.argv[2] || 'iphone17promax-tiktok.mp4';
const url = pathToFileURL(path.resolve('index.html')).href + '?capture';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(url, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
const dur = await page.evaluate(() => window.AD_DURATION);
const frames = Math.round((dur / 1000) * FPS);

const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
  { stdio: ['pipe', 'inherit', 'inherit'] });

for (let i = 0; i < frames; i++) {
  await page.evaluate(ms => window.seek(ms), (i * 1000) / FPS);
  ff.stdin.write(await page.screenshot({ type: 'png' }));
  if (i % 30 === 0) process.stdout.write(`\rframe ${i}/${frames}`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log(`\nwrote ${out}`);
