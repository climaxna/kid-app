// KHOA 오픈마린데이터 API 목록 탐색
async function get(url) {
  const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } })
  return { status: r.status, text: await r.text() }
}

// KHOA API 목록 페이지
const intro = await get('https://www.khoa.go.kr/api/oceangrid/intro.do')
console.log('intro status:', intro.status)

// 조석 관련 서비스명 추출
const apiMatches = intro.text.match(/tide[A-Za-z]+|Tide[A-Za-z]+|조석[^\s<]{0,30}/g) ?? []
console.log('조석 관련 키워드:', [...new Set(apiMatches)].slice(0, 20))

// API 도메인/경로 추출
const paths = intro.text.match(/\/api\/oceangrid\/[^\s"'<>]+/g) ?? []
console.log('API 경로들:', [...new Set(paths)].slice(0, 20))

// KHOA에서 직접 확인 가능한 JSON 형식
const apiList = await get('https://www.khoa.go.kr/api/oceangrid/intro.do?_type=json')
console.log('JSON intro:', apiList.status, apiList.text.slice(0, 200))

// 조석예보 API 직접 시도 (ServiceKey 없이 → 오류 메시지 확인)
const noKey = await get('https://www.khoa.go.kr/api/oceangrid/tideObsPredicAPI.do/json')
console.log('noKey 응답:', noKey.status, noKey.text.slice(0, 200))

// 다른 경로들
for (const path of [
  'https://www.khoa.go.kr/api/oceangrid/ObsTidePredictAPI.do/json',
  'https://www.khoa.go.kr/api/oceangrid/obsPreTide.do/json',
  'https://www.khoa.go.kr/api/oceangrid/tidePredict.do/json',
]) {
  const res = await get(path)
  console.log(path.split('/').pop(), ':', res.status, res.text.slice(0, 100))
}
