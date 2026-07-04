// FerryCast 완도군청 제안서 생성 — PDF(Playwright) + DOCX(docx) 동시 생성
// 실행: node scripts/make-proposal.mjs
import fs from "node:fs"
import { chromium } from "playwright"
import {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  Table, TableRow, TableCell, WidthType, ImageRun, BorderStyle, ShadingType,
} from "docx"

const SHOTS = "proposal-shots"
const b64 = (f) => fs.readFileSync(`${SHOTS}/${f}`).toString("base64")
const buf = (f) => fs.readFileSync(`${SHOTS}/${f}`)

// ── 공통 콘텐츠 ────────────────────────────────
const CONTACT = { name: "김신진", phone: "010-8478-7552", email: "climaxna@naver.com", web: "https://ferrycast.kr" }

const FEATURE_ROWS = [
  ["실시간 운항 시간표", "완도 출발·도착 전 항로의 배 시각을 실시간으로 제공 (완도–제주·청산도·소안도·보길도·노화)"],
  ["운항 / 결항 표시", "운항(파랑)·결항(빨강)을 색으로 직관 표시. 일부 편만 결항돼도 운항하는 배는 그대로 안내"],
  ["날씨 · 파고", "완도 현재 날씨·바람·습도·파고 + 3일 단기예보를 함께 제공해 뱃길 가늠 지원"],
  ["조석(물때) 예보", "국립해양조사원 만조·간조 시각과 물높이를 5일치 제공"],
  ["출항 알림", "원하는 출발 시각 30·10·5분 전 알림 (홈화면 추가 시) — 배를 놓치지 않도록"],
  ["앱 설치 없이 즉시", "QR 스캔 또는 검색으로 접속 즉시 모든 정보 표시. 홈화면 추가 시 앱처럼 사용"],
]

const PRINCIPLES = [
  ["클릭 없이 한 화면", "앱을 열면 메뉴를 찾아 들어갈 필요 없이 날씨·물때·배 시각·운항상태가 곧바로 보입니다. 디지털이 익숙하지 않은 어르신도 헤매지 않습니다."],
  ["큰 글씨 · 색으로 구분", "다음 배 시각은 큰 숫자로, 운항은 파란색·결항은 빨간색으로 표시합니다. 글을 자세히 읽지 않아도, 외국인 관광객도 색만으로 상황을 알 수 있습니다."],
  ["설치 과정 없음", "복잡한 앱 설치 없이 QR을 카메라로 비추거나 주소만 입력하면 바로 열립니다. 안내물에 '휴대폰 카메라로 비추면 열려요'라고 크게 적었습니다."],
  ["빈 화면이 없는 설계", "일시적으로 데이터가 지연돼도 흰 화면 대신 참고 시간표를 보여줍니다. 언제 열어도 무언가는 반드시 보입니다."],
]

const GALLERY = [
  ["01-main.png", 780, 2600, "메인 화면 — 한 화면에 모든 정보",
    "앱을 열면 클릭 한 번 없이 곧바로 ① 완도 현재 날씨·파고, ② 다음 만조·간조, ③ 완도 출발 모든 항로의 다음 배 시각과 운항·결항 상태가 한 화면에 나옵니다. 메뉴를 찾아 들어갈 필요가 없습니다."],
  ["04-route-detail.png", 780, 1688, "항로 상세 — 시간표·운임·터미널·알림",
    "항로를 누르면 오늘 출발 시간표(지난 편은 흐리게, 다음 편은 큰 파란 버튼으로 강조), 공식 운임표, 출발 터미널 지도, 내일 운항 편수, 승선 예약까지 한 화면에 모읍니다."],
  ["06-arrivals.png", 780, 2600, "완도 도착 — 섬에서 돌아오는 배편",
    "'완도 도착' 탭에서 섬에서 완도로 돌아오는 배편 시각과 운항 상태, 섬에서 타는 터미널 위치를 확인합니다. 돌아오는 일정도 미리 계획할 수 있습니다."],
  ["02-forecast.png", 780, 1688, "단기 날씨 예보",
    "날씨를 누르면 기상청 단기예보 기반으로 오늘부터 3일간 날씨·최저/최고 기온·강수확률을 큰 글씨와 아이콘으로 보여줍니다."],
  ["03-tidal.png", 780, 1688, "5일 조석(물때) 예보",
    "국립해양조사원(KHOA) 완도 관측소 기준 만조·간조 시각과 물높이를 5일치 제공합니다. 물때에 민감한 완도 뱃길 판단에 도움이 됩니다."],
  ["05-alarm.png", 780, 1688, "출항 알림",
    "원하는 출발 시각을 누르면 30·10·5분 전에 알림을 받을 수 있습니다(홈화면 추가 시). 깜빡 잊고 배를 놓치는 일을 줄여 줍니다."],
  ["07-qr.png", 780, 1688, "QR 안내물 (인쇄·부착용)",
    "터미널·정류장에 붙일 수 있는 인쇄용 QR입니다. '완도 배 시간표 / 결항·날씨 한눈에' 큰 글씨와 '휴대폰 카메라로 비추면 열려요' 안내로, 누구나 앱 설치 없이 즉시 접속합니다."],
]

