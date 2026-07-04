// KHOA 조석예보 API URL 탐색 v3
// data.go.kr 카탈로그를 통해 실제 baseUrl 찾기

async function get(url, asJson) {
  const r = await fetch(url, { headers: { 'Accept': 'application/json, text/html', 'User-Agent': 'Mozilla/5.0' } })
  const txt = await r.text()
  if (asJson) {
    try { return { status: r.status, data: JSON.parse(txt) } } catch {}
  }
  return { status: r.status, text: txt }
}

// 1. data.go.kr API 상세 정보 (Swagger)
const swag = await get('https://www.data.go.kr/tcs/apf/apfBizAPI.do?action=getSwaggerInfoByPublicDataPk&publicDataPk=15038991', true)
console.log('Swagger by PK:', swag.status, JSON.stringify(swag.data).slice(0, 400))

// 2. data.go.kr 서비스 목록에서 KHOA 조석예보 찾기 (HTML 파싱)
const list = await get('https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=API&keyword=%EC%A1%B0%EC%84%9D%EC%98%88%EB%B3%B4&orgId=1192000')
const apiPaths = (list.text?.match(/\/api\/oceangrid\/[^"'\s<>]+/g) ?? [])
  .filter((v, i, a) => a.indexOf(v) === i)
console.log('조석예보 API paths:', apiPaths.slice(0, 10))

// 3. KHOA의 정확한 도메인 확인
const domains = [
  'https://api.khoa.go.kr',
  'https://data.khoa.go.kr/api',
  'https://www.khoa.go.kr/oceangrid',
]
for (const d of domains) {
  const r = await get(d + '/intro.do')
  console.log(d, ':', r.status, r.text?.slice(0, 80))
}

// 4. data.go.kr에서 기관코드 1192000 API 목록
const orgList = await get('https://www.data.go.kr/tcs/apf/apfBizAPI.do?action=getAPIInfoListByOrg&orgId=1192000')
const paths2 = (orgList.text?.match(/baseUrl[^"]{0,150}/g) ?? []).slice(0, 10)
console.log('1192000 baseUrl:', paths2)
