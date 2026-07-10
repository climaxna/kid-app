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

사진: 본문의 `📷 [사진 N] 검색어: `키워드`` 표시는 기본적으로 텍스트 그대로 유지된다
(수동으로 이미지를 넣을 자리 표시용). --with-images 옵션을 주면 한국관광공사
관광사진에서 자동 검색·업로드해 실제 사진으로 채워 넣는다 (tour_images.py).
"""
import argparse
import json
import os
import re
import secrets
import sys
import tempfile
import time
import uuid
from pathlib import Path

import requests

import tour_images

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


URL_RE = re.compile(r"(https?://[^\s]+)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
# 스타일 스키마(실제 캡처로 확인):
#   textNode.style  = {"bold":true, "fontSizeCode":"fs24", "fontColor":"#rrggbb", "@ctype":"nodeStyle"}
#   paragraph.style = {"align":"center", "@ctype":"paragraphStyle"}
#   인용구 = @ctype:"quotation", 구분선 = @ctype:"horizontalLine"


def text_node(value: str, link: str | None = None, bold: bool = False,
              font_size: str | None = None, font_color: str | None = None) -> dict:
    node = {"id": se_id(), "value": value}
    if link:
        node["link"] = {"url": link, "@ctype": "urlLink"}
    style = {}
    if bold:
        style["bold"] = True
    if font_size:
        style["fontSizeCode"] = font_size
    if font_color:
        style["fontColor"] = font_color
    if style:
        style["@ctype"] = "nodeStyle"
        node["style"] = style
    node["@ctype"] = "textNode"
    return node


def _linkify_segment(seg: str, bold: bool, font_size, font_color, out: list):
    """한 텍스트 조각 안의 URL을 링크 노드로 분리해 out에 추가."""
    pos = 0
    for m in URL_RE.finditer(seg):
        if m.start() > pos:
            out.append(text_node(seg[pos:m.start()], bold=bold, font_size=font_size, font_color=font_color))
        url = m.group(1)
        out.append(text_node(url, link=url, bold=bold, font_size=font_size, font_color=font_color))
        pos = m.end()
    if pos < len(seg):
        out.append(text_node(seg[pos:], bold=bold, font_size=font_size, font_color=font_color))


def inline_nodes(text: str, bold: bool = False, font_size=None, font_color=None,
                 parse_bold: bool = False) -> list[dict]:
    """줄을 textNode 리스트로. URL은 항상 링크로, parse_bold면 `**...**`도 굵게 처리."""
    nodes: list[dict] = []
    if parse_bold and "**" in text:
        pos = 0
        for m in BOLD_RE.finditer(text):
            if m.start() > pos:
                _linkify_segment(text[pos:m.start()], bold, font_size, font_color, nodes)
            _linkify_segment(m.group(1), True, font_size, font_color, nodes)
            pos = m.end()
        if pos < len(text):
            _linkify_segment(text[pos:], bold, font_size, font_color, nodes)
    else:
        _linkify_segment(text, bold, font_size, font_color, nodes)
    if not nodes:
        nodes.append(text_node("", bold=bold, font_size=font_size, font_color=font_color))
    return nodes


def linkify_nodes(text: str) -> list[dict]:
    """줄 안의 http(s):// URL을 클릭 가능한 urlLink textNode로 분리 (스타일 없음)."""
    return inline_nodes(text)


def paragraph(text: str, align: str | None = None, bold: bool = False,
              font_size: str | None = None, font_color: str | None = None,
              parse_bold: bool = False) -> dict:
    para = {
        "id": se_id(),
        "nodes": inline_nodes(text, bold=bold, font_size=font_size, font_color=font_color, parse_bold=parse_bold),
        "@ctype": "paragraph",
    }
    if align:
        para["style"] = {"align": align, "@ctype": "paragraphStyle"}
    return para


def quotation_component(lines: list[str]) -> dict:
    paras = [paragraph(l, align="center") for l in lines] or [paragraph("")]
    return {
        "id": se_id(), "layout": "default", "value": paras,
        "source": None, "align": "center", "@ctype": "quotation",
    }


def horizontal_line() -> dict:
    return {"id": se_id(), "layout": "default", "align": "center", "@ctype": "horizontalLine"}


MOMBLOG_DIRECTIVE = "<!-- momblog -->"
HEADING_RE = re.compile(r"^##\s+(.*)$")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
DIVIDER_RE = re.compile(r"^[\-─—]{3,}$")
HEADING_FONT_SIZE = "fs19"


