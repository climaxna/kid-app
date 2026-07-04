// data.go.kr 서비스 15038991 실제 API URL 탐색
async function get(url) {
  const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0', 'Accept': '*/*' } })
  return await r.text()
}

const html = await get('https://www.data.go.kr/data/15038991/openapi.do')
const urls = (html.match(/https?:\/\/[^\s"'<>]+/g) ?? [])
  .filter(u => u.includes('apis.data') || u.includes('khoa'))
console.log('관련 URLs:', urls.slice(0, 10))

const title = html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1]
console.log('title:', title)

// swagger / api 경로 검색
const swaggerMatch = html.match(/swagger[^"'<>]{0,200}/gi)?.slice(0, 3)
console.log('swagger mentions:', swaggerMatch)

const baseUrlMatch = html.match(/baseUrl[^"'<>]{0,100}/gi)?.slice(0, 3)
console.log('baseUrl:', baseUrlMatch)

// HTML에서 특정 서비스명 패턴
const svcPattern = html.match(/1192000[^\s"'<>]{0,80}/g)?.slice(0, 5)
console.log('1192000 org paths:', svcPattern)
