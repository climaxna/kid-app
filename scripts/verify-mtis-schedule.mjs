/**
 * 한국해양교통안전공단_운항 스케줄 정보 (data.go.kr ID: 15142302) 검증
 * 목적: 기존 DATAGOKR_API_KEY로 접근 가능한지, 완도·청산도 편 포함 여부 확인
 *
 * 실행 방법 (로컬 PC에서):
 *   node --env-file=.env.local scripts/verify-mtis-schedule.mjs
 *
 * .env.local에 DATAGOKR_API_KEY=... 가 있어야 합니다.
 */

const KEY = process.env.DATAGOKR_API_KEY
if (!KEY) {
  console.error("❌ DATAGOKR_API_KEY 없음 — .env.local 확인")
  process.exit(1)
}

const kst = new Date(Date.now() + 9 * 60 * 60 * 1000)
const TODAY = kst.toISOString().slice(0, 10).replace(/-/g, "")

console.log("🔑 키 앞 8자리:", KEY.slice(0, 8) + "...")
console.log("📅 조회 날짜:", TODAY)

// KOMSA(B554035) data.go.kr URL 후보 — 정확한 URL은 data.go.kr ID:15142302 페이지 참조
const URL_CANDIDATES = [
  "https://apis.data.go.kr/B554035/oprtSchdInfoV2/get-oprt-schd-info-v2",
  "https://apis.data.go.kr/B554035/oprt-schd-info-v2/get-oprt-schd-info-v2",
  "https://apis.data.go.kr/B554035/oprtSchdInfo/get-oprt-schd-info-v2",
]

async function fetch_api(baseUrl, label, extra = {}) {
  const p = new URLSearchParams({
    serviceKey: KEY,
    pageNo: "1",
    numOfRows: "200",
    dataType: "JSON",
    rlvtYmd: TODAY,
    psnshpNm: "",
    ...extra,
  })
  const url = `${baseUrl}?${p}`
  console.log(`\n📡 [${label}]`)
  console.log("   ", url.replace(KEY, "***").slice(0, 130) + "...")

  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(12000) })
    const text = await res.text()
    console.log("   HTTP:", res.status)

    if (!res.ok) {
      console.log("   응답:", text.slice(0, 300))
      return null
    }

    let json
    try { json = JSON.parse(text) } catch {
      console.log("   JSON 파싱 실패:", text.slice(0, 300))
      return null
    }

    const header = json?.response?.header ?? json?.header
    const rc  = header?.resultCode
    const msg = (header?.resultMsg ?? "").trim()
    console.log(`   resultCode: ${rc} / ${msg}`)
    if (rc !== "00") return null

    const body = json?.response?.body ?? json?.body
    console.log("   totalCount:", body?.totalCount)

    const raw = body?.items?.item
    const arr = Array.isArray(raw) ? raw : raw ? [raw] : []
    console.log("   items 수:", arr.length)

    if (arr.length > 0) {
      console.log("   📋 필드:", Object.keys(arr[0]).join(", "))
      console.log("\n   ─── 첫 번째 item ───")
      console.log(JSON.stringify(arr[0], null, 4))
    }

    return arr
  } catch (e) {
    console.log("   오류:", e.message)
    return null
  }
}

// ═══ Step 1: 올바른 URL 탐색 ═══
console.log("\n════════ Step 1: API URL 탐색 ════════")
let BASE = null
for (const url of URL_CANDIDATES) {
  const result = await fetch_api(url, url.split("/").slice(-2).join("/"))
  if (result !== null) { BASE = url; break }
}

if (!BASE) {
  console.log("\n❌ 모든 URL 후보 실패.")
  console.log("   → data.go.kr에서 'ID 15142302' 검색 → 상세 페이지의 endpoint URL 확인")
  console.log("   → 또는 mtisopenapi.komsa.or.kr Swagger UI에서 실제 URL 확인")
  process.exit(1)
}

console.log("\n✅ 동작하는 URL:", BASE)

// ═══ Step 2: 전체 조회 후 완도 관련 필터링 ═══
console.log("\n════════ Step 2: 완도 관련 노선 조회 ════════")
const allItems = await fetch_api(BASE, "전체 여객선 (psnshpNm 빈값)")

if (allItems && allItems.length > 0) {
  const wandoItems = allItems.filter(item =>
    /완도|청산|소안|보길|노화|제주|화흥/.test(JSON.stringify(item))
  )
  console.log(`\n   완도 관련 항목: ${wandoItems.length}건`)
  wandoItems.forEach((item, i) => {
    console.log(`\n   [${i + 1}]`, JSON.stringify(item, null, 4))
  })
}

// ═══ Step 3: 청산도 선박명 직접 조회 ═══
console.log("\n════════ Step 3: 청산도 선박 직접 조회 ════════")
const targets = ["슬로시티청산도호", "청산아일랜드호", "섬사랑7호", "대한호", "민국호"]
for (const name of targets) {
  await fetch_api(BASE, `psnshpNm=${name}`, { psnshpNm: name, numOfRows: "20" })
}

// ═══ Step 4: 기존 KOMSA 결항 API 비교 ═══
console.log("\n════════ Step 4: 기존 KOMSA 결항 API (비교) ════════")
const komsaBase = "https://apis.data.go.kr/B554035/ferry-route-info-v4/get-ferry-route-info-v4"
const kp = new URLSearchParams({
  serviceKey: KEY, rlvtYmd: TODAY, psnshpNm: "슬로시티청산도호",
  dataType: "JSON", numOfRows: "5", pageNo: "1",
})
try {
  const res  = await fetch(`${komsaBase}?${kp}`)
  const json = await res.json()
  const rc   = json?.response?.header?.resultCode
  const raw  = json?.response?.body?.items?.item
  const arr  = Array.isArray(raw) ? raw : raw ? [raw] : []
  console.log(`   기존 KOMSA resultCode: ${rc}, items: ${arr.length}건`)
  if (arr[0]) console.log("   첫 item:", JSON.stringify(arr[0], null, 2))
} catch (e) {
  console.log("   오류:", e.message)
}

console.log("\n🏁 검증 완료")
