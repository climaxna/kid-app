"""원고와 이미지 계획(JSON)으로 Codex 이미지를 만들고, 이미지를 넣어 네이버에 임시저장한다.

사용: python -X utf8 scripts/codex_image_draft.py parenting/<slug>-2026.md
계획 파일 기본값: 원고와 같은 폴더의 <원고이름>.images.json (형식은 design/IMAGE_RULES.md)
결과: <원고이름>.receipt.json, logs/auto_image_drafts.log 한 줄
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

import naver_blog_draft as n

ROOT = Path(__file__).resolve().parent.parent
RULES = "design/IMAGE_RULES.md"
LOG = ROOT / "logs" / "auto_image_drafts.log"
CODEX_LOG_DIR = ROOT / "logs" / "codex"
TEMP_LIST_URL = "https://blog.naver.com/TempPostList.naver"
TEMP_READ_URL = "https://blog.naver.com/RabbitTempPostRead.naver"
SECRET_ENV = ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def find_codex() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "OpenAI" / "Codex" / "bin"
    found = sorted(base.glob("*/codex.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not found:
        raise RuntimeError(f"codex.exe를 찾지 못했습니다: {base}")
    return found[0]


def load_plan(plan_path: Path, body_lines: list[str]) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    stripped = {line.strip() for line in body_lines}
    for item in plan["images"]:
        item["file"] = item["file"].replace("\\", "/")
        if not (item["file"].startswith("assets/posts/") and item["file"].endswith(".png")):
            raise ValueError(f"이미지 경로는 assets/posts/...png 이어야 합니다: {item['file']}")
        insert = item.get("insert", "top").strip()
        if insert != "top" and insert not in stripped:
            raise ValueError(f"원고에 없는 삽입 위치: {insert}")
        item["insert"] = insert
    if not (ROOT / plan["reference"]).is_file():
        raise ValueError(f"레퍼런스 이미지 없음: {plan['reference']}")
    return plan


def is_image(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def codex_prompt(md_path: Path, plan_path: Path, todo: list[dict]) -> str:
    files = "\n".join(f"   - {item['file']}" for item in todo)
    return f"""이 실행은 사용자가 승인한 블로그 자동 이미지 단계다. 원고는 이미 승인됐다.
AGENTS.md의 '원고 확인 전 이미지 생성 금지'와 '이미지 검수 뒤 임시저장' 단계는 이번 실행에 적용하지 않는다.
네이버 임시저장은 하지 않는다. 저장은 실행한 스크립트가 맡는다.

