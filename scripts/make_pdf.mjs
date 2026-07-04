import { chromium } from "playwright-core"
import { readFileSync } from "fs"
import path from "path"
import { fileURLToPath, pathToFileURL } from "url"

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DOCS = path.join(__dirname, "..", "docs")
const htmlPath = path.join(DOCS, "_제안서_print.html")
const outPdf = path.join(DOCS, "FerryCast_완도군청_제안서_v2.pdf")

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage()
// docs 폴더 기준으로 로드해야 screenshots/ 상대경로 이미지가 잡힘
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" })
await page.pdf({
  path: outPdf,
  format: "A4",
  printBackground: true,
  margin: { top: "16mm", bottom: "16mm", left: "15mm", right: "15mm" },
})
await browser.close()
console.log("PDF 생성 완료:", outPdf)
