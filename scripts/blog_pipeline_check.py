#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이미지 포함 네이버 임시저장 전에 로컬 원고 패키지를 검사한다."""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "BLOG_PIPELINE_CONFIG.json"

LOCAL_IMAGE_RE = re.compile(
    r"^\s*📷\s*\[(생성이미지|실제사진|편집사진)\s*(\d+)\]\s*파일:\s*`([^`]+)`",
    re.MULTILINE,
)
TOUR_IMAGE_RE = re.compile(
    r"^\s*📷\s*\[사진\s*(\d+)\]\s*검색어:\s*`([^`]+)`",
    re.MULTILINE,
)
STYLE_RE = re.compile(r"<!--\s*(travel|momblog|parenting|info)\s*-->")
INTERNAL_SECTION_RE = re.compile(
    r"^##\s*(?:이미지\s*(?:생성\s*브리프|제작\s*목록)|Image Manifest)",
    re.MULTILINE | re.IGNORECASE,
)
ISLAND_IMAGE_ROLES = [
   "thumbnail",
   "comparison_overview",
   "attractions",
   "final_recommendation",
]


def _read_markdown(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("첫 줄은 '# 제목' 형식이어야 합니다.")
    return lines[0][2:].strip(), "\n".join(lines[1:]).lstrip("\n")


def _resolve_image(raw_path: str, draft_path: Path) -> Path | None:
    p = Path(raw_path).expanduser()
    if p.is_absolute():
        return p.resolve() if p.is_file() else None
    for base in (draft_path.parent, PROJECT_ROOT):
        candidate = (base / p).resolve()
        if candidate.is_file():
            return candidate
    return None


def _image_size(path: Path) -> tuple[int, int] | None:
    """PNG, JPEG, WebP의 크기를 외부 라이브러리 없이 읽는다."""
    with path.open("rb") as f:
        head = f.read(32)
        if head.startswith(b"\x89PNG\r\n\x1a\n") and len(head) >= 24:
            return struct.unpack(">II", head[16:24])

        if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
            if head[12:16] == b"VP8X" and len(head) >= 30:
                width = 1 + int.from_bytes(head[24:27], "little")
                height = 1 + int.from_bytes(head[27:30], "little")
                return width, height
            return None

        if not head.startswith(b"\xff\xd8"):
            return None
        f.seek(2)
        while True:
            marker_start = f.read(1)
            if not marker_start:
                return None
            if marker_start != b"\xff":
                continue
            marker = f.read(1)
            while marker == b"\xff":
                marker = f.read(1)
            if not marker or marker in (b"\xd8", b"\xd9"):
                continue
            length_raw = f.read(2)
            if len(length_raw) != 2:
                return None
            length = int.from_bytes(length_raw, "big")
            if marker[0] in {
                0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
            }:
                data = f.read(5)
                if len(data) != 5:
                    return None
                return int.from_bytes(data[3:5], "big"), int.from_bytes(data[1:3], "big")
            f.seek(max(length - 2, 0), 1)


def _allowed_media_path(path: Path, config: dict) -> bool:
    allowed = [
        (PROJECT_ROOT / config["paths"]["image_output_root"]).resolve(),
        (PROJECT_ROOT / config["paths"]["private_photo_root"]).resolve(),
    ]
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in allowed)


def _load_manifest(image_paths: list[Path], raw_paths: list[str]) -> tuple[Path | None, dict | None]:
    for path, raw in zip(image_paths, raw_paths):
        normalized = raw.replace("\\", "/")
        if normalized.startswith("assets/posts/"):
            manifest_path = path.parent / "manifest.json"
            if not manifest_path.is_file():
                return manifest_path, None
            return manifest_path, json.loads(manifest_path.read_text(encoding="utf-8"))
    return None, None