1. {RULES} 규칙을 읽는다.
2. 이미지 계획 {rel(plan_path)} 과 원고 {rel(md_path)} 를 읽는다.
3. 아래 파일을 계획 순서대로 하나씩 내장 이미지 생성 도구로 만든다. 각 항목의 prompt와 text를 정확히 따른다.
   첨부한 이미지는 컨셉 레퍼런스다. 분위기, 색, 질감만 참고하고 베끼지 않는다.
{files}
4. 생성된 PNG를 각 경로에 복사해 저장한다. 폴더가 없으면 만든다. 다른 파일은 만들거나 고치지 않는다.
5. 파이썬 이미지 라이브러리, 외부 API, API 키를 쓰지 않는다. 내장 이미지 생성 도구와 파일 복사만 쓴다.
6. 한 장이 실패하면 한 번만 다시 시도하고, 그래도 안 되면 건너뛴다.
7. 마지막 답은 JSON 한 줄로 한다: {{"saved": [경로들], "failed": [경로들]}}
"""


def run_codex(prompt: str, reference: Path, stem: str, count: int) -> tuple[int, float, str]:
    CODEX_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = CODEX_LOG_DIR / f"{stem}-{stamp}.log"
    last_path = CODEX_LOG_DIR / f"{stem}-{stamp}.last.txt"
    env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
    cmd = [
        str(find_codex()), "exec",
        "--sandbox", "workspace-write",
        "-C", str(ROOT),
        "-o", str(last_path),
        "-i", str(reference),
    ]
    timeout = min(600 + 300 * count, 3600)
    start = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        try:
            proc = subprocess.run(
                cmd, input=prompt, text=True, encoding="utf-8",
                stdout=log, stderr=subprocess.STDOUT, env=env, cwd=str(ROOT), timeout=timeout,
            )
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = -1
            log.write(f"\n[timeout] {timeout}s\n")
    return code, round(time.time() - start), rel(log_path)


def insert_image_lines(lines: list[str], images: list[dict]) -> list[str]:
    """제목 줄을 뺀 본문 줄에 생성이미지 표시 줄을 넣는다."""
    top = [item for item in images if item["insert"] == "top"]
    by_heading: dict[str, list[dict]] = {}
    for item in images:
        if item["insert"] != "top":
            by_heading.setdefault(item["insert"], []).append(item)

    out: list[str] = []
    pending_top = list(top)
    counter = 0

    def emit(items):
        nonlocal counter
        for item in items:
            counter += 1
            out.append(f"📷 [생성이미지 {counter}] 파일: `{item['file']}`")
            out.append("")

    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start < len(lines) and n.DIRECTIVE_RE.match(lines[start].strip()):
        out.extend(lines[: start + 1])
        start += 1
    else:
        out.extend(lines[:start])
    emit(pending_top)
    for line in lines[start:]:
        out.append(line)
        items = by_heading.pop(line.strip(), None)
        if items:
            emit(items)
    return out


def hashtags(body_lines: list[str]) -> list[str]:
    tags = []
    for line in body_lines:
        if line.startswith("#") and not line.startswith("# ") and not line.startswith("##"):
            tags.extend(t for t in line.split() if t.startswith("#") and len(t) > 1)
    seen, result = set(), []
    for t in tags:
        name = t[1:]
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result[:30]


def recurse(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            yield from recurse(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from recurse(v, key)


def decode_json_strings(obj):
    if isinstance(obj, str) and obj[:1] in ("{", "["):
        try:
            return decode_json_strings(json.loads(obj))
        except ValueError:
            return obj
    if isinstance(obj, dict):
        return {k: decode_json_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decode_json_strings(v) for v in obj]
    return obj


def save_to_naver(title: str, body: str, tags: list[str], category: int, with_images: bool) -> dict:
    session = n.load_session(n.find_cookies_path(None), n.DEFAULT_BLOG_ID, category)
    check = session.get(TEMP_LIST_URL, params={
        "blogId": n.DEFAULT_BLOG_ID, "editorVersion": "SEOne", "onlyCount": "true",
    }, timeout=30).json()
    if not check.get("isSuccess"):
        return {"status": "cookie_expired"}

    image_results = n.prepare_image_results(body, image_base_dir=ROOT) if with_images else None
    uploaded = sum(1 for r in (image_results or []) if r)
    document = n.build_document_model(title, body, image_results=image_results)
    population = json.loads(n.build_population_params(category, n.DEFAULT_EDITOR_SOURCE, int(time.time() * 1000)))
    population["populationMeta"]["tags"] = ",".join(tags)
    resp = session.post(n.WRITE_URL, data={
        "blogId": n.DEFAULT_BLOG_ID,
        "documentModel": document,
        "populationParams": json.dumps(population, ensure_ascii=False, separators=(",", ":")),
        "mediaResources": '{"image":[],"video":[],"file":[]}',
        "productApiVersion": "v1",
    }, timeout=60)
    result = resp.json()
    log_no = (result.get("result") or {}).get("logNo")
    if resp.status_code != 200 or not result.get("isSuccess") or not log_no:
        return {"status": "save_failed", "response": json.dumps(result, ensure_ascii=False)[:300]}

    read = session.get(TEMP_READ_URL, params={"blogId": n.DEFAULT_BLOG_ID, "logNo": log_no}, timeout=30).json()
    decoded = decode_json_strings(read.get("result", {}))
    ctypes = list(recurse(decoded, "@ctype"))
    return {
        "status": "saved",
        "logNo": log_no,
        "images_uploaded": uploaded,
        "images_in_draft": ctypes.count("image"),
        "title_verified": title in json.dumps(decoded, ensure_ascii=False),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--plan")
    ap.add_argument("--category", type=int, default=n.DEFAULT_CATEGORY_ID)
    ap.add_argument("--no-save", action="store_true", help="이미지만 만들고 임시저장은 하지 않음")
    ap.add_argument("--force", action="store_true", help="이미 있는 이미지도 다시 생성")
    args = ap.parse_args()

    md_path = (ROOT / args.markdown).resolve() if not Path(args.markdown).is_absolute() else Path(args.markdown)
    plan_path = Path(args.plan).resolve() if args.plan else md_path.with_suffix(".images.json")
    receipt_path = md_path.with_suffix(".receipt.json")
    lines = md_path.read_text(encoding="utf-8").split("\n")
    title, body_lines = lines[0][2:].strip(), lines[1:]
    plan = load_plan(plan_path, body_lines)
    images = plan["images"]

    receipt = {
        "manuscript": rel(md_path), "plan": rel(plan_path), "title": title,
        "started": datetime.now().isoformat(timespec="seconds"), "images_planned": len(images),
    }
    todo = [it for it in images if args.force or not is_image(ROOT / it["file"])]
    if todo:
        prompt = codex_prompt(md_path, plan_path, todo)
        code, seconds, codex_log = run_codex(prompt, ROOT / plan["reference"], md_path.stem, len(todo))
        receipt.update(codex_exit=code, codex_seconds=seconds, codex_log=codex_log)

    ready = [it for it in images if is_image(ROOT / it["file"])]
    receipt["images_ready"] = len(ready)
    receipt["missing"] = [it["file"] for it in images if it not in ready]

    body = "\n".join(insert_image_lines(body_lines, ready)).lstrip("\n")
    if args.no_save:
        receipt["status"] = "images_only"
    else:
        receipt.update(save_to_naver(title, body, hashtags(body_lines), args.category, bool(ready)))
        if receipt["status"] == "saved" and receipt["missing"]:
            receipt["status"] = "saved_partial" if ready else "saved_text_only"

    receipt["finished"] = datetime.now().isoformat(timespec="seconds")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(
            f"{receipt['finished']} | {receipt['status']} | logNo {receipt.get('logNo', '-')} | "
            f"이미지 {receipt['images_ready']}/{receipt['images_planned']} | {title}\n"
        )
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] in ("saved", "saved_partial", "images_only") else 1


if __name__ == "__main__":
    sys.exit(main())
