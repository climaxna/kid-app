// KHOA 조석예보 서비스 탐색 v2 — 키 인코딩 없이, 파라미터 다양하게
const KEY = process.env.DATAGOKR_API_KEY
const today = '20260617'

console.log('키 앞8:', KEY.slice(0, 8), '뒤4:', KEY.slice(-4))

async function get(label, url) {
  try {
    const r = await fetch(url)
    const txt = await r.text()
    let j
    try { j = JSON.parse(txt) } catch { }
    const code = j?.response?.header?.resultCode
    if (code === '00') {
      const items = j?.response?.body?.items?.item
      const arr = Array.isArray(items) ? items : [items]
      console.log(label, '✅ 성공! 첫 항목:', JSON.stringify(arr[0]).slice(0, 300))
    } else if (code) {
      console.log(label, '❌', code, j?.response?.header?.resultMsg)
    } else if (j) {
      console.log(label, 'JSON?', JSON.stringify(j).slice(0, 200))
    } else {
      console.log(label, 'HTTP', r.status, txt.slice(0, 150))
    }
  } catch (e) {
    console.log(label, 'ERR:', e.message)
  }
}

// 키 인코딩 없이
const qRaw = `serviceKey=${KEY}&_type=json&numOfRows=10&pageNo=1`
const qEnc = `serviceKey=${encodeURIComponent(KEY)}&_type=json&numOfRows=10&pageNo=1`

// 실제 KHOA 조석예보가 등록된 data.go.kr 경로들
// 서비스코드 15038991 → 주로 1192000 기관 또는 1613000
const paths = [
  '1192000/ObsTidePredictInfoService2/getObsTidePredictInfoList2',
  '1192000/ObsTideInfo/getObsTideInfoList',
  '1192000/ObsTidePrediction/getObsTidePredictionList',
  '1192000/KHOA_TidePrediction/getTidePredictionList',
]

console.log('\n[키 인코딩 없이]')
for (const p of paths) {
  await get(p.split('/')[1], `https://apis.data.go.kr/${p}?${qRaw}&obsPostId=DT_0003&tideDate=${today}`)
}

console.log('\n[키 인코딩 적용]')
for (const p of paths.slice(0, 2)) {
  await get(p.split('/')[1]+'(enc)', `https://apis.data.go.kr/${p}?${qEnc}&obsPostId=DT_0003&tideDate=${today}`)
}

// data.go.kr API 목록 (인증 불필요)
await get('orgAPI list', `https://www.data.go.kr/tcs/apf/apfBizAPI.do?action=getAPIInfoList&orgId=1192000&_type=json`)
