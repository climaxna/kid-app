/**
 * TAGO + KOMSA API 통합 테스트
 * 실행: node --env-file=.env.local scripts/test-datagokr.mjs
 */

const KEY = process.env.DATAGOKR_API_KEY
if (!KEY) {
  console.error("❌ DATAGOKR_API_KEY 없음 — .env.local 확인")
  process.exit(1)
}

console.log("🔑 키 앞 8자리:", KEY.slice(0, 8) + "...")

async function call(label, url) {
  console.log(`\n📡 [${label}]`)
  console.log("URL:", url.replace(KEY, KEY.slice(0, 8) + "..."))
  try {
    const res = await fetch(url)
    const text = await res.text()
    console.log("HTTP:", res.status)
    try {
      const json = JSON.parse(text)
      const header = json?.response?.header
      if (header) console.log("resultCode:", header.resultCode, "/", header.resultMsg)
      const body = json?.response?.body
      if (body?.totalCount !== undefined) console.log("totalCount:", body.totalCount)
      const item = body?.items?.item
      const first = Array.isArray(item) ? item[0] : item
      if (first) console.log("첫 번째 item:", JSON.stringify(first, null, 2).slice(0, 500))
      else if (!header) console.log("Raw:", text.slice(0, 400))
    } catch {
      console.log("Raw:", text.slice(0, 400))
    }
  } catch (e) {
    console.log("오류:", e.message)
  }
}

// ── 1. TAGO 국내선박운항정보 (1613000/DmstcSvExaminSevice)
console.log("\n\n══════════════════════════════")
console.log("1. TAGO 국내선박운항정보")
console.log("══════════════════════════════")

const tagoBase = "https://apis.data.go.kr/1613000/DmstcSvExaminSevice"

// URLSearchParams로 한국어 자동 인코딩
const tagoCommon = new URLSearchParams({ serviceKey: KEY, _type: "json", numOfRows: "5", pageNo: "1" })
const tagoWando = new URLSearchParams({ serviceKey: KEY, _type: "json", numOfRows: "10", pageNo: "1", depPlaceNm: "완도" })

await call("터미널 목록 (필터 없음)", `${tagoBase}/getTerminalList?${tagoCommon}`)
await call("항로 목록 — 완도 출발 (인코딩)", `${tagoBase}/getRouteList?${tagoWando}`)
await call("항로 목록 — 전체", `${tagoBase}/getRouteList?${tagoCommon}`)

// ── 2. KOMSA 여객선 운항상태 정보
console.log("\n\n══════════════════════════════")
console.log("2. KOMSA 여객선 운항상태")
console.log("══════════════════════════════")

const komsaCommon = new URLSearchParams({ serviceKey: KEY, _type: "json", numOfRows: "5", pageNo: "1" })

// 알려진 KOMSA 엔드포인트 후보들
const komsaCandidates = [
  ["1412000/NngsVslOprInfoService/getList",          "후보1 NngsVslOprInfoService"],
  ["1412000/VslPsageInfoService/getVslPsageInfoList", "후보2 VslPsageInfoService"],
  ["1412000/KomsaVslOprtInfoService/getList",         "후보3 KomsaVslOprtInfoService"],
  ["1412000/VslOprtInfoService/getVslOprtInfoList",   "후보4 VslOprtInfoService"],
  ["B553359/VslOpertInfoService/getVslOpertInfoList", "후보5 B553359"],
]

for (const [path, label] of komsaCandidates) {
  await call(label, `https://apis.data.go.kr/${path}?${komsaCommon}`)
}
