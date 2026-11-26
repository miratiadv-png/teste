// usage: node rec2.js page.html timeline.json outDir fps workers [t1,t2,... stills]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [, , html, tlp, outDir, fpsA, wA, stillsA] = process.argv;
const tl = JSON.parse(fs.readFileSync(tlp, 'utf8')); const fps = Number(fpsA);
fs.mkdirSync(outDir, { recursive: true });
(async () => {
  const br = await chromium.launch();
  let frames;
  if (stillsA && stillsA.startsWith('f:')) { frames = []; for (const r of stillsA.slice(2).split(',')) { const [a, b] = r.split('-').map(Number); for (let i = a; i <= (b ?? a); i++) frames.push([`f_${String(i).padStart(5, '0')}.jpg`, i / fps]); } }
  else if (stillsA) frames = stillsA.split(',').map(Number).map((t, i) => [`still_${i}.png`, t]);
  else { const n = Math.round(tl.total * fps); frames = Array.from({ length: n }, (_, i) => [`f_${String(i).padStart(5, '0')}.jpg`, i / fps]); }
  const W = Number(wA || 1);
  const t0 = Date.now();
  await Promise.all(Array.from({ length: W }, async (_, k) => {
    const p = await br.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    p.on('pageerror', e => console.error('PAGE ERROR', e.message));
    await p.goto('file://' + path.resolve(html));
    await p.evaluate(() => document.fonts.ready);
    await p.evaluate(t => window.setup(t), tl);
    for (let i = k; i < frames.length; i += W) {
      const [name, t] = frames[i];
      await p.evaluate(t => window.render(t), t);
      await p.evaluate(() => window.ready());
      await p.screenshot({ path: path.join(outDir, name), type: name.endsWith('.png') ? 'png' : 'jpeg', quality: name.endsWith('.png') ? undefined : 92 });
      if (k === 0 && i % 300 === 0) console.log(`${i}/${frames.length} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    await p.close();
  }));
  console.log('done', frames.length, ((Date.now() - t0) / 1000).toFixed(1) + 's');
  await br.close();
})();
