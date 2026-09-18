"""Save only the explicitly requested 15 text-only drafts, with native tags and receipts.

Never publishes. A recorded success is never submitted again. Uncertain writes stop.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
import naver_blog_draft as n
from blog_pipeline_check import validate

ROOT = Path(__file__).resolve().parent.parent
RECEIPT = ROOT / 'drafts/20260915-traffic-save-receipts.json'
FILES = [ROOT / 'drafts/20260914-incheon-coastal-terminal-parking-boarding.md'] + sorted((ROOT / 'drafts').glob('20260915-traffic-[0-9][0-9]-*.md'))

def prepare(path):
    source = path.read_text(encoding='utf-8')
    title, body = source.split('\n', 1)
    title = title.removeprefix('# ').strip()
    tags = re.findall(r'(?<!\S)#([^\s#]+)', '\n'.join(line for line in body.splitlines() if re.match(r'^#[^#\s]', line)))
    assert 8 <= len(tags) <= 15, (path.name, tags)
    assert not re.search(r'[｜·|()]', title), title
    assert len(body) > 1700, path.name
    errors, warnings = validate(path, 'ferry_info', 'local', json.loads((ROOT/'BLOG_PIPELINE_CONFIG.json').read_text(encoding='utf-8')))
    assert not errors, errors
    public_body = re.sub(r'<!--(?!\s*(?:info|travel|momblog|parenting|experience)\s*-->).*?-->', '', body, flags=re.S)
    document = n.build_document_model(title, public_body)
    obj = json.loads(document)
    assert not any(c.get('@ctype') in ('image','imageGroup') for c in obj['document']['components'])
    assert '<!--' not in document and '이미지 추후' not in document
    return title, body, tags, document, hashlib.sha256(source.encode()).hexdigest()

def persist(data):
    RECEIPT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--limit', type=int, default=15)
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    assert len(FILES) == 15, len(FILES)
    prepared = [(p, prepare(p)) for p in FILES]
    for p, (title, body, tags, doc, digest) in prepared:
        print('PASS', p.name, 'chars', len(body), 'tags', len(tags), 'images 0', flush=True)
    if not args.save and not args.verify:
        return
    receipts = json.loads(RECEIPT.read_text(encoding='utf-8')) if RECEIPT.exists() else []
    session = n.load_session(n.find_cookies_path(None), n.DEFAULT_BLOG_ID, 18)
    saved_count = 0
    for p, (title, body, tags, document, digest) in prepared:
        prior = next((v for v in receipts if v['file'] == p.name), None)
        if prior:
            assert prior.get('logNo'), 'Uncertain earlier write; inspect server before proceeding'
            assert prior['sha256'] == digest, 'Saved manuscript changed; do not create duplicate'
        elif args.save and saved_count < args.limit:
            population = json.loads(n.build_population_params(18, n.DEFAULT_EDITOR_SOURCE, int(time.time()*1000)))
            population['populationMeta']['tags'] = ','.join(tags)
            entry = {'file': p.name, 'title': title, 'sha256': digest, 'tags': tags, 'imageCount': 0, 'status': 'submitting'}
            receipts.append(entry)
            persist(receipts)
            response = session.post(n.WRITE_URL, data={
                'blogId': n.DEFAULT_BLOG_ID,
                'documentModel': document,
                'populationParams': json.dumps(population, ensure_ascii=False, separators=(',',':')),
                'mediaResources': '{"image":[],"video":[],"file":[]}',
                'productApiVersion': 'v1',
            }, timeout=30)
            result = response.json()
            assert response.status_code == 200 and result.get('isSuccess') is True, (response.status_code, result)
            log_no = result.get('result', {}).get('logNo')
            assert log_no, result
            entry.update(logNo=log_no, status='saved', savedAt=time.strftime('%Y-%m-%d %H:%M:%S'))
            persist(receipts)
            prior = entry
            saved_count += 1
            print('SAVED', title, log_no, flush=True)
        if prior and args.verify:
            r = session.get('https://blog.naver.com/RabbitTempPostRead.naver', params={'blogId':n.DEFAULT_BLOG_ID,'logNo':prior['logNo']}, timeout=30)
            data = r.json()
            assert r.status_code == 200 and data.get('isSuccess') is True, (r.status_code, data)
            result = data.get('result', {})
            # Retain only task-related document data if schema inspection is needed.
            def values(obj, key):
                if isinstance(obj, dict):
                    for k,v in obj.items():
                        if k == key: yield v
                        yield from values(v, key)
                elif isinstance(obj, list):
                    for v in obj: yield from values(v,key)
            def decode(obj):
                if isinstance(obj,str) and obj[:1] in ('{','['):
                    try: return decode(json.loads(obj))
                    except ValueError: return obj
                if isinstance(obj,dict): return {k:decode(v) for k,v in obj.items()}
                if isinstance(obj,list): return [decode(v) for v in obj]
                return obj
            decoded = decode(result)
            read_tags = list(values(decoded, 'tags'))
            ctypes = list(values(decoded, '@ctype'))
            serialized = json.dumps(decoded, ensure_ascii=False)
            title_ok = title in serialized
            tags_ok = ','.join(tags) in read_tags or tags in read_tags
            no_images = 'image' not in ctypes and 'imageGroup' not in ctypes
            # Compare all rendered paragraph text, not just a successful HTTP response.
            expected_text = [v for v in values(json.loads(document), 'value') if isinstance(v, str)]
            actual_text = [v for v in values(decoded, 'value') if isinstance(v, str)]
            body_ok = bool(expected_text) and all(v in actual_text for v in expected_text)
            print('READBACK', title, 'keys', list(result), 'title',title_ok,'tags',tags_ok,'body',body_ok,'images0',no_images, flush=True)
            if not (title_ok and tags_ok and body_ok and no_images):
                print('TAG_SCHEMA', read_tags, flush=True)
                print('MISSING_VALUES', [v for v in expected_text if v not in actual_text], flush=True)
                raise AssertionError('Readback verification failed; no duplicate write attempted')
            prior.update(status='verified', nativeTagsVerified=True, bodyVerified=True, imageCountVerified=0)
            persist(receipts)
    print('COMPLETE verified', sum(v['status']=='verified' for v in receipts), 'saved', len(receipts), flush=True)

if __name__ == '__main__':
    main()
