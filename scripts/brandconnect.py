"""네이버 브랜드커넥트(쇼핑 커넥트) 조회와 제휴 링크 발급.

cookies.json 로그인 세션으로 사용자 본인 계정만 다룬다. 쓰기 동작은 링크 발급 하나뿐이다.
브라우저 도구는 네이버 도메인이 막혀 있어서 이 파이썬 세션을 쓴다.

사용법 (결과는 JSON으로 stdout에 출력):
  python -X utf8 scripts/brandconnect.py tabs                 이벤트 탭 목록 (주문 TOP100, 시즌 TOP100 등)
  python -X utf8 scripts/brandconnect.py event <탭ID>         탭의 상품 전체
  python -X utf8 scripts/brandconnect.py search <검색어>      상품 검색
  python -X utf8 scripts/brandconnect.py product <상품ID>     상품 상세
  python -X utf8 scripts/brandconnect.py links                내가 발급한 링크 전체
  python -X utf8 scripts/brandconnect.py earnings             월별 커넥트 수익
  python -X utf8 scripts/brandconnect.py issue <상품ID>       제휴 링크 발급 (이미 있으면 기존 링크 반환)
"""

import contextlib
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import naver_blog_draft as n  # noqa: E402

SPACE_ID = "980734822180224"
BASE = "https://gw-brandconnect.naver.com/affiliate"
HEADERS = {
    "Origin": "https://brandconnect.naver.com",
    "Referer": f"https://brandconnect.naver.com/{SPACE_ID}/affiliate/products",
    "X-Space-Id": SPACE_ID,
    "Accept": "application/json",
}


def session():
    # load_session의 안내 문구가 JSON 출력에 섞이지 않게 stderr로 보낸다.
    with contextlib.redirect_stdout(sys.stderr):
        return n.load_session(n.find_cookies_path(None), n.DEFAULT_BLOG_ID, 18)


def get(s, path):
    r = s.get(f"{BASE}/query{path}", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def paged(s, path, max_pages=10):
    """page 파라미터로 끝까지 모은다. 응답은 {data, paging:{nextCursor}} 형태."""
    items, seen = [], set()
    sep = "&" if "?" in path else "?"
    for page in range(1, max_pages + 1):
        d = get(s, f"{path}{sep}page={page}")
        new = [x for x in d.get("data", []) if x.get("id") not in seen]
        for x in new:
            seen.add(x.get("id"))
            items.append(x)
        if not new or not d.get("paging", {}).get("nextCursor"):
            break
    return items


def slim(x):
    """글 작성에 필요한 필드만 남긴다."""
    review = x.get("reviewInfo") or {}
    price = x.get("discountedSalePrice") or x.get("salePrice") or 0
    rate = x.get("commissionRate") or 0
    return {
        "id": x.get("id"),
        "name": x.get("productName"),
        "store": x.get("storeName"),
        "price": price,
        "commissionRate": rate,
        "perSale": int(price * rate / 100),
        "reviews": review.get("totalReviewCount"),
        "score": review.get("averageReviewScore"),
        "productUrl": x.get("productUrl"),
        "link": x.get("shortenUrl"),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd, args = sys.argv[1], sys.argv[2:]
    s = session()
    if cmd == "tabs":
        out = get(s, "/event/tabs")
    elif cmd == "event":
        out = [slim(x) for x in paged(s, f"/affiliate-events/{args[0]}/products/search")]
    elif cmd == "search":
        q = urllib.parse.quote(" ".join(args))
        out = [slim(x) for x in paged(s, f"/affiliate-products/search-by-query?query={q}", 3)]
    elif cmd == "product":
        out = slim(get(s, f"/affiliate-products/{args[0]}"))
    elif cmd == "links":
        items, seen = [], set()
        for page in range(1, 20):
            r = s.post(f"{BASE}/query/affiliate-urls/search", headers={**HEADERS, "Content-Type": "application/json"},
                       data=json.dumps({"page": page}), timeout=20)
            r.raise_for_status()
            d = r.json()
            new = [x for x in d.get("data", []) if x.get("affiliateUrlId") not in seen]
            for x in new:
                seen.add(x.get("affiliateUrlId"))
                items.append({**slim(x), "createdAt": (x.get("urlCreatedAt") or "")[:10]})
            if not new or not d.get("paging", {}).get("nextCursor"):
                break
        out = items
    elif cmd == "earnings":
        out = get(s, "/connect-creator-settlements/recent-earnings")
    elif cmd == "issue":
        r = s.post(f"{BASE}/command/affiliate-urls?affiliateProductId={args[0]}",
                   headers={**HEADERS, "Content-Type": "application/json"}, data="{}", timeout=20)
        r.raise_for_status()
        out = r.json()
    else:
        print(__doc__)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
