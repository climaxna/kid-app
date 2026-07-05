#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한국관광공사 관광사진 API(PhotoGalleryService1)로 키워드 검색 후 이미지를 받아와
네이버 블로그 업로드(blog.upphoto.naver.com simpleUpload)까지 처리하는 헬퍼.

사진은 공공누리 1유형(포토코리아, phoko.visitkorea.or.kr) 콘텐츠로 자유롭게
다운로드·활용 가능하다. 업로드 토큰(base64) 구조는 실제 캡처로 확인한 형식을
그대로 재현한다: "YYYYMMDDHHMMSS\\x07epochMillis\\x07blog_editor2\\x07blogId\\x070\\x072\\x07<32자hex>"
"""
import base64
import mimetypes
import secrets
import time
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


def _gen_upload_token(blog_id: str) -> str:
    now = time.time()
    ts = time.strftime("%Y%m%d%H%M%S", time.localtime(now))
    millis = str(int(now * 1000))
    nonce = secrets.token_hex(16)
    raw = "\x07".join([ts, millis, "blog_editor2", blog_id, "0", "2", nonce])
    return base64.b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def upload_image_to_naver(session: requests.Session, blog_id: str, image_bytes: bytes, filename: str) -> dict:
    """이미지를 네이버 blogfiles CDN에 업로드하고 documentModel용 정보를 반환."""
    token = _gen_upload_token(blog_id)
    content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
    upload_url = (
        f"https://blog.upphoto.naver.com/{token}/simpleUpload/0"
        f"?userId={blog_id}&extractExif=true&extractAnimatedCnt=false&extractAnimatedInfo=true"
        f"&autorotate=true&extractDominantColor=false&type=&customQuery=&denyAnimatedImage=false"
        f"&skipXcamFiltering=false"
    )
    files = {"image": (filename, image_bytes, content_type)}
    resp = session.post(upload_url, files=files, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    # <url>은 파일명 세그먼트(.../JPEG/파일명.jpg)를 포함, <path>는 미포함(.../JPEG).
    # 실제 에디터 image 컴포넌트는 파일명이 붙은 경로를 써야 렌더링되므로 <url>을 사용.
    image_path = root.findtext("url") or root.findtext("path")
    return {
        "path": image_path,
        "width": int(root.findtext("width") or 0),
        "height": int(root.findtext("height") or 0),
        "fileSize": int(root.findtext("fileSize") or 0),
        "fileName": root.findtext("fileName") or filename,
    }


def fetch_and_upload(session: requests.Session, blog_id: str, keyword: str) -> tuple[dict, dict] | None:
    """키워드로 검색해서 첫 결과를 다운로드 후 업로드. (검색결과, 업로드결과) 또는 None."""
    items = search_gallery(keyword, num_rows=3)
    if not items or not items[0]["image_url"]:
        return None
    item = items[0]
    ext = item["image_url"].rsplit(".", 1)[-1].split("?")[0] or "jpg"
    filename = f"{keyword.replace(' ', '_')[:20]}.{ext}"
    image_bytes = download_image(item["image_url"])
    upload = upload_image_to_naver(session, blog_id, image_bytes, filename)
    return item, upload