def is_table_separator(line: str) -> bool:
    """`|------|------|` 같은 마크다운 표 구분선인지 확인."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    parts = [p.strip() for p in stripped.strip("|").split("|")]
    return bool(parts) and all(re.fullmatch(r":?-{2,}:?", p) for p in parts if p)


def parse_table_row(line: str) -> list[str]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return [c.replace("**", "") for c in cells]


def table_cell(text: str, width: float) -> dict:
    return {
        "id": se_id(),
        "colSpan": 1,
        "rowSpan": 1,
        "width": width,
        "height": 43,
        "value": [paragraph(text)] if text else None,
        "@ctype": "tableCell",
    }


def table_component(rows: list[list[str]]) -> dict:
    col_count = max(len(r) for r in rows)
    cell_width = round(100 / col_count, 2)
    se_rows = [
        {
            "cells": [
                table_cell(row[i] if i < len(row) else "", cell_width)
                for i in range(col_count)
            ],
            "@ctype": "tableRow",
        }
        for row in rows
    ]
    return {
        "id": se_id(),
        "layout": "default",
        "width": 100,
        "rows": se_rows,
        "columnCount": col_count,
        "borderStyleName": "thinLine",
        "@ctype": "table",
    }


def text_component(paragraphs: list[dict]) -> dict:
    return {
        "id": se_id(),
        "layout": "default",
        "value": paragraphs,
        "@ctype": "text",
    }


IMAGE_PLACEHOLDER_RE = re.compile(r"^\s*📷\s*\[사진\s*\d+\]\s*검색어:\s*`([^`]+)`")
ATTRIBUTION_RE = re.compile(r"^\s*\(ⓒ")


def image_component(upload: dict, represent: bool = False) -> dict:
    path = upload["path"]
    return {
        "id": se_id(),
        "layout": "default",
        "src": f"{tour_images.IMAGE_DOMAIN}{path}?type=w1",
        "internalResource": True,
        "represent": represent,
        "path": path,
        "domain": tour_images.IMAGE_DOMAIN,
        "fileSize": upload["fileSize"],
        "width": upload["width"],
        "widthPercentage": 0,
        "height": upload["height"],
        "originalWidth": upload["width"],
        "originalHeight": upload["height"],
        "fileName": upload["fileName"],
        "caption": None,
        "format": "normal",
        "displayFormat": "normal",
        "imageLoaded": True,
        "contentMode": "normal",
        "origin": {"srcFrom": "local", "@ctype": "imageOrigin"},
        "ai": False,
        "@ctype": "image",
    }


def prepare_image_results(body_text: str) -> list:
    """본문의 `📷 [사진 N] 검색어: `키워드`` 순서대로 관광사진을 검색·다운로드하고
    브라우저로 네이버에 업로드한다. 각 placeholder에 대응하는 (item, upload) 또는 None
    리스트를 순서대로 반환한다."""
    lines = body_text.split("\n")
    keywords = []
    for line in lines:
        m = IMAGE_PLACEHOLDER_RE.match(line)
        if m:
            keywords.append(m.group(1))
    if not keywords:
        return []

    results: list = [None] * len(keywords)
    tmpdir = tempfile.mkdtemp(prefix="wando_img_")
    items_by_idx: dict[int, dict] = {}
    to_upload: list[tuple[int, str]] = []
    used_urls: set[str] = set()  # 같은 문서 내 사진 중복 방지 (로테이션)
    for idx, kw in enumerate(keywords):
        dest = os.path.join(tmpdir, f"{idx}.jpg")
        try:
            item = tour_images.search_and_download(kw, dest, exclude_urls=used_urls)
        except Exception as e:
            print(f"[경고] 이미지 검색/다운로드 실패 ({kw}): {e}")
            item = None
        if item:
            items_by_idx[idx] = item
            to_upload.append((idx, dest))
            used_urls.add(item["image_url"])
            print(f"[정보] 사진 {idx + 1} 매칭: '{item['matched_keyword']}' → {item['title']} (ⓒ{item['photographer']})")
        else:
            print(f"[경고] 이미지 없음 ({kw}) — 이 자리는 텍스트로 유지")

    if to_upload:
        try:
            uploads = tour_images.upload_images_via_browser([p for _, p in to_upload])
        except Exception as e:
            print(f"[경고] 이미지 업로드 실패: {e}")
            uploads = [None] * len(to_upload)
        for (idx, _), up in zip(to_upload, uploads):
            if up and up.get("path"):
                results[idx] = (items_by_idx[idx], up)
            else:
                print(f"[경고] 업로드 실패 — 사진 {idx + 1}은 텍스트로 유지")

    ok = sum(1 for r in results if r)
    print(f"[정보] 이미지 {ok}/{len(keywords)}장 준비 완료")
    return results


def body_to_components(body_text: str, image_results: list | None = None) -> list[dict]:
    """본문 텍스트를 최상위 컴포넌트 리스트(text/table/image)로 변환.

    `| a | b |` 헤더 다음 줄이 `|---|---|` 형태 구분선이면 마크다운 표로 보고
    실제 네이버 table 컴포넌트로 변환한다 (table은 text와 형제 관계인 별도 컴포넌트여야 함).
    `📷 [사진 N] 검색어: `키워드`` 줄은 image_results(prepare_image_results 결과)의 대응
    항목이 있으면 실제 image 컴포넌트로 바꾼다 (없으면 원문 텍스트 유지).
    그 외 줄은 일반 문단(URL은 자동 링크)으로 묶어 하나의 text 컴포넌트에 담는다.
    """
    image_results = image_results or []
    lines = body_text.split("\n")

    # momblog 지시자가 있으면 리치 스타일(가운데정렬·## 헤딩·> 인용구·--- 구분선·**볼드**) 활성화
    momblog = any(ln.strip() == MOMBLOG_DIRECTIVE for ln in lines)
    if momblog:
        lines = [ln for ln in lines if ln.strip() != MOMBLOG_DIRECTIVE]
    base_align = "center" if momblog else None

    def make_para(text: str) -> dict:
        return paragraph(text, align=base_align, parse_bold=momblog)

    components: list[dict] = []
    para_buffer: list[dict] = []
    represent_used = False
    img_idx = 0

    def flush_paragraphs():
        if para_buffer:
            components.append(text_component(list(para_buffer)))
            para_buffer.clear()

    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        m = IMAGE_PLACEHOLDER_RE.match(line)
        if m:
            result = image_results[img_idx] if img_idx < len(image_results) else None
            img_idx += 1
            if result:
                item, upload = result
                flush_paragraphs()
                components.append(image_component(upload, represent=not represent_used))
                represent_used = True
                photographer = item["photographer"] or "포토코리아"
                para_buffer.append(make_para(f"(ⓒ한국관광공사 {photographer})"))
                i += 1
                if i < n and ATTRIBUTION_RE.match(lines[i]):
                    i += 1
                continue
        if line.strip().startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]):
            rows = [parse_table_row(line)]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(parse_table_row(lines[i]))
                i += 1
            flush_paragraphs()
            components.append(table_component(rows))
            continue
        if momblog:
            hm = HEADING_RE.match(line.strip())
            if hm:
                para_buffer.append(paragraph(
                    hm.group(1), align="center", bold=True, font_size=HEADING_FONT_SIZE, parse_bold=True))
                i += 1
                continue
            if DIVIDER_RE.match(line.strip()):
                flush_paragraphs()
                components.append(horizontal_line())
                i += 1
                continue
            if QUOTE_RE.match(line):
                qlines = []
                while i < n and QUOTE_RE.match(lines[i]):
                    qlines.append(QUOTE_RE.match(lines[i]).group(1))
                    i += 1
                flush_paragraphs()
                components.append(quotation_component(qlines))
                continue
        para_buffer.append(make_para(line))
        i += 1
    flush_paragraphs()
    return components or [text_component([paragraph("")])]


def build_document_model(title: str, body_text: str, image_results: list | None = None) -> str:
    """제목/본문을 네이버 SE 에디터 documentModel JSON 문자열로 변환 (실제 캡처 구조)."""
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
                *body_to_components(body_text, image_results=image_results),
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


def save_draft(session, blog_id, title, body_text, category_id, editor_source, debug=False,
               with_images=False) -> bool:
    image_results = prepare_image_results(body_text) if with_images else None
    data = {
        "blogId": blog_id,
        "documentModel": build_document_model(title, body_text, image_results=image_results),
        "mediaResources": json.dumps({"image": [], "video": [], "file": []}, separators=(",", ":")),
        "populationParams": build_population_params(
            category_id, editor_source, auto_save_no=int(time.time() * 1000)
        ),
        "productApiVersion": "v1",
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
        if "isSuccess" in j:
            ok = bool(j["isSuccess"])
        else:
            result = j.get("result")
            ok = bool(
                (isinstance(result, dict) and result.get("logNo"))
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
    ap.add_argument("--with-images", action="store_true",
                    help="사진 자동 검색·업로드 활성화 (기본: 꺼짐, placeholder 텍스트 유지)")
    args = ap.parse_args()

    if args.body_file:
        body_text = Path(args.body_file).read_text(encoding="utf-8")
    elif args.body is not None:
        body_text = args.body
    else:
        ap.error("본문을 body 인자 또는 --body-file 로 제공하세요.")

    session = load_session(find_cookies_path(args.cookies), args.blog_id, args.category)
    success = save_draft(
        session, args.blog_id, args.title, body_text, args.category, args.editor_source,
        debug=args.debug, with_images=args.with_images,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
