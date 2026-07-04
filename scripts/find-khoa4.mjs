// KHOA API 현재 운영 경로 확인
async function get(url) {
  try {
    const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0', 'Accept': '*/*' } })
    const txt = await r.text()
    return { status: r.status, text: txt }
  } catch (e) {
    return { status: 0, text: e.message }
  }
}

// KHOA 메인 홈 — API 경로 추출
const main = await get('https://www.khoa.go.kr')
const found = (main.text.match(/["']([^"']*\/api\/[^"']{5,50}["'])/g) ?? []).slice(0, 15)
console.log('KHOA main API refs:', found)

// API 목록 페이지 후보
for (const path of [
  '/api/',
  '/api/oceangrid/',
  '/oceangrid/ocean/oceangridIntr.do',
  '/oceangrid/api/intro.do',
  '/swtc/api/intro.do',
]) {
  const r = await get('https://www.khoa.go.kr' + path)
  const apiPaths = (r.text.match(/\/api\/[^\s"'<>]{5,60}/g) ?? [])
    .filter((v, i, a) => a.indexOf(v) === i).slice(0, 5)
  console.log(path, ':', r.status, apiPaths.length ? apiPaths : r.text.slice(0, 60))
}

// data.go.kr에서 조석예보 API 정보 직접 조회
const svcInfo = await get('https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15038991')
const endpointMatch = svcInfo.text.match(/endPoint[^<>]{0,200}/g) ?? []
const baseUrlMatch = svcInfo.text.match(/baseUrl[^<>]{0,200}/g) ?? []
const urlMatch = svcInfo.text.match(/apis\.data\.go\.kr\/[^\s"'<>]+/g) ?? []
console.log('endPoint:', endpointMatch.slice(0, 3))
console.log('baseUrl:', baseUrlMatch.slice(0, 3))
console.log('apis.data.go.kr paths:', urlMatch.slice(0, 5))
