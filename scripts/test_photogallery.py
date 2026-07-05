import urllib.request
import urllib.parse
import urllib.error

key = open("C:/blog/.env", encoding="utf-8").read().split("=", 1)[1].strip()
base = "https://apis.data.go.kr/B551011/PhotoGalleryService1/gallerySearchList1"
params = {
    "serviceKey": key,
    "numOfRows": "10",
    "pageNo": "1",
    "MobileOS": "ETC",
    "MobileApp": "wando-blog",
    "keyword": "노화도",
    "_type": "json",
}
url = base + "?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read().decode("utf-8")
        print(data[:3000])
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, e.reason)
    print(e.read().decode("utf-8", errors="replace")[:2000])
except Exception as e:
    print("ERROR", e)
