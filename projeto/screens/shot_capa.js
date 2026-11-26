const { chromium } = require('playwright');
(async () => {
  const [, , html, out] = process.argv;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + require('path').resolve(html)); await p.evaluate(() => document.fonts.ready);
  await p.evaluate(() => Promise.all([...document.images].map(i => i.decode().catch(() => {}))));
  await p.waitForTimeout(300); await p.screenshot({ path: out }); await b.close();
})();
