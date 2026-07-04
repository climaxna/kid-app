// data.go.kr KHOA 조석예보 서비스(15038991) 실제 URL 탐색
const KEY = process.env.DATAGOKR_API_KEY
const today = '20260617'

async function get(label, url) {
  try {
    const r = await fetch(url)
    const txt = await r.text()
    const urlMatches = txt.match(/apis\.data\.go\.kr\/[^\s"'<>]+/g) ?? []
    const khoaMatches = txt.match(/khoa\.go\.kr\/[^\s"'<>]+/g) ?? []
    if (urlMatches.length || khoaMatches.length) {
      console.log(label, '→ URL 발견:', [...urlMatches, ...khoaMatches].slice(0, 5))
    } else {
      console.log(label, 'HTTP', r.status, txt.slice(0, 300))
    }
  } catch (e) {
    console.log(label, 'ERR:', e.message)
  }
}

console.log('=== data.go.kr 서비스 15038991 정보 탐색 ===\n')

// 서비스 정보 페이지
await get('openapi 상세', 'https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15038991')

// API 직접 테스트 — KHOA 조석예보
// data.go.kr 서비스 코드 15038991 보통 기관코드 1192000
const qs = `serviceKey=${encodeURIComponent(KEY)}&_type=json&numOfRows=10&pageNo=1`

// 가능한 엔드포인트들
const endpoints = [
  ['TidePredictService/getTidePredictList', `tideDate=${today}&obsPostId=DT_0003`],
  ['TideForecastService/getTideForecastList', `tideDate=${today}&obsCode=DT_0003`],
  ['ObsTideInfoSvc/getObsTideInfoList', `tideDate=${today}&obsPostId=DT_0003`],
  ['ObsTidePredictService/getObsTidePredictList', `tideDate=${today}&obsPostId=DT_0003`],
  ['tidalPredictInfoService/getTidalPredictInfoList', `tideDate=${today}&obsCode=DT_0003`],
  ['tideObsPredictAPI/getTideObsPredictAPIList', `tideDate=${today}&obsCode=DW0011`],
]

for (const [path, params] of endpoints) {
  const url = `https://apis.data.go.kr/1192000/${path}?${qs}&${params}`
  try {
    const r = await fetch(url)
    const txt = await r.text()
    let j
    try { j = JSON.parse(txt) } catch { }
    const code = j?.response?.header?.resultCode
    if (code === '00') {
      const items = j?.response?.body?.items?.item
      const arr = Array.isArray(items) ? items : [items]
      console.log(path, '✅ 성공! 첫 항목:', JSON.stringify(arr[0]).slice(0, 200))
    } else if (code) {
      console.log(path, '❌', code, j?.response?.header?.resultMsg)
    } else {
      console.log(path, 'HTTP', r.status, txt.slice(0, 100))
    }
  } catch (e) {
    console.log(path, 'ERR:', e.message)
  }
}
