// usage: node render.js <post.html> <outDir>
const { chromium } = require('playwright');
const path = require('path');
const [, , html, outDir] = process.argv;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1400 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(html));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  // overflow check: any element extending past its slide
  const issues = await p.evaluate(() => {
    const out = [];
    document.querySelectorAll('.slide').forEach(s => {
      const r = s.getBoundingClientRect();
      s.querySelectorAll('*').forEach(e => {
        if (e.classList.contains('glow')) return;
        const q = e.getBoundingClientRect();
        if (q.width && (q.right > r.right - 40 || q.left < r.left + 30 || q.bottom > r.bottom - 30)) out.push(`${s.id}: ${e.className || e.tagName} ${Math.round(q.left - r.left)},${Math.round(q.top - r.top)} ${Math.round(q.width)}x${Math.round(q.height)}`);
        if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflow === 'hidden' && !e.classList.contains('slide')) out.push(`${s.id}: clipped ${e.className}`);
      });
    });
    return out;
  });
  const cols = await p.evaluate(() => [...document.querySelectorAll('.q .col')].map(c => `${c.parentElement.id}: content ${c.scrollHeight} / box ${c.clientHeight}`));
  console.log(cols.join('\n'));
  console.log(issues.filter(x => !/(contact|DIV 0,|story: (k|hint|foot))/.test(x)).slice(0, 40).join('\n') || 'no overflow');
  const ids = await p.$$eval('.slide', ss => ss.map(s => s.id));
  for (const id of ids) {
    const name = id === 'story' ? 'story-caixa-de-perguntas.png' : `carrossel-${id.slice(1).padStart(2, '0')}.png`;
    await (await p.$('#' + id)).screenshot({ path: path.join(outDir, name) });
  }
  await b.close();
})();
