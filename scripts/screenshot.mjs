import { chromium } from "playwright"

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  userAgent:
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
})
const page = await context.newPage()

console.log("🌐 접속 중: https://ferrycast.vercel.app")
await page.goto("https://ferrycast.vercel.app", { waitUntil: "networkidle", timeout: 30000 })

// 날씨·항로 데이터 로딩 대기 (Suspense 해소)
await page.waitForTimeout(3000)

await page.screenshot({ path: "screenshot-main.png", fullPage: true })
console.log("✅ 저장 완료: screenshot-main.png")

await browser.close()