def validate(draft_path: Path, content_type: str, stage: str, config: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        title, body = _read_markdown(draft_path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"원고를 읽을 수 없습니다: {exc}"], warnings

    content_config = config.get("content_types", {}).get(content_type)
    if not content_config:
        return [f"지원하지 않는 콘텐츠 유형입니다: {content_type}"], warnings

    style_match = STYLE_RE.search(body)
    expected_style = content_config["style_directive"]
    if not style_match:
        errors.append(f"스타일 지시자 <!-- {expected_style} -->가 없습니다.")
    elif style_match.group(1) != expected_style:
        errors.append(
            f"스타일 지시자가 {style_match.group(1)}입니다. {expected_style}이어야 합니다."
        )

    if INTERNAL_SECTION_RE.search(body):
        errors.append("이미지 브리프·제작 목록 같은 내부 작업 섹션이 본문에 남아 있습니다.")

    local_matches = list(LOCAL_IMAGE_RE.finditer(body))
    tour_matches = list(TOUR_IMAGE_RE.finditer(body))
    image_count = len(local_matches) + len(tour_matches)
    minimum = int(content_config["minimum_images"])
    maximum = int(content_config["maximum_images"])
    if stage == "naver" and content_type == "island_compare" and image_count != minimum:
        errors.append(f"섬 비교 이미지는 정확히 {minimum}장이어야 합니다. 현재 {image_count}장입니다.")
    elif stage == "naver" and image_count < minimum:
        errors.append(f"이미지가 {image_count}장입니다. 최소 {minimum}장이 필요합니다.")
    if content_type != "island_compare" and image_count > maximum:
        warnings.append(f"이미지가 {image_count}장으로 권장 최대 {maximum}장을 넘습니다.")

    resolved_pairs: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for match in local_matches:
        kind, _, raw_path = match.groups()
        resolved = _resolve_image(raw_path, draft_path)
        if resolved is None:
            errors.append(f"이미지 파일을 찾을 수 없습니다: {raw_path}")
            continue
        resolved_pairs.append((resolved, raw_path))
        if resolved in seen:
            errors.append(f"같은 이미지 파일이 중복 사용되었습니다: {raw_path}")
        seen.add(resolved)
        if not _allowed_media_path(resolved, config):
            errors.append(f"허용된 이미지 폴더 밖의 파일입니다: {resolved}")

        size = _image_size(resolved)
        if size is None:
            warnings.append(f"이미지 크기를 확인하지 못했습니다: {raw_path}")
        else:
            width, height = size
            if width <= 0 or height <= 0:
                errors.append(f"이미지 크기가 올바르지 않습니다: {raw_path}")
            elif content_type == "island_compare" and abs(width - height) / max(width, height) > 0.01:
                errors.append(f"섬 비교 이미지는 1:1 정사각형이어야 합니다: {raw_path} ({width}×{height})")
            elif width / height < 0.8:
                errors.append(f"4:5보다 긴 세로 이미지입니다: {raw_path} ({width}×{height})")
            elif width < 1000:
                warnings.append(f"가로 해상도가 1000px 미만입니다: {raw_path} ({width}×{height})")

        if content_type == "product_review" and kind == "생성이미지":
            errors.append("제품 리뷰의 제품 외형은 실제 제품 사진 없이 생성할 수 없습니다.")

    if local_matches and stage == "naver":
        manifest_path, manifest = _load_manifest(
            [path for path, _ in resolved_pairs],
            [raw for _, raw in resolved_pairs],
        )
        if manifest_path and manifest is None:
            errors.append(f"이미지 매니페스트가 없습니다: {manifest_path}")
        elif manifest is not None:
            if content_type == "island_compare":
                manifest_images = manifest.get("images", [])
                roles = [item.get("role") for item in manifest_images]
                numbers = [item.get("number") for item in manifest_images]
                if len(manifest_images) != 4:
                    errors.append(f"섬 비교 매니페스트는 이미지 4개여야 합니다. 현재 {len(manifest_images)}개입니다.")
                if roles != ISLAND_IMAGE_ROLES:
                    errors.append("섬 비교 매니페스트의 4개 역할 또는 순서가 올바르지 않습니다.")
                if numbers != list(range(1, 5)):
                    errors.append("섬 비교 매니페스트의 이미지 번호는 1~4 순서여야 합니다.")
            entries = {
                str(item.get("file", "")).replace("\\", "/"): item
                for item in manifest.get("images", [])
            }
            for _, raw_path in resolved_pairs:
                key = raw_path.replace("\\", "/")
                item = entries.get(key)
                if not item:
                    errors.append(f"매니페스트에 이미지가 없습니다: {raw_path}")
                    continue
                if item.get("status") != "ready":
                    errors.append(f"이미지 상태가 ready가 아닙니다: {raw_path}")
                qa = item.get("qa", {})
                if not qa or not all(qa.values()):
                    errors.append(f"이미지 QA가 완료되지 않았습니다: {raw_path}")

    if content_type == "parenting_info":
        if "http://" not in body and "https://" not in body:
            errors.append("육아 정보 글에 확인 가능한 공식 출처 URL이 없습니다.")

    if not title:
        errors.append("제목이 비어 있습니다.")
    if not re.search(r"^##\s+\S+", body, re.MULTILINE):
        errors.append("본문 소제목이 없습니다.")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="블로그 원고·이미지 품질 관문")
    parser.add_argument("draft", help="검사할 Markdown 원고")
    parser.add_argument(
        "--content-type",
        required=True,
        choices=[
            "island_compare",
            "ferry_info",
            "parenting_info",
            "parenting_diary",
            "product_review",
        ],
    )
    parser.add_argument("--stage", choices=["local", "naver"], default="local")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = parser.parse_args()

    draft_path = Path(args.draft).resolve()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    errors, warnings = validate(draft_path, args.content_type, args.stage, config)

    print(f"[검사] {draft_path.name} / {args.content_type} / {args.stage}")
    for item in warnings:
        print(f"[주의] {item}")
    for item in errors:
        print(f"[실패] {item}")
    if errors:
        print(f"[결과] 실패 {len(errors)}건, 주의 {len(warnings)}건")
        return 1
    print(f"[결과] 통과, 주의 {len(warnings)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
