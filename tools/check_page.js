#!/usr/bin/env node
// Development check for index.html with a headless browser (Playwright).
// The shipped page does not use this tool. It needs a running tools/serve.py.
//
//   node tools/check_page.js [base URL] [out dir]
//
// Checks: no console errors, first load size (raw and gzip), and the CSP blocks
// an external request. It writes screenshots at 360, 1280, and 1920 px width.
const zlib = require('zlib');
const path = require('path');
const fs = require('fs');
let pw;
try { pw = require('playwright'); } catch (e) {
  console.log('Playwright is not installed. Skip the page check.');
  process.exit(0);
}
const base = process.argv[2] || 'http://localhost:8000/';
const out = process.argv[3] || 'page-check';
const NOW = '2026-10-20T18:00:00Z';

(async () => {
  fs.mkdirSync(out, {recursive: true});
  const exe = fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
  const browser = await pw.chromium.launch(exe ? {executablePath: exe} : {});
  let failed = false;
  for (const [w, h, theme] of [[1280, 900, 'dark'], [360, 780, 'dark'], [1920, 1080, 'light']]) {
    const ctx = await browser.newContext({viewport: {width: w, height: h}});
    const page = await ctx.newPage();
    const errors = [], sizes = new Map(), external = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', e => errors.push('pageerror: ' + e.message));
    page.on('request', r => { if (!r.url().startsWith(base) && !r.url().startsWith('blob:') && !r.url().startsWith('data:')) external.push(r.url()); });
    page.on('response', async r => { try { const b = await r.body(); sizes.set(r.url(), b); } catch (e) { /* redirect or no body */ } });
    if (theme === 'light') await ctx.addInitScript(() => { try { localStorage.setItem('pdd.theme', '"light"'); } catch (e) {} });
    await page.goto(base + '?now=' + NOW, {waitUntil: 'networkidle'});
    await page.waitForTimeout(800);
    let first = 0;
    for (const b of sizes.values()) first += zlib.gzipSync(b, {level: 6}).length;
    // Scroll down step by step. The page loads a widget when it comes into view.
    for (let y = 0; y < 20000; y += h / 2) { await page.evaluate(v => window.scrollTo(0, v), y); await page.waitForTimeout(120); if (y > await page.evaluate(() => document.body.scrollHeight)) break; }
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(800);
    // The CSP must block a request to another origin.
    const blocked = await page.evaluate(async () => {
      let v = 0; document.addEventListener('securitypolicyviolation', () => { v++; });
      try { await fetch('https://example.com/x.json'); return 'not blocked'; } catch (e) { await new Promise(r => setTimeout(r, 100)); return v ? 'blocked' : 'failed without CSP event'; }
    });
    const cspErrors = errors.filter(e => /Content Security Policy|example\.com|Failed to fetch/.test(e));
    const realErrors = errors.filter(e => !cspErrors.includes(e));
    let raw = 0, gz = 0;
    for (const b of sizes.values()) { raw += b.length; gz += zlib.gzipSync(b, {level: 6}).length; }
    const file = path.join(out, `page-${w}.png`);
    await page.screenshot({path: file, fullPage: true});
    console.log(`${w}px ${theme}: ${sizes.size} requests, raw ${(raw / 1024).toFixed(1)} KB, gzip ${(gz / 1024).toFixed(1)} KB, ` +
      `first view gzip ${(first / 1024).toFixed(1)} KB, CSP ${blocked}, console errors ${realErrors.length}, external requests ${external.filter(u => !u.includes('example.com')).length}, ${file}`);
    for (const e of realErrors) console.log('  ERROR ' + e);
    if (realErrors.length || blocked !== 'blocked' || first > 300 * 1024 || external.some(u => !u.includes('example.com'))) failed = true;
    await ctx.close();
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
