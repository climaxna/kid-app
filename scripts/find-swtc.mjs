// KHOA swtc 경로 탐색
async function get(url) {
  try {
    const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0', 'Accept': '*/*' } })
    const txt = await r.text()
    return { status: r.status, text: txt }
  } catch (e) {
    return { status: 0, text: e.message }
  }
}

const base = 'https://www.khoa.go.kr'

// /swtc/ 경로 탐색
const swtc = await get(base + '/swtc/main.do')
console.log('swtc main:', swtc.status, swtc.text.slice(0, 100))

// API 경로 추출
const apiRefs = (swtc.text.match(/["']([^"']*\/api[^"']{5,80})['"]/g) ?? []).slice(0, 20)
const ajaxRefs = (swtc.text.match(/["']([^"']*\.do[^"']{0,50})['"]/g) ?? [])
  .filter(u => !u.includes('css') && !u.includes('js')).slice(0, 15)
console.log('API refs:', apiRefs)
console.log('AJAX (.do):', ajaxRefs.slice(0, 10))

// data.go.kr 조석예보 API URL 패턴 (다시 시도 — 올바른 URL)
const svcPage = await get('https://www.data.go.kr/data/15038991/openapi.do')
const jsRefs = (svcPage.text.match(/apis\.data\.go\.kr[^\s"'<>]+/g) ?? []).slice(0, 10)
const endpointRefs = (svcPage.text.match(/(basePath|endpoint|baseUrl|apiUrl)[^<>]{0,200}/gi) ?? []).slice(0, 5)
console.log('\ndata.go.kr 15038991:')
console.log('apis.data.go.kr refs:', jsRefs)
console.log('endpoint refs:', endpointRefs)

// /swtc/api 경로들 시도
for (const path of [
  '/swtc/api/tidePredict',
  '/swtc/tide/getTidePredict.do',
  '/swtc/api/getTidePredict.do',
  '/swtc/sttnTidePredct/getTidePredict.do',
]) {
  const r = await get(base + path + '?obsCode=DW0011&date=20260617&_type=json')
  console.log(path, ':', r.status, r.text.slice(0, 100))
}
