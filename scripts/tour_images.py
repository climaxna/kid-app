#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국관광공사 관광사진 API(PhotoGalleryService1)로 키워드 검색 후 이미지를 받아와
네이버 블로그에 업로드하는 헬퍼.

사진은 공공누리 1유형(포토코리아, phoko.visitkorea.or.kr) 콘텐츠로 자유롭게
다운로드·활용 가능하다. 네이버 업로드 토큰은 에디터 JS가 서명하므로 순수 HTTP로는
위조가 불가능(SYSTEM 에러) → 실제 업로드는 브라우저(upload_images.mjs)로 수행하고,
반환된 CDN 경로를 documentModel 저장에 사용한다.
"""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
GALLERY_SEARCH_URL = "https://apis.data.go.kr/B551011/PhotoGalleryService1/gallerySearchList1"
IMAGE_DOMAIN = "https://blogfiles.pstatic.net"
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def load_datagokr_key() -> str:
    if not ENV_PATH.is_file():
        raise RuntimeError(f"{ENV_PATH} 없음 — DATAGOKR_API_KEY 설정 필요")
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("DATAGOKR_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(".env에 DATAGOKR_API_KEY 없음")


def search_gallery(keyword: str, num_rows: int = 5) -> list[dict]:
    """관광사진 키워드 검색. [{title, image_url, location, photographer}, ...] 반환."""
    key = load_datagokr_key()
    params = {
        "serviceKey": key,
        "numOfRows": str(num_rows),
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "wando-blog",
        "keyword": keyword,
    }
    url = GALLERY_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    resp = requests.get(url, headers=_UA, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for it in root.findall(".//item"):
        items.append({
            "title": it.findtext("galTitle") or "",
            "image_url": it.findtext("galWebImageUrl") or "",
            "location": it.findtext("galPhotographyLocation") or "",
            "photographer": it.findtext("galPhotographer") or "",
        })
    return items


def download_image(url: str) -> bytes:
    resp = requests.get(url, headers=_UA, timeout=20)
    resp.raise_for_status()
    return resp.content


# 장소명일 가능성이 높은 접미사(섬/포구/명소). generic 지역명은 매칭이 너무 넓어 후순위.
_PLACE_SUFFIXES = ("도", "항", "해변", "대교", "봉", "숲", "사", "원", "리", "마을", "센터", "기념관", "섬", "해안")
_GENERIC_TOKENS = {"완도", "완도군", "전남", "전라남도", "여름", "가족", "바다", "풍경", "전경", "항공뷰"}


def _search_variants(keyword: str) -> list[str]:
    """긴 검색 문구가 결과가 없을 때 시도할 축약 변형들을 우선순위대로 생성.

    예) '완도 전복체험 노화도 해녀 전복'
        → 전체 → '노화도'(장소명 토큰) → 접두 축약들 → 나머지 개별 토큰
    섬 이름(예: 노화도) 같은 장소명 토큰을 generic 지역명('완도')보다 먼저 시도해
    엉뚱한 지역 사진이 잡히는 걸 줄인다."""
    tokens = keyword.split()
    variants = [keyword]
    # 1) 장소명 후보 토큰 (generic 제외, place suffix로 끝나는 것)
    for t in tokens:
        if t not in _GENERIC_TOKENS and any(t.endswith(s) for s in _PLACE_SUFFIXES):
            variants.append(t)
    # 2) 접두 축약 (앞쪽일수록 장소명일 가능성 높음)
    for k in range(len(tokens) - 1, 0, -1):
        variants.append(" ".join(tokens[:k]))
    # 3) 나머지 개별 토큰
    variants.extend(tokens)
    seen, out = set(), []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def search_and_download(keyword: str, dest_path: str) -> dict | None:
    """키워드(긴 문구 허용)로 관광사진을 검색해 첫 결과를 dest_path에 저장.

    전체 문구가 결과가 없으면 점점 짧은 변형으로 재시도한다. 성공 시 item 메타 반환."""
    for variant in _search_variants(keyword):
        items = search_gallery(variant, num_rows=3)
        if items and items[0]["image_url"]:
            item = items[0]
            data = download_image(item["image_url"])
            with open(dest_path, "wb") as f:
                f.write(data)
            item["matched_keyword"] = variant
            return item
    return None


def upload_images_via_browser(local_paths: list[str]) -> list[dict | None]:
    """로컬 이미지들을 브라우저(Playwright)로 네이버에 업로드하고 경로 정보 리스트 반환.

    업로드 토큰이 에디터 JS 서명값이라 순수 HTTP로는 위조 불가 → upload_images.mjs로
    실제 브라우저 업로드를 수행한다. 반환 순서는 입력 순서와 동일(실패분은 None)."""
    if not local_paths:
        return []
    scripts_dir = Path(__file__).resolve().parent
    tmp = tempfile.mkdtemp(prefix="wando_upload_")
    in_json = os.path.join(tmp, "input.json")
    out_json = os.path.join(tmp, "output.json")
    with open(in_json, "w", encoding="utf-8") as f:
        json.dump(local_paths, f, ensure_ascii=False)
    node = shutil.which("node") or "node"
    subprocess.run(
        [node, str(scripts_dir / "upload_images.mjs"), in_json, out_json],
        check=True,
        cwd=str(scripts_dir.parent),
    )
    with open(out_json, encoding="utf-8") as f:
        return json.load(f)
