const { chromium } = require('playwright');
const path = require('path');
const [, , html, outDir] = process.argv;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 2000 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(html));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  const info = await p.evaluate(() => [...document.querySelectorAll('.slide')].map(s => {
    const r = s.getBoundingClientRect(), w = s.querySelector('.wrap').getBoundingClientRect(), f = s.querySelector('.foot').getBoundingClientRect();
    return `${s.id}: wrap ${Math.round(w.top - r.top)}-${Math.round(w.bottom - r.top)}  foot ${Math.round(f.top - r.top)}-${Math.round(f.bottom - r.top)}  h ${Math.round(r.height)}`;
  }));
  console.log(info.join('\n'));
  for (const id of ['feed', 'story']) await (await p.$('#' + id)).screenshot({ path: path.join(outDir, `feriado-20-11-${id}.png`) });
  await b.close();
})();
