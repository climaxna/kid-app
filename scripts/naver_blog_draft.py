#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 블로그 임시저장 스크립트.

로컬 cookies.json(브라우저 확장 내보내기 형식: [{name, value, domain, path, ...}, ...])에서
네이버 로그인 쿠키를 읽어 requests 세션에 적용하고, 제목/본문을 SE 에디터
documentModel JSON으로 변환해 임시저장한다. payload 구조는 실제 브라우저가 보내는
RabbitTempPostWrite/RabbitTempPostUpdate 요청을 그대로 재현한다.

사용법:
    python scripts/naver_blog_draft.py "제목" "본문 내용"
    python scripts/naver_blog_draft.py "제목" --body-file 본문.txt
    python scripts/naver_blog_draft.py "제목" "본문" --category 18 --debug

본문에 줄바꿈(\\n)이 있으면 문단(paragraph)이 분리된다.
"""
import argparse
import json
import secrets
import sys
import time
import uuid
from pathlib import Path

import requests

# 임시저장(신규 생성) 엔드포인트. 기존 임시글 갱신은 RabbitTempPostUpdate.naver
WRITE_URL = "https://blog.naver.com/RabbitTempPostWrite.naver"
DEFAULT_BLOG_ID = "climaxna"
DEFAULT_CATEGORY_ID = 18

# 에디터 인스턴스 토큰. 캡처된 값(세션에 따라 달라질 수 있음 — 실패 시 --editor-source 로 최신값 지정)
DEFAULT_EDITOR_SOURCE = "IK00H4dPooL7OdSPoAhfQQ=="

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32


def gen_ulid() -> str:
    """네이버 documentModel document.id 용 ULID(26자) 생성."""
    ts = int(time.time() * 1000) & ((1 << 48) - 1)
    value = (ts << 80) | secrets.randbits(80)  # 128비트
    chars = []
    for _ in range(26):
        chars.append(_ULID_ALPHABET[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def se_id() -> str:
    """SE 컴포넌트/노드용 고유 id (예: SE-a1b2c3d4-...)."""
    return "SE-" + str(uuid.uuid4())


def find_cookies_path(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            sys.exit(f"[오류] 지정한 쿠키 파일이 없습니다: {p}")
        return p
    here = Path(__file__).resolve().parent
    candidates = [
        Path.cwd() / "cookies.json",
        here.parent / "cookies.json",
        here / "cookies.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    sys.exit(
        "[오류] cookies.json 을 찾을 수 없습니다. 프로젝트 루트에 두거나 "
        "--cookies 경로를 지정하세요.\n  탐색한 위치: "
        + ", ".join(str(c) for c in candidates)
    )


def load_session(cookies_path: Path, blog_id: str, category_id: int) -> requests.Session:
    """cookies.json(list/dict 지원)을 requests 세션에 적용하고 헤더 세팅."""
    try:
        raw = json.loads(cookies_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[오류] cookies.json 파싱 실패: {e}")

    session = requests.Session()
    referer = (
        f"https://blog.naver.com/PostWriteForm.naver?blogId={blog_id}"
        f"&Redirect=Write&redirect=Write&widgetTypeCall=true&categoryNo={category_id}"
        f"&topReferer=https%3A%2F%2Fblog.naver.com%2FPostList.naver%3FblogId%3D{blog_id}"
        f"&trackingCode=blog_bloghome&directAccess=false"
    )
    session.headers.update({
        "accept": "application/json, text/plain, */*",
        "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://blog.naver.com",
        "referer": referer,
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
    })

    count = 0
    if isinstance(raw, list):
        for c in raw:
            name, value = c.get("name"), c.get("value")
            if name is None or value is None:
                continue
            session.cookies.set(
                name, value,
                domain=c.get("domain", ".naver.com").lstrip("."),
                path=c.get("path", "/"),
            )
            count += 1
    elif isinstance(raw, dict):
        for name, value in raw.items():
            session.cookies.set(name, str(value), domain="naver.com", path="/")
            count += 1
    else:
        sys.exit("[오류] cookies.json 형식을 인식할 수 없습니다 (list 또는 dict 필요).")

    if count == 0:
        sys.exit("[오류] cookies.json 에서 적용된 쿠키가 없습니다.")
    print(f"[정보] 쿠키 {count}개 적용됨 ({cookies_path})")
    return session


def build_document_model(title: str, body_text: str) -> str:
    """제목/본문을 네이버 SE 에디터 documentModel JSON 문자열로 변환 (실제 캡처 구조)."""
    def paragraph(text: str) -> dict:
        return {
            "id": se_id(),
            "nodes": [{"id": se_id(), "value": text, "@ctype": "textNode"}],
            "@ctype": "paragraph",
        }

    body_paragraphs = [paragraph(line) for line in body_text.split("\n")] or [paragraph("")]

    document = {
        "documentId": "",
        "document": {
            "version": "2.10.2",
            "theme": "default",
            "language": "ko-KR",
            "id": gen_ulid(),
            "di": {"dif": False, "dio": [{"dis": "N", "dia": {"t": 0, "p": 0, "st": 0, "sk": 0}}]},
            "components": [
                {
                    "id": se_id(),
                    "layout": "default",
                    "title": [paragraph(title)],
                    "subTitle": None,
                    "align": "left",
                    "@ctype": "documentTitle",
                },
                {
                    "id": se_id(),
                    "layout": "default",
                    "value": body_paragraphs,
                    "@ctype": "text",
                },
            ],
        },
    }
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"))


def build_population_params(category_id: int, editor_source: str, auto_save_no: int) -> str:
    params = {
        "configuration": {
            "openType": 2, "commentYn": True, "searchYn": True, "sympathyYn": True,
            "scrapType": 2, "outSideAllowYn": False, "twitterPostingYn": False,
            "facebookPostingYn": False, "cclYn": False,
        },
        "populationMeta": {
            "categoryId": category_id, "logNo": None, "directorySeq": 0,
            "directoryDetail": None, "mrBlogTalkCode": None, "postWriteTimeType": "now",
            "tags": None, "moviePanelParticipation": False, "greenReviewBannerYn": False,
            "continueSaved": False, "noticePostYn": False, "autoByCategoryYn": False,
            "postLocationSupportYn": False, "postLocationJson": None, "prePostDate": None,
            "thisDayPostInfo": None, "scrapYn": False, "autoSaveNo": auto_save_no,
        },
        "editorSource": editor_source,
    }
    return json.dumps(params, ensure_ascii=False, separators=(",", ":"))


def save_draft(session, blog_id, title, body_text, category_id, editor_source, debug=False) -> bool:
    data = {
        "blogId": blog_id,
        "documentModel": build_document_model(title, body_text),
        "mediaResources": json.dumps({"image": [], "video": [], "file": []}, separators=(",", ":")),
        "populationParams": build_population_params(
            category_id, editor_source, auto_save_no=int(time.time() * 1000)
        ),
    }
    if debug:
        print("[디버그] 전송 URL:", WRITE_URL)
        for k, v in data.items():
            print(f"[디버그] data[{k}] = {v}")

    try:
        resp = session.post(WRITE_URL, data=data, timeout=30)
    except requests.RequestException as e:
        print(f"[실패] 요청 오류: {e}")
        return False

    text = resp.text.strip()
    print(f"[정보] HTTP {resp.status_code}")

    ok = False
    try:
        j = resp.json()
        ok = bool(
            j.get("isSuccess")
            or isinstance(j.get("result"), dict)
            or j.get("logNo")
            or str(j.get("code", "")).lower() in ("success", "0", "200")
        )
        preview = json.dumps(j, ensure_ascii=False)[:500]
    except ValueError:
        preview = text[:500]
        lowered = text.lower()
        if resp.status_code == 200 and "login" not in lowered and "로그인" not in text:
            ok = True

    if resp.status_code == 200 and ok:
        print("[성공] 임시저장 완료 ✅")
    else:
        print("[실패] 임시저장 실패 ❌ (쿠키 만료·editorSource·카테고리ID 확인 필요)")
    print(f"[응답] {preview}")
    return resp.status_code == 200 and ok


def main():
    ap = argparse.ArgumentParser(description="네이버 블로그 임시저장")
    ap.add_argument("title", help="글 제목")
    ap.add_argument("body", nargs="?", default=None, help="본문 텍스트 (또는 --body-file)")
    ap.add_argument("--body-file", help="본문을 읽어올 텍스트 파일 경로 (UTF-8)")
    ap.add_argument("--blog-id", default=DEFAULT_BLOG_ID, help=f"blogId (기본 {DEFAULT_BLOG_ID})")
    ap.add_argument("--category", type=int, default=DEFAULT_CATEGORY_ID,
                    help=f"categoryId (기본 {DEFAULT_CATEGORY_ID})")
    ap.add_argument("--editor-source", default=DEFAULT_EDITOR_SOURCE,
                    help="editorSource 토큰 (세션별로 다르면 최신값 지정)")
    ap.add_argument("--cookies", help="cookies.json 경로 (기본: 자동 탐색)")
    ap.add_argument("--debug", action="store_true", help="전송 payload 출력")
    args = ap.parse_args()

    if args.body_file:
        body_text = Path(args.body_file).read_text(encoding="utf-8")
    elif args.body is not None:
        body_text = args.body
    else:
        ap.error("본문을 body 인자 또는 --body-file 로 제공하세요.")

    session = load_session(find_cookies_path(args.cookies), args.blog_id, args.category)
    success = save_draft(
        session, args.blog_id, args.title, body_text, args.category, args.editor_source, debug=args.debug
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
