// KHOA swtc/main.do JavaScript에서 실제 API 호출 찾기
async function get(url) {
  try {
    const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0', 'Accept': '*/*' } })
    return { status: r.status, text: await r.text() }
  } catch (e) {
    return { status: 0, text: e.message }
  }
}

// swtc main 페이지 HTML 전체 가져오기
const main = await get('https://www.khoa.go.kr/swtc/main.do')
console.log('swtc HTML len:', main.text.length)

// JS 파일 경로 추출
const jsFiles = (main.text.match(/src=["']([^"']+\.js[^"']*)['"]/g) ?? []).slice(0, 10)
console.log('JS files:', jsFiles)

// AJAX/fetch URL 패턴 추출
const ajaxUrls = (main.text.match(/["'](\/[^"']*getSttn[^"']+)['"]/g) ?? [])
  .concat(main.text.match(/["'](\/swtc\/[^"']{5,60})['"]/g) ?? [])
  .filter((v, i, a) => a.indexOf(v) === i)
console.log('swtc AJAX:', ajaxUrls.slice(0, 20))

// 공개 ServiceKey 사용해서 swtc 관련 API 시도
const pubKey = '0A71D7EFDF5DD8D252A26716A'
const testUrls = [
  `https://www.khoa.go.kr/swtc/api/tidePredict?ServiceKey=${pubKey}&obsCode=DW0011&date=20260617`,
  `https://www.khoa.go.kr/swtc/sttn/getSttnTidePredct.do?ServiceKey=${pubKey}&sttnId=DW0011&tmFc=20260617`,
  `https://www.khoa.go.kr/api/oceangrid/tideObsPredicAPI.do/json?ServiceKey=${pubKey}&ObsCode=DW0011&Date=20260617`,
]
for (const url of testUrls) {
  const r = await get(url)
  const isJson = r.text.trim().startsWith('{') || r.text.trim().startsWith('[')
  console.log(url.replace(pubKey, '***'), ':', r.status, isJson ? r.text.slice(0, 200) : r.text.slice(0, 80))
}
