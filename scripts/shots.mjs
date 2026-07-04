import { chromium } from "playwright-core"
import { fileURLToPath } from "url"
import path from "path"

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.join(__dirname, "..", "docs", "screenshots")
const BASE = "https://ferrycast.kr"
const VIEW = { width: 390, height: 844 }

// 홈화면(PWA) 실행으로 인식시키는 init 스크립트 — 알림 UI 노출용
const standaloneInit = `
  const _mm = window.matchMedia.bind(window);
  window.matchMedia = (q) => q && q.includes('display-mode: standalone')
    ? { matches: true, media: q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false} }
    : _mm(q);
`

async function shot(page, name) {
  await page.waitForTimeout(900)
  await page.screenshot({ path: path.join(OUT, name), fullPage: false })
  console.log("saved", name)
}

const browser = await chromium.launch({ headless: true })

// ── 일반 컨텍스트 ──
const ctx = await browser.newContext({
  viewport: VIEW, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  locale: "ko-KR",
})
const page = await ctx.newPage()

// ① 메인
await page.goto(BASE, { waitUntil: "networkidle" })
await page.getByText("완도 → 제주").first().waitFor({ timeout: 15000 })
await page.waitForTimeout(1200)
await shot(page, "01_main.png")

// ② 항로 상세 (제주 — 직항/경유)
await page.locator("button", { hasText: "완도 → 제주" }).first().click()
await page.getByText("추자도 경유").first().waitFor({ timeout: 8000 }).catch(() => {})
await shot(page, "02_route_jeju.png")

// ③ 완도 도착 탭
await page.goto(BASE, { waitUntil: "networkidle" })
await page.getByRole("button", { name: /완도 도착/ }).first().click()
await page.waitForTimeout(1200)
await shot(page, "03_arrival.png")

// ④ 단기 날씨 예보
await page.goto(BASE, { waitUntil: "networkidle" })
await page.getByText("완도 → 제주").first().waitFor({ timeout: 15000 })
await page.getByText("단기 날씨 예보").first().click()
await page.waitForTimeout(1200)
await shot(page, "04_weather.png")

// ⑤ 5일 조석 예보 (곡선 그래프)
await page.goto(BASE, { waitUntil: "networkidle" })
await page.getByText("완도 → 제주").first().waitFor({ timeout: 15000 })
await page.getByText("5일 조석 예보").first().click()
await page.getByText("완도 5일 조석 예보").first().waitFor({ timeout: 8000 }).catch(() => {})
await shot(page, "05_tide.png")

// ⑦ QR 안내물
await page.goto(`${BASE}/qr`, { waitUntil: "networkidle" })
await page.waitForTimeout(1500)
await shot(page, "07_qr.png")

await ctx.close()

// ── 알림용 (standalone 에뮬레이션) ──
const ctx2 = await browser.newContext({
  viewport: VIEW, deviceScaleFactor: 2, isMobile: true, hasTouch: true,
  locale: "ko-KR", permissions: ["notifications"],
})
await ctx2.addInitScript(standaloneInit)
const page2 = await ctx2.newPage()

// ⑥ 출항 알림 — 미래 시각이 있는 항로를 찾아 열고 시각 탭
const routes = ["완도 → 청산도", "완도 → 제주", "완도 → 소안도·보길도·노화"]
let alarmDone = false
for (const r of routes) {
  await page2.goto(BASE, { waitUntil: "networkidle" })
  await page2.getByText("완도 → 제주").first().waitFor({ timeout: 15000 }).catch(() => {})
  const btn = page2.locator("button", { hasText: r }).first()
  if (await btn.count() === 0) continue
  await btn.click()
  await page2.waitForTimeout(800)
  const timeBtn = page2.locator(".grid-cols-4 button").first()
  if (await timeBtn.count() === 0) { continue }
  await timeBtn.click()
  await page2.waitForTimeout(700)
  // AlarmSheet 노출 확인 (분 전 알림)
  if (await page2.getByText(/분 전 알림|알림 설정/).first().count() > 0) {
    await shot(page2, "06_alarm.png")
    alarmDone = true
    break
  }
}
if (!alarmDone) console.log("WARN: 알림 화면 캡처 실패 — 미래 출항 시각 없음(시간대 영향)")

await ctx2.close()
await browser.close()
console.log("DONE")
