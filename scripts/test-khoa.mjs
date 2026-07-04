/**
 * 국립해양조사원 조석예보(고·저조) API 테스트
 * Base URL: apis.data.go.kr/1192136/tideFcstHghLw
 * 완도 예보지점 코드: DT_0027
 * 실행: node --env-file=.env.local scripts/test-khoa.mjs
 */

const KEY = process.env.DATAGOKR_API_KEY
if (!KEY) {
  console.error("❌ DATAGOKR_API_KEY 없음 — .env.local 확인")
  process.exit(1)
}

console.log("🔑 키 앞 8자리:", KEY.slice(0, 8) + "...")

const kst = new Date(Date.now() + 9 * 60 * 60 * 1000)
const today = kst.toISOString().slice(0, 10).replace(/-/g, "")
const tomorrow = new Date(kst.getTime() + 86400000).toISOString().slice(0, 10).replace(/-/g, "")
console.log("📅 오늘:", today, "내일:", tomorrow)

const base = "https://apis.data.go.kr/1192136/tideFcstHghLw/GetTideFcstHghLwApiService"

async function call(label, params) {
  const url = base + "?" + new URLSearchParams({ serviceKey: KEY, type: "json", numOfRows: "20", pageNo: "1", ...params })
  console.log(`\n📡 [${label}]`)
  try {
    const r = await fetch(url)
    const j = await r.json()
    const rc = j?.header?.resultCode
    console.log("resultCode:", rc, "/", j?.header?.resultMsg)
    if (rc !== "00") return

    const items = j?.body?.items?.item
    const arr = Array.isArray(items) ? items : [items]
    console.log("이벤트 수:", arr.length)
    for (const it of arr) {
      const type = Number(it.extrSe) % 2 === 1 ? "고조 🔴" : "저조 🔵"
      const time = String(it.predcDt).slice(11, 16)
      console.log(`  ${time}  ${type}  ${it.predcTdlvVl}cm`)
    }
  } catch (e) {
    console.log("오류:", e.message)
  }
}

await call("완도(DT_0027) 오늘", { obsCode: "DT_0027", reqDate: today })
await call("완도(DT_0027) 내일", { obsCode: "DT_0027", reqDate: tomorrow })
