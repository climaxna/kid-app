/**
 * TAGO 국내선박운항정보서비스 응답 테스트
 * 실행: node --env-file=.env.local scripts/test-tago.mjs
 *
 * 확인된 API:
 *   Base: https://apis.data.go.kr/1613000/DmstcShipNvgInfo
 *   Ops: GetShipOpratInfoList / GetPortList / GetPsnshipTrminlList / GetShipKndList
 *   완도항 nodeId: SEA31020  / 완도_화흥포: SEA31022
 */

const KEY = process.env.DATAGOKR_API_KEY
if (!KEY) {
  console.error("❌ DATAGOKR_API_KEY 없음 — .env.local 확인")
  process.exit(1)
}

const BASE = "https://apis.data.go.kr/1613000/DmstcShipNvgInfo"
const kst = new Date(Date.now() + 9 * 60 * 60 * 1000)
const TODAY = kst.toISOString().slice(0, 10).replace(/-/g, "")

console.log("🔑 키 앞 8자리:", KEY.slice(0, 8) + "...")
console.log("📅 조회 날짜:", TODAY)

async function call(label, url) {
  console.log(`\n📡 [${label}]`)
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
      const arr = Array.isArray(item) ? item : item ? [item] : []
      if (arr[0]) console.log("첫 번째 item:", JSON.stringify(arr[0], null, 2))
    } catch {
      console.log("Raw:", text.slice(0, 300))
    }
  } catch (e) {
    console.log("오류:", e.message)
  }
}

const q = `serviceKey=${KEY}&_type=json&numOfRows=5&pageNo=1`

// 1. 완도항 오늘 운항 목록
await call("완도항 운항정보 (SEA31020)", `${BASE}/GetShipOpratInfoList?${q}&depNodeId=SEA31020&depPlandTime=${TODAY}`)

// 2. 완도화흥포 오늘 운항 목록
await call("완도화흥포 운항정보 (SEA31022)", `${BASE}/GetShipOpratInfoList?${q}&depNodeId=SEA31022&depPlandTime=${TODAY}`)

// 3. 항구 목록 (완도 검색용)
await call("항구 목록 (첫 5개)", `${BASE}/GetPortList?${q}`)

// 4. 여객선터미널 목록
await call("여객선터미널 목록 (첫 5개)", `${BASE}/GetPsnshipTrminlList?${q}`)
