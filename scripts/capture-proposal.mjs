import { chromium } from "playwright"
import fs from "node:fs"

const BASE = process.env.CAP_BASE || "http://localhost:3100"
const OUT = "proposal-shots"
fs.mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  userAgent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
})
const page = await context.newPage()

async function go(path = "/") {
  await page.goto(BASE + path, { waitUntil: "networkidle", timeout: 30000 })
  await page.waitForTimeout(2500)
}
async function shot(name, opts = {}) {
  const p = `${OUT}/${name}.png`
  await page.screenshot({ path: p, ...opts })
  console.log("✅", p)
}
async function dismissBanner() {
  try {
    const btn = page.getByRole("button", { name: "닫기" })
    if (await btn.count()) await btn.first().click({ timeout: 1500 })
  } catch {}
  await page.waitForTimeout(400)
}

// 1) 메인 화면 (출발 탭) — 전체
await go("/")
await dismissBanner()
await shot("01-main", { fullPage: true })

// 2) 단기 날씨 예보
try {
  await page.getByText("단기 날씨 예보").click({ timeout: 4000 })
  await page.waitForTimeout(1200)
  await shot("02-forecast")
  await page.keyboard.press("Escape")
  await page.waitForTimeout(600)
} catch (e) { console.log("⚠ forecast:", e.message) }

// 3) 5일 조석 예보
try {
  await page.getByText("5일 조석 예보").click({ timeout: 4000 })
  await page.waitForTimeout(1200)
  await shot("03-tidal")
  await page.keyboard.press("Escape")
  await page.waitForTimeout(600)
} catch (e) { console.log("⚠ tidal:", e.message) }

// 4) 항로 상세 (청산도) — viewport
try {
  await page.getByText("완도 → 청산도").first().click({ timeout: 4000 })
  await page.waitForTimeout(1200)
  await shot("04-route-detail")

  // 5) 출항 알림 시트 — 미래 출발시각 칩 클릭
  try {
    const futureChip = page.locator("button.bg-blue-50").filter({ hasText: ":" }).first()
    if (await futureChip.count()) {
      await futureChip.click({ timeout: 2500 })
      await page.waitForTimeout(900)
      await shot("05-alarm")
      await page.keyboard.press("Escape")
      await page.waitForTimeout(400)
    } else {
      console.log("⚠ alarm: 미래 시각 칩 없음 (오늘 운항 종료)")
    }
  } catch (e) { console.log("⚠ alarm:", e.message) }

  await page.keyboard.press("Escape")
  await page.waitForTimeout(600)
} catch (e) { console.log("⚠ route-detail:", e.message) }

// 6) 완도 도착 탭
try {
  await page.getByRole("button", { name: "완도 도착" }).click({ timeout: 4000 })
  await page.waitForTimeout(1000)
  await shot("06-arrivals", { fullPage: true })
} catch (e) { console.log("⚠ arrivals:", e.message) }

// 7) QR 페이지 (인쇄용 안내물)
await go("/qr")
await dismissBanner()
await shot("07-qr", { fullPage: true })

await browser.close()
console.log("🎉 캡처 완료")
