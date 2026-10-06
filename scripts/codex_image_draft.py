"""원고와 이미지 계획(JSON)으로 Codex 이미지를 만들고, 이미지를 넣어 네이버에 임시저장한다.

사용: python -X utf8 scripts/codex_image_draft.py parenting/<slug>-2026.md
계획 파일 기본값: 원고와 같은 폴더의 <원고이름>.images.json (형식은 design/IMAGE_RULES.md)
결과: <원고이름>.receipt.json, logs/auto_image_drafts.log 한 줄
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
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
JOB_ROOT = Path(tempfile.gettempdir()) / "codex_image_jobs"
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
    for raw in [plan["reference"], *plan.get("host_references", []), *plan.get("thumbnail_references", [])]:
        if not (ROOT / raw).is_file():
            raise ValueError(f"레퍼런스 이미지 없음: {raw}")
    return plan


def is_image(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


CODEX_PROMPT = """이 폴더에서 블로그 이미지를 만든다. 사용자가 미리 승인한 자동 작업이므로 확인을 기다리지 않는다.

1. IMAGE_RULES.md 규칙을 읽는다. 이 폴더에서는 계획의 file 값이 이 폴더 안의 파일 이름이다.
2. plan.json과 manuscript.md(내용 참고용)를 읽는다.
3. plan.json의 images를 순서대로 하나씩 내장 이미지 생성 도구로 만든다. 각 항목의 prompt와 text를 정확히 따른다.
   첨부한 이미지(reference 파일)는 컨셉 레퍼런스다. 분위기, 색, 질감만 참고하고 베끼지 않는다.
   thumb-로 시작하는 첨부 이미지는 썸네일 항목(insert가 top) 전용 융합 레퍼런스다. 두 장의 특징(평면 벡터 랜드마크 콜라주의 색과 도형, 실제 사진 위에 평면 일러스트 인물과 곡선 리본을 얹는 합성 구도)을 섞어 새 장면을 만들되 그림이나 건물, 글자, 로고를 베끼지 않는다. 본문 항목에는 쓰지 않는다.
   host-로 시작하는 첨부 이미지는 진행자 얼굴 기준이다. 항목 prompt에 진행자가 나오면 이 얼굴(얼굴형, 눈, 코, 입, 헤어 느낌)을 유지하고, 옷과 포즈와 배경은 그 이미지 컨셉에 맞게 새로 그린다. 진행자가 없는 항목에는 사람 얼굴을 넣지 않는다.
4. 생성된 PNG를 이 폴더에 각 항목의 file 이름으로 복사해 저장한다. 다른 파일은 만들거나 고치지 않는다.
5. 파이썬 이미지 라이브러리, 외부 API, API 키를 쓰지 않는다. 내장 이미지 생성 도구와 파일 복사만 쓴다.
6. 한 장이 실패하면 한 번만 다시 시도하고, 그래도 안 되면 건너뛴다.
7. 마지막 답은 JSON 한 줄로 한다: {"saved": [파일 이름들], "failed": [파일 이름들]}
"""


def prepare_job(md_path: Path, plan: dict, todo: list[dict]) -> Path:
    """Codex는 블로그 폴더 전체에서 샌드박스 초기화에 실패하므로 작은 작업 폴더에서 돌린다."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job = JOB_ROOT / f"{md_path.stem}-{stamp}"
    job.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / RULES, job / "IMAGE_RULES.md")
    shutil.copy2(md_path, job / "manuscript.md")
    reference = ROOT / plan["reference"]
    shutil.copy2(reference, job / f"reference{reference.suffix}")
    hosts = []
    for i, raw in enumerate(plan.get("host_references", []), 1):
        src = ROOT / raw
        name = f"host-{i}{src.suffix}"
        shutil.copy2(src, job / name)
        hosts.append(name)
    thumbs = []
    for i, raw in enumerate(plan.get("thumbnail_references", []), 1):
        src = ROOT / raw
        name = f"thumb-{i}{src.suffix}"
        shutil.copy2(src, job / name)
        thumbs.append(name)
    local_plan = {
        "concept": plan.get("concept"),
        "thumbnail_references": thumbs,
        "reference": f"reference{reference.suffix}",
        "host_references": hosts,
        "images": [{**item, "file": Path(item["file"]).name} for item in todo],
    }
    (job / "plan.json").write_text(json.dumps(local_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return job


def run_codex(job: Path, reference_names: list[str], count: int) -> tuple[int, float, str]:
    CODEX_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = CODEX_LOG_DIR / f"{job.name}.log"
    env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
    cmd = [
        str(find_codex()), "exec",
        "--skip-git-repo-check",
        "--sandbox", "workspace-write",
        "-C", str(job),
        "-o", str(job / "last.txt"),
        "-i", *[str(job / name) for name in reference_names],
    ]
    timeout = min(600 + 300 * count, 3600)
    start = time.time()
    with open(log_path, "a", encoding="utf-8") as log:
        try:
            proc = subprocess.run(
                cmd, input=CODEX_PROMPT, text=True, encoding="utf-8",
                stdout=log, stderr=subprocess.STDOUT, env=env, cwd=str(job), timeout=timeout,
            )
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = -1
            log.write(f"\n[timeout] {timeout}s\n")
    return code, round(time.time() - start), rel(log_path)


def collect(job: Path, todo: list[dict]) -> int:
    moved = 0
    for item in todo:
        src = job / Path(item["file"]).name
        if is_image(src):
            dest = ROOT / item["file"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            moved += 1
    return moved


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
        job = prepare_job(md_path, plan, todo)
        local_plan = json.loads((job / "plan.json").read_text(encoding="utf-8"))
        reference_names = [local_plan["reference"], *local_plan["thumbnail_references"], *local_plan["host_references"]]
        code, seconds, codex_log = run_codex(job, reference_names, len(todo))
        moved = collect(job, todo)
        if moved == 0:
            code, more, codex_log = run_codex(job, reference_names, len(todo))
            seconds += more
            moved = collect(job, todo)
        receipt.update(codex_exit=code, codex_seconds=seconds, codex_log=codex_log, codex_job=str(job))

    ready = [it for it in images if is_image(ROOT / it["file"])]
    receipt["images_ready"] = len(ready)
    receipt["missing"] = [it["file"] for it in images if it not in ready]

    body = "\n".join(insert_image_lines(body_lines, ready)).lstrip("\n")
    if args.no_save:
        receipt["status"] = "images_only"
    else:
        has_local = any(n.LOCAL_IMAGE_PLACEHOLDER_RE.match(line) for line in body.split("\n"))
        receipt.update(save_to_naver(title, body, hashtags(body_lines), args.category, has_local))
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