const REQUESTS = [
  ["1", "QR코드 부착 허가", "여객선터미널·버스터미널 등 공공장소에 접속 QR 안내물 부착 허가"],
  ["2", "공식 홍보 협조", "완도군 누리집·SNS 등 공식 채널을 통한 서비스 소개 게시"],
  ["3", "정보 정확성 협의", "정확한 정보 제공을 위한 데이터·운영 관련 의견 교류 (선택)"],
]

const REVENUE = [
  ["온라인 광고", "화면 하단에 비침해적 배너 광고를 게재 (정보 확인을 방해하지 않는 위치)"],
  ["지역 상생", "완도 지역 업체(펜션·식당·특산물 등) 홍보를 우선 게재하여 지역 경제에 기여"],
  ["정보 무료", "배편·날씨 등 핵심 정보는 영구 무료. 이용자에게 요금을 부과하지 않음"],
]

// ════════════════════════════════════════════════
// 1) HTML → PDF
// ════════════════════════════════════════════════
function buildHtml() {
  const featureTable = FEATURE_ROWS.map(([a, b]) => `<tr><td class="k">${a}</td><td>${b}</td></tr>`).join("")
  const revenueTable = REVENUE.map(([a, b]) => `<tr><td class="k">${a}</td><td>${b}</td></tr>`).join("")
  const requestTable = REQUESTS.map(([n, a, b]) => `<tr><td class="num">${n}</td><td class="k">${a}</td><td>${b}</td></tr>`).join("")
  const principles = PRINCIPLES.map(([t, d]) => `<div class="card"><p class="ct">${t}</p><p class="cd">${d}</p></div>`).join("")
  const gallery = GALLERY.map(([f, , , t, d], i) =>
    `<div class="shot"><img src="data:image/png;base64,${b64(f)}"/><div class="shotbody"><p class="st">${["①","②","③","④","⑤","⑥","⑦"][i]} ${t}</p><p class="sd">${d}</p></div></div>`
  ).join("")

  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>
  @page { size: A4; margin: 16mm 15mm; }
  * { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { font-family: "Malgun Gothic","맑은 고딕",sans-serif; color: #1e293b; font-size: 11pt; line-height: 1.65; margin: 0; }
  h1,h2 { margin: 0; }
  .cover { text-align: center; padding: 40px 0 28px; }
  .cover .sub { color: #64748b; font-size: 13pt; font-weight: 700; }
  .cover .title { color: #1d4ed8; font-size: 30pt; font-weight: 800; margin: 8px 0; }
  .cover .tag { font-size: 12pt; margin-top: 6px; }
  .cover .quote { margin-top: 22px; font-size: 13pt; }
  .cover .quote b { color: #1d4ed8; }
  .cover .meta { margin-top: 22px; color: #334155; font-size: 11pt; line-height: 1.9; }
  .cover .meta .web { color: #1d4ed8; font-weight: 700; }
  h2.sec { color: #1d4ed8; font-size: 16pt; font-weight: 800; border-bottom: 2px solid #1d4ed8; padding-bottom: 5px; margin: 26px 0 12px; break-after: avoid; }
  h3 { font-size: 12.5pt; color: #1e293b; margin: 14px 0 6px; }
  p { margin: 0 0 9px; }
  ul { margin: 0 0 9px; padding-left: 20px; }
  li { margin-bottom: 4px; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0 10px; }
  th { background: #1d4ed8; color: #fff; font-weight: 700; padding: 8px 10px; text-align: left; font-size: 10.5pt; }
  td { border: 1px solid #e2e8f0; padding: 8px 10px; font-size: 10.5pt; vertical-align: top; }
  td.k { font-weight: 700; color: #0f172a; width: 26%; background: #f8fafc; }
  td.num { width: 8%; text-align: center; font-weight: 700; color: #1d4ed8; background: #f8fafc; }
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 8px 0; }
  .card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; background: #f8fafc; break-inside: avoid; }
  .card .ct { font-weight: 800; color: #1d4ed8; font-size: 11.5pt; margin: 0 0 4px; }
  .card .cd { margin: 0; font-size: 10pt; color: #334155; line-height: 1.55; }
  .shot { display: flex; gap: 16px; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; break-inside: avoid; }
  .shot img { width: 150px; height: auto; border: 1px solid #e2e8f0; border-radius: 10px; flex-shrink: 0; }
  .shot .st { font-weight: 800; color: #1d4ed8; font-size: 12pt; margin: 0 0 6px; }
  .shot .sd { margin: 0; font-size: 10.5pt; color: #334155; }
  .note { color: #64748b; font-size: 9.5pt; margin-top: 4px; }
  .pagebreak { page-break-before: always; }
  .contact { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px; margin-top: 10px; }
  </style></head><body>

  <div class="cover">
    <div class="sub">완도 배편 · 날씨 통합 정보 서비스</div>
    <div class="title">FerryCast 협력 제안서</div>
    <div class="tag">QR코드 부착 허가 및 공식 홍보 협조 요청</div>
    <div class="quote"><b>“오늘 배 뜨나요?”</b><br/>완도 군민과 관광객이 한 화면에서 즉시 확인하는 공익 정보 서비스</div>
    <div class="meta">
      제출일 : 2026년 6월<br/>
      제안자 : FerryCast 운영자 (${CONTACT.name})<br/>
      웹주소 : <span class="web">${CONTACT.web}</span>
    </div>
  </div>

  <h2 class="sec">1. 제안 개요</h2>
  <p>FerryCast는 완도를 오가는 군민과 관광객이 <b>여객선 운항 시간표, 실시간 운항·결항 여부, 날씨·파고·물때</b>를 별도 앱 설치 없이 <b>한 화면에서 즉시</b> 확인할 수 있는 모바일 웹 서비스입니다.</p>
  <p>본 제안서는 완도군청에 다음 두 가지를 정중히 요청드립니다.</p>
  <ul>
    <li>완도 여객선터미널·버스터미널 등 공공장소에 FerryCast 접속 <b>QR코드 부착 허가</b></li>
    <li>완도군 공식 채널(누리집·SNS 등)을 통한 <b>서비스 홍보 협조</b></li>
  </ul>
  <p>FerryCast는 군민 편의와 관광객 만족도 향상을 목표로 하는 공익적 정보 서비스이며, <b>군의 예산 지원 없이 민간이 자체 개발·운영</b>합니다.</p>

  <h2 class="sec">2. 추진 배경 — 군민·관광객의 불편</h2>
  <p>완도는 기상 변화에 따라 여객선 결항이 잦은 지역입니다. 그러나 현재 배편 정보는 여러 기관에 흩어져 있어 이용자가 다음과 같은 불편을 겪습니다.</p>
  <ul>
    <li>운항 시간표, 결항 여부, 날씨 정보를 <b>각각 다른 사이트</b>에서 따로 확인해야 함</li>
    <li>관광객은 어디서 정보를 찾아야 할지 몰라, <b>터미널에 도착해서야 결항을 알게 되는</b> 경우 발생</li>
    <li>고령 군민은 여러 사이트를 오가며 정보를 찾기 어려움</li>
  </ul>
  <p>FerryCast는 이 문제를 <b>‘한 화면, 클릭 없는 즉시 확인’</b>으로 해결합니다.</p>

  <h2 class="sec">3. 누구나 쉽게 — 디자인 원칙</h2>
  <p>FerryCast는 <b>디지털이 익숙하지 않은 어르신과 처음 온 관광객</b>도 헤매지 않도록, 화면을 최대한 단순하고 직관적으로 설계했습니다.</p>
  <div class="cards">${principles}</div>

  <h2 class="sec">4. 서비스 주요 기능</h2>
  <table><tr><th style="width:26%">기능</th><th>내용</th></tr>${featureTable}</table>
  <p class="note">※ 데이터 출처 : 한국해양교통안전공단(MTIS 운항 스케줄), 기상청, 국립해양조사원(KHOA) 등 공공 API 활용</p>

  <h2 class="sec pagebreak">5. 실제 앱 화면</h2>
  <p>아래는 실제 서비스 화면입니다. 모든 정보는 스마트폰에서 손가락 한 번으로 확인할 수 있도록 설계했습니다.</p>
  ${gallery}

  <h2 class="sec pagebreak">6. 안정적인 운영 — 많은 사람이 써도 끊기지 않게</h2>
  <ul>
    <li><b>믿을 수 있는 공공 데이터</b> : 국토교통부 계열 해양교통안전공단·기상청·국립해양조사원의 공식 API를 사용합니다.</li>
    <li><b>실시간 + 결항 통합</b> : 운항 시간표와 결항 정보를 하나의 공식 데이터로 동시에 받아, 정보가 어긋나지 않습니다. 청산농협 차도선 등 지역 운항 배편까지 실시간으로 표시됩니다.</li>
    <li><b>사용자가 늘어도 안정</b> : 데이터 호출을 최소화하는 캐시 구조로 설계해, 이용자가 많아져도 서버·외부 데이터 한도에 무리가 가지 않습니다.</li>
    <li><b>빈 화면 없는 안전망</b> : 일시적 장애 시에도 참고 시간표를 표시하여 정보 공백을 만들지 않습니다.</li>
  </ul>

  <h2 class="sec">7. 향후 추가 예정</h2>
  <ul>
    <li><b>출항 알림 확대</b> : 관심 항로의 출발 시각 알림을 더 많은 환경에서 안정적으로 제공</li>
    <li><b>제공 항로 확대</b> : 현재 제주·청산도·소안도·보길도·노화 → 그 외 항로도 데이터 확보에 따라 순차 추가</li>
  </ul>

  <h2 class="sec">8. 완도군의 기대 효과</h2>
  <h3>8-1. 군민 편의 증진</h3>
  <ul><li>배편·날씨·물때를 한 번에 확인하여 불필요한 헛걸음 방지</li><li>고령층도 쉽게 쓰는 단순한 화면으로 정보 접근성 향상</li></ul>
  <h3>8-2. 관광객 만족도 향상</h3>
  <ul><li>결항 정보를 미리 확인하여 일정 차질 최소화</li><li>‘정보를 쉽게 찾을 수 있는 완도’라는 긍정적 방문 경험 제공</li></ul>
  <h3>8-3. 군의 부담 없는 협력</h3>
  <ul><li>군의 예산·인력 투입 없이 민간이 자체 개발·운영</li><li>군은 부착 허가와 홍보 협조만으로 군민 편의 서비스 제공 효과</li></ul>

  <h2 class="sec">9. 운영 방식 및 지속가능성</h2>
  <p>FerryCast는 무료 공익 서비스로 운영되며, 서버 유지를 위해 다음과 같은 최소한의 수익 모델을 투명하게 운영합니다.</p>
  <table><tr><th style="width:26%">구분</th><th>내용</th></tr>${revenueTable}</table>
  <p>운영 수익은 서버 유지와 서비스 개선에 사용되며, 군의 예산 부담 없이 서비스를 안정적으로 지속하기 위한 수단입니다.</p>

  <h2 class="sec">10. 완도군청에 드리는 요청 사항</h2>
  <table><tr><th style="width:8%">No</th><th style="width:26%">요청 항목</th><th>세부 내용</th></tr>${requestTable}</table>

  <h2 class="sec">11. 맺음말</h2>
  <p>FerryCast는 완도를 찾는 모든 사람이 <b>‘오늘 배가 뜨는지’</b>를 쉽고 빠르게 확인하도록 돕는 작은 서비스입니다. 군의 예산이나 인력 부담 없이 군민 편의와 관광 활성화에 보탬이 되고자 합니다. 완도군청의 부착 허가와 홍보 협조를 부탁드립니다.</p>

  <h2 class="sec">문의 및 연락처</h2>
  <div class="contact">
    서비스명 : FerryCast (페리캐스트)<br/>
    웹주소 : <b style="color:#1d4ed8">${CONTACT.web}</b><br/>
    담당자 : <b>${CONTACT.name}</b> &nbsp;·&nbsp; 연락처 : ${CONTACT.phone} &nbsp;·&nbsp; 이메일 : ${CONTACT.email}
  </div>

  </body></html>`
}

async function makePdf() {
  const html = buildHtml()
  fs.writeFileSync("proposal.html", html)
  const browser = await chromium.launch()
  const page = await browser.newPage()
  await page.setContent(html, { waitUntil: "networkidle" })
  await page.pdf({ path: "FerryCast_완도군청_제안서.pdf", format: "A4", printBackground: true,
    margin: { top: "16mm", bottom: "16mm", left: "15mm", right: "15mm" } })
  await browser.close()
  console.log("✅ PDF 생성 완료: FerryCast_완도군청_제안서.pdf")
}

// ════════════════════════════════════════════════
// 2) DOCX
// ════════════════════════════════════════════════
const FONT = "맑은 고딕", BLUE = "1D4ED8", DARK = "1E293B", GRAY = "64748B"
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: o.size ?? 20, bold: o.bold, color: o.color ?? DARK, break: o.break })
const para = (c, o = {}) => new Paragraph({ alignment: o.align, spacing: { after: o.after ?? 120, before: o.before ?? 0, line: 276 }, pageBreakBefore: o.pageBreakBefore, children: Array.isArray(c) ? c : [c] })
const h1 = (t) => new Paragraph({ spacing: { before: 280, after: 140 }, pageBreakBefore: false, border: { bottom: { color: BLUE, size: 8, style: BorderStyle.SINGLE, space: 4 } }, children: [run(t, { size: 26, bold: true, color: BLUE })] })
const h2 = (t) => para(run(t, { size: 22, bold: true }), { before: 160, after: 80 })
const body = (t, o = {}) => para(run(t, { size: 20, color: o.color ?? "334155" }), { after: o.after ?? 100 })
const bullet = (t) => new Paragraph({ bullet: { level: 0 }, spacing: { after: 60, line: 276 }, children: [run(t, { size: 20, color: "334155" })] })
const cellB = (c = "E2E8F0") => ({ top: { style: BorderStyle.SINGLE, size: 4, color: c }, bottom: { style: BorderStyle.SINGLE, size: 4, color: c }, left: { style: BorderStyle.SINGLE, size: 4, color: c }, right: { style: BorderStyle.SINGLE, size: 4, color: c } })
const noB = { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } }

function dataTable(headers, rows, widths) {
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => new TableCell({
    width: { size: widths[i], type: WidthType.PERCENTAGE }, borders: cellB(), shading: { type: ShadingType.CLEAR, fill: BLUE },
    margins: { top: 60, bottom: 60, left: 100, right: 100 }, children: [para(run(h, { bold: true, color: "FFFFFF", size: 20 }), { after: 0 })] })) })
  const dr = rows.map((r, ri) => new TableRow({ children: r.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.PERCENTAGE }, borders: cellB(), shading: ri % 2 ? { type: ShadingType.CLEAR, fill: "F8FAFC" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 }, children: [para(run(c, { size: 19, color: "334155" }), { after: 0 })] })) }))
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: [head, ...dr] })
}

function shotRow(file, w, h, title, desc, idx) {
  const W = 150, img = new ImageRun({ data: buf(file), type: "png", transformation: { width: W, height: Math.round(W * h / w) } })
  return new TableRow({ children: [
    new TableCell({ width: { size: 32, type: WidthType.PERCENTAGE }, borders: noB, verticalAlign: "center", margins: { top: 80, bottom: 80, left: 40, right: 120 },
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [img] })] }),
    new TableCell({ width: { size: 68, type: WidthType.PERCENTAGE }, borders: noB, verticalAlign: "center", margins: { top: 80, bottom: 80, left: 80, right: 40 },
      children: [para(run(`${["①","②","③","④","⑤","⑥","⑦"][idx]} ${title}`, { bold: true, size: 22, color: BLUE }), { after: 80 }), para(run(desc, { size: 19, color: "334155" }), { after: 0 })] }),
  ] })
}

async function makeDocx() {
  const children = [
    para(run("완도 배편 · 날씨 통합 정보 서비스", { size: 24, bold: true, color: GRAY }), { align: AlignmentType.CENTER, before: 200, after: 60 }),
    para(run("FerryCast 협력 제안서", { size: 44, bold: true, color: BLUE }), { align: AlignmentType.CENTER, after: 80 }),
    para(run("QR코드 부착 허가 및 공식 홍보 협조 요청", { size: 22 }), { align: AlignmentType.CENTER, after: 200 }),
    para([run("“오늘 배 뜨나요?”", { size: 22, bold: true, color: BLUE })], { align: AlignmentType.CENTER, after: 20 }),
    para(run("완도 군민과 관광객이 한 화면에서 즉시 확인하는 공익 정보 서비스", { size: 20, color: GRAY }), { align: AlignmentType.CENTER, after: 220 }),
    para(run("제출일 : 2026년 6월", { size: 20 }), { align: AlignmentType.CENTER, after: 20 }),
    para(run(`제안자 : FerryCast 운영자 (${CONTACT.name})`, { size: 20 }), { align: AlignmentType.CENTER, after: 20 }),
    para(run(`웹주소 : ${CONTACT.web}`, { size: 20, bold: true, color: BLUE }), { align: AlignmentType.CENTER, after: 200 }),

    h1("1. 제안 개요"),
    body("FerryCast는 완도를 오가는 군민과 관광객이 여객선 운항 시간표, 실시간 운항·결항 여부, 날씨·파고·물때를 별도 앱 설치 없이 한 화면에서 즉시 확인할 수 있는 모바일 웹 서비스입니다."),
    body("본 제안서는 완도군청에 다음 두 가지를 정중히 요청드립니다."),
    bullet("완도 여객선터미널·버스터미널 등 공공장소에 FerryCast 접속 QR코드 부착 허가"),
    bullet("완도군 공식 채널(누리집·SNS 등)을 통한 서비스 홍보 협조"),
    body("FerryCast는 군민 편의와 관광객 만족도 향상을 목표로 하는 공익적 정보 서비스이며, 군의 예산 지원 없이 민간이 자체 개발·운영합니다."),

    h1("2. 추진 배경 — 군민·관광객의 불편"),
    body("완도는 기상 변화에 따라 여객선 결항이 잦은 지역입니다. 그러나 현재 배편 정보는 여러 기관에 흩어져 있어 이용자가 다음과 같은 불편을 겪습니다."),
    bullet("운항 시간표, 결항 여부, 날씨 정보를 각각 다른 사이트에서 따로 확인해야 함"),
    bullet("관광객은 어디서 정보를 찾아야 할지 몰라, 터미널에 도착해서야 결항을 알게 되는 경우 발생"),
    bullet("고령 군민은 여러 사이트를 오가며 정보를 찾기 어려움"),
    body("FerryCast는 이 문제를 ‘한 화면, 클릭 없는 즉시 확인’으로 해결합니다."),

    h1("3. 누구나 쉽게 — 디자인 원칙"),
    body("FerryCast는 디지털이 익숙하지 않은 어르신과 처음 온 관광객도 헤매지 않도록, 화면을 최대한 단순하고 직관적으로 설계했습니다."),
    ...PRINCIPLES.flatMap(([t, d]) => [h2(t), body(d)]),

    h1("4. 서비스 주요 기능"),
    dataTable(["기능", "내용"], FEATURE_ROWS, [26, 74]),
    body("※ 데이터 출처 : 한국해양교통안전공단(MTIS 운항 스케줄), 기상청, 국립해양조사원(KHOA) 등 공공 API 활용", { color: GRAY, after: 40 }),

    h1("5. 실제 앱 화면"),
    body("아래는 실제 서비스 화면입니다. 모든 정보는 스마트폰에서 손가락 한 번으로 확인할 수 있도록 설계했습니다.", { after: 140 }),
    new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: GALLERY.map(([f, w, h, t, d], i) => shotRow(f, w, h, t, d, i)) }),

    h1("6. 안정적인 운영 — 많은 사람이 써도 끊기지 않게"),
    bullet("믿을 수 있는 공공 데이터 : 해양교통안전공단·기상청·국립해양조사원의 공식 API를 사용합니다."),
    bullet("실시간 + 결항 통합 : 운항 시간표와 결항 정보를 하나의 공식 데이터로 동시에 받아 정보가 어긋나지 않습니다. 청산농협 차도선 등 지역 운항 배편까지 실시간 표시됩니다."),
    bullet("사용자가 늘어도 안정 : 데이터 호출을 최소화하는 캐시 구조로 설계해, 이용자가 많아져도 무리가 가지 않습니다."),
    bullet("빈 화면 없는 안전망 : 일시적 장애 시에도 참고 시간표를 표시하여 정보 공백을 만들지 않습니다."),

    h1("7. 향후 추가 예정"),
    bullet("출항 알림 확대 : 관심 항로의 출발 시각 알림을 더 많은 환경에서 안정적으로 제공"),
    bullet("제공 항로 확대 : 현재 제주·청산도·소안도·보길도·노화 → 그 외 항로도 데이터 확보에 따라 순차 추가"),

    h1("8. 완도군의 기대 효과"),
    h2("8-1. 군민 편의 증진"),
    bullet("배편·날씨·물때를 한 번에 확인하여 불필요한 헛걸음 방지"),
    bullet("고령층도 쉽게 쓰는 단순한 화면으로 정보 접근성 향상"),
    h2("8-2. 관광객 만족도 향상"),
    bullet("결항 정보를 미리 확인하여 일정 차질 최소화"),
    bullet("‘정보를 쉽게 찾을 수 있는 완도’라는 긍정적 방문 경험 제공"),
    h2("8-3. 군의 부담 없는 협력"),
    bullet("군의 예산·인력 투입 없이 민간이 자체 개발·운영"),
    bullet("군은 부착 허가와 홍보 협조만으로 군민 편의 서비스 제공 효과"),

    h1("9. 운영 방식 및 지속가능성"),
    body("FerryCast는 무료 공익 서비스로 운영되며, 서버 유지를 위해 다음과 같은 최소한의 수익 모델을 투명하게 운영합니다."),
    dataTable(["구분", "내용"], REVENUE, [26, 74]),
    body("운영 수익은 서버 유지와 서비스 개선에 사용되며, 군의 예산 부담 없이 서비스를 안정적으로 지속하기 위한 수단입니다."),

    h1("10. 완도군청에 드리는 요청 사항"),
    dataTable(["No", "요청 항목", "세부 내용"], REQUESTS, [10, 28, 62]),

    h1("11. 맺음말"),
    body("FerryCast는 완도를 찾는 모든 사람이 ‘오늘 배가 뜨는지’를 쉽고 빠르게 확인하도록 돕는 작은 서비스입니다. 군의 예산이나 인력 부담 없이 군민 편의와 관광 활성화에 보탬이 되고자 합니다. 완도군청의 부착 허가와 홍보 협조를 부탁드립니다."),

    h1("문의 및 연락처"),
    body("서비스명 : FerryCast (페리캐스트)"),
    body(`웹주소 : ${CONTACT.web}`),
    para([run(`담당자 : ${CONTACT.name}`, { size: 20, bold: true }), run(`     연락처 : ${CONTACT.phone}     이메일 : ${CONTACT.email}`, { size: 20 })], { after: 60 }),
  ]
  const doc = new Document({ styles: { default: { document: { run: { font: FONT, size: 20 } } } },
    sections: [{ properties: { page: { margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } } }, children }] })
  const out = await Packer.toBuffer(doc)
  fs.writeFileSync(process.argv[2] || "FerryCast_완도군청_제안서.docx", out)
  console.log("✅ DOCX 생성 완료:", process.argv[2] || "FerryCast_완도군청_제안서.docx", `(${(out.length / 1024).toFixed(0)} KB)`)
}

await makePdf()
await makeDocx()
console.log("🎉 제안서 생성 완료")
