#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주제 → 블로그 글 생성(Claude) → drafts/ 저장 → 네이버 임시저장까지 한 번에.

흐름:
  1. Claude(claude-opus-4-8)로 제목+본문 생성 (한국어, 네이버 블로그용)
  2. drafts/YYYYMMDD-HHMMSS-<슬러그>.md 로 저장
  3. naver_blog_draft 모듈로 네이버 임시저장 자동 실행

사용법:
  python scripts/generate_and_draft.py "완도 여객선 겨울 여행 팁"
  python scripts/generate_and_draft.py "청산도 슬로시티 당일치기" --category 18
  python scripts/generate_and_draft.py "주제" --no-naver        # 생성·저장만(임시저장 생략)
  python scripts/generate_and_draft.py "주제" --model claude-sonnet-5

필요 환경:
  - ANTHROPIC_API_KEY 환경변수 (console.anthropic.com 에서 발급)
  - cookies.json (네이버 로그인 쿠키) — 네이버 임시저장 단계에서 필요
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import anthropic

# 같은 scripts/ 폴더의 네이버 임시저장 모듈 재사용
sys.path.insert(0, str(Path(__file__).resolve().parent))
import naver_blog_draft as nbd  # noqa: E402

DEFAULT_MODEL = "claude-opus-4-8"
DRAFTS_DIR = Path(__file__).resolve().parent.parent / "drafts"

SYSTEM_PROMPT = """당신은 완도·여객선·섬 여행을 다루는 한국어 블로그 작가입니다.
독자는 배를 타고 섬으로 여행·이동하려는 일반인입니다. 다음 원칙을 지키세요.

- 자연스럽고 친근한 한국어 존댓말. 과장·클릭베이트 금지.
- 도입(왜 읽는지) → 본문(구체 정보·팁, 소제목으로 구분) → 마무리(요약·한마디) 구조.
- 실제로 도움이 되는 구체 정보 위주. 확실하지 않은 수치(정확한 시간표·요금)는
  "공식 채널에서 확인하세요"처럼 안전하게 안내하고 지어내지 마세요.
- 본문 길이는 900~1400자 내외. 소제목은 문장 앞에 '## '를 붙여 표시.
- 문단은 빈 줄로 구분."""

# 구조화 출력 스키마 (제목/본문)
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "블로그 글 제목 (한국어, 40자 이내)"},
        "body": {"type": "string", "description": "블로그 본문 (한국어, 소제목은 '## ', 문단은 빈 줄 구분)"},
    },
    "required": ["title", "body"],
    "additionalProperties": False,
}


def generate_post(topic: str, model: str) -> tuple[str, str]:
    """Claude로 제목/본문 생성. (title, body) 반환."""
    try:
        client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 자동 사용
    except Exception as e:
        sys.exit(f"[오류] Claude 클라이언트 생성 실패: {e}")

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"다음 주제로 네이버 블로그 글을 작성해 주세요: {topic}",
            }],
        )
    except anthropic.AuthenticationError:
        sys.exit("[오류] 인증 실패 — ANTHROPIC_API_KEY 를 확인하세요 (console.anthropic.com).")
    except anthropic.APIStatusError as e:
        sys.exit(f"[오류] Claude API {e.status_code}: {e.message}")
    except anthropic.APIConnectionError as e:
        sys.exit(f"[오류] Claude API 연결 실패: {e}")

    # thinking 블록을 제외한 text 블록만 이어붙여 JSON 파싱
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    if not text.strip():
        sys.exit("[오류] 모델이 빈 응답을 반환했습니다.")
    try:
        data = json.loads(text)
        title, body = data["title"].strip(), data["body"].strip()
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        sys.exit(f"[오류] 생성 결과 파싱 실패: {e}\n원문: {text[:300]}")

    if not title or not body:
        sys.exit("[오류] 제목 또는 본문이 비어 있습니다.")
    print(f"[정보] 글 생성 완료 — 제목: {title}  (본문 {len(body)}자)")
    return title, body


def slugify(text: str) -> str:
    s = re.sub(r"[^\w가-힣]+", "-", text).strip("-")
    return (s[:40] or "post").lower()


def save_draft_file(title: str, body: str) -> Path:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = DRAFTS_DIR / f"{stamp}-{slugify(title)}.md"
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    print(f"[정보] drafts 저장: {path}")
    return path


def main():
    ap = argparse.ArgumentParser(description="주제 → 글 생성 → drafts 저장 → 네이버 임시저장")
    ap.add_argument("topic", help="블로그 글 주제")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"생성 모델 (기본 {DEFAULT_MODEL})")
    ap.add_argument("--blog-id", default=nbd.DEFAULT_BLOG_ID, help=f"네이버 blogId (기본 {nbd.DEFAULT_BLOG_ID})")
    ap.add_argument("--category", type=int, default=nbd.DEFAULT_CATEGORY_ID,
                    help=f"네이버 categoryId (기본 {nbd.DEFAULT_CATEGORY_ID})")
    ap.add_argument("--editor-source", default=nbd.DEFAULT_EDITOR_SOURCE, help="네이버 editorSource 토큰")
    ap.add_argument("--cookies", help="cookies.json 경로 (기본: 자동 탐색)")
    ap.add_argument("--no-naver", action="store_true", help="네이버 임시저장 생략 (생성·저장만)")
    args = ap.parse_args()

    # 1. 생성
    title, body = generate_post(args.topic, args.model)
    # 2. drafts 저장
    save_draft_file(title, body)
    # 3. 네이버 임시저장
    if args.no_naver:
        print("[정보] --no-naver: 네이버 임시저장을 생략했습니다.")
        return
    session = nbd.load_session(nbd.find_cookies_path(args.cookies), args.blog_id, args.category)
    success = nbd.save_draft(session, args.blog_id, title, body, args.category, args.editor_source)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
