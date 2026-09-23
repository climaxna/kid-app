"""Save and read back the three requested text-only Chuseok autumn island drafts."""
import hashlib
import json
import re
import time
from pathlib import Path

import naver_blog_draft as n

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted((ROOT / "drafts").glob("20260921-chuseok-autumn-island-*.md"))
RECEIPT = ROOT / "drafts/20260921-chuseok-autumn-island-save-receipts.json"


def recurse(obj, key):
    if isinstance(obj, dict):
        for k, value in obj.items():
            if k == key:
                yield value
            yield from recurse(value, key)
    elif isinstance(obj, list):
        for value in obj:
            yield from recurse(value, key)


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


def prepare(path):
    source = path.read_text(encoding="utf-8")
    first, body = source.split("\n", 1)
    title = first.removeprefix("# ").strip()
    tags = re.findall(r"(?<!\S)#([^\s#]+)", "\n".join(
        line for line in body.splitlines() if re.match(r"^#[^#\s]", line)
    ))
    assert 8 <= len(tags) <= 15, (path.name, tags)
    assert not re.search(r"[｜·|()]", title), title
    assert len(body) >= 2300, (path.name, len(body))
    assert "2026년 9월 21일" in body
    document = n.build_document_model(title, body)
    parsed = json.loads(document)
    ctypes = list(recurse(parsed, "@ctype"))
    assert "image" not in ctypes and "imageGroup" not in ctypes
    assert "image-plan" not in document and "<!--" not in document
    return source, title, body, tags, document


def write_receipts(receipts):
    RECEIPT.write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    assert len(FILES) == 3, FILES
    prepared = [(path, prepare(path)) for path in FILES]
    for path, (_, title, body, tags, _) in prepared:
        print("PASS", path.name, "chars", len(body), "tags", len(tags), "images 0", flush=True)

    receipts = json.loads(RECEIPT.read_text(encoding="utf-8")) if RECEIPT.exists() else []
    session = n.load_session(n.find_cookies_path(None), n.DEFAULT_BLOG_ID, 18)
    server_list = session.get(
        "https://blog.naver.com/TempPostList.naver",
        params={"blogId": n.DEFAULT_BLOG_ID, "editorVersion": "SEOne", "onlyCount": "false"},
        timeout=30,
    ).json()
    server_titles = {
        item.get("title"): item.get("logNo")
        for item in server_list.get("result", {}).get("tempPostList", [])
    }

    for path, (source, title, _, tags, document) in prepared:
        digest = hashlib.sha256(source.encode()).hexdigest()
        entry = next((item for item in receipts if item["file"] == path.name), None)
        if entry is None:
            assert title not in server_titles, ("Existing unrecorded draft", title, server_titles[title])
            population = json.loads(n.build_population_params(
                18, n.DEFAULT_EDITOR_SOURCE, int(time.time() * 1000)
            ))
            population["populationMeta"]["tags"] = ",".join(tags)
            entry = {
                "file": path.name,
                "title": title,
                "sha256": digest,
                "tags": tags,
                "imageCount": 0,
                "status": "submitting",
            }
            receipts.append(entry)
            write_receipts(receipts)
            response = session.post(n.WRITE_URL, data={
                "blogId": n.DEFAULT_BLOG_ID,
                "documentModel": document,
                "populationParams": json.dumps(population, ensure_ascii=False, separators=(",", ":")),
                "mediaResources": '{"image":[],"video":[],"file":[]}',
                "productApiVersion": "v1",
            }, timeout=30)
            result = response.json()
            assert response.status_code == 200 and result.get("isSuccess") is True, result
            log_no = result.get("result", {}).get("logNo")
            assert log_no, result
            entry.update(logNo=log_no, status="saved", savedAt=time.strftime("%Y-%m-%d %H:%M:%S"))
            write_receipts(receipts)
            print("SAVED", title, log_no, flush=True)
        else:
            assert entry["sha256"] == digest and entry.get("logNo"), entry

        response = session.get(
            "https://blog.naver.com/RabbitTempPostRead.naver",
            params={"blogId": n.DEFAULT_BLOG_ID, "logNo": entry["logNo"]},
            timeout=30,
        )
        payload = response.json()
        assert response.status_code == 200 and payload.get("isSuccess") is True, payload
        decoded = decode_json_strings(payload.get("result", {}))
        serialized = json.dumps(decoded, ensure_ascii=False)
        expected_values = [v for v in recurse(json.loads(document), "value") if isinstance(v, str)]
        actual_values = [v for v in recurse(decoded, "value") if isinstance(v, str)]
        read_tags = list(recurse(decoded, "tags"))
        ctypes = list(recurse(decoded, "@ctype"))
        checks = {
            "title": title in serialized,
            "body": all(value in actual_values for value in expected_values),
            "tags": ",".join(tags) in read_tags or tags in read_tags,
            "images0": "image" not in ctypes and "imageGroup" not in ctypes,
        }
        assert all(checks.values()), (title, checks, read_tags)
        entry.update(status="verified", nativeTagsVerified=True, bodyVerified=True, imageCountVerified=0)
        write_receipts(receipts)
        print("VERIFIED", title, checks, flush=True)

    print("COMPLETE", sum(item["status"] == "verified" for item in receipts), flush=True)


if __name__ == "__main__":
    main()
