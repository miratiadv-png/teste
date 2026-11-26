// usage: node rec.js page.html out.mp4 duration fps   |   node rec.js page.html stills.jpg t1,t2,...
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const [, , html, out, a, b] = process.argv;
(async () => {
  const br = await chromium.launch();
  const p = await br.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await p.goto('file://' + path.resolve(html));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  if (out.endsWith('.jpg')) {
    const ts = a.split(',').map(Number), shots = [];
    for (const t of ts) { await p.evaluate(t => window.render(t), t); shots.push(await p.screenshot({ type: 'png' })); }
    const fs = require('fs'); const dir = path.dirname(out);
    shots.forEach((s, i) => fs.writeFileSync(path.join(dir, `_st_${i}.png`), s));
  } else {
    const dur = Number(a), fps = Number(b || 30), n = Math.round(dur * fps);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      await p.evaluate(t => window.render(t), i / fps);
      const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log('frames', n);
  }
  await br.close();
})();
