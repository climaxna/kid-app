import { chromium } from 'playwright';
import fs from 'fs';
const outDir = process.argv[2];
const urls = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const b = await chromium.launch();
const pg = await b.newPage({ locale: 'ko-KR' });
for (const [k, u] of Object.entries(urls)) {
  try {
    await pg.goto(u, { timeout: 60000, waitUntil: 'domcontentloaded' });
    await pg.waitForTimeout(6000);
    for (let i = 0; i < 8; i++) { await pg.mouse.wheel(0, 3000); await pg.waitForTimeout(700); }
    for (const sel of ['text=스펙 더보기', 'text=전체 스펙', 'text=상세 스펙', 'text=스펙 전체보기', 'text=상세 사양']) {
      try { await pg.click(sel, { timeout: 2000 }); await pg.waitForTimeout(2000); } catch {}
    }
    const t = await pg.innerText('body');
    fs.writeFileSync(`${outDir}/r_${k}.txt`, t, 'utf8');
    console.log(k, t.length);
  } catch (e) { console.log(k, 'ERR', String(e).slice(0, 200)); }
}
await b.close();
