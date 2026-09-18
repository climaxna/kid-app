"""Read only: inspect current editor schema without exposing session data."""
import re
import json
from urllib.parse import urljoin
import naver_blog_draft as n

s = n.load_session(n.find_cookies_path(None), n.DEFAULT_BLOG_ID, 18)
listing = s.get('https://blog.naver.com/TempPostList.naver', params={'blogId':n.DEFAULT_BLOG_ID,'editorVersion':'SEOne','onlyCount':'false'}, timeout=30).json()
print('DRAFT_LIST', json.dumps(listing, ensure_ascii=False)[:12000])
r = s.get(s.headers['referer'], timeout=30)
print('HTTP', r.status_code, 'login_redirect', 'nidlogin' in r.url)
scripts = re.findall(r'<script[^>]+src=[\"\x27]([^\"\x27]+)', r.text)
for src in scripts:
    print('SCRIPT', urljoin(r.url, src))
    if 'pc-pages-SEOnePage' in src or '/489.' in src or '/238.' in src:
        js = s.get(urljoin(r.url, src), timeout=30).text
        for pattern in ('RabbitTemp', 'tags:', '.tags', 'tempPostList', 'TempPost'):
            for m in list(re.finditer(re.escape(pattern), js))[:12]:
                print('SCHEMA', pattern, js[max(0,m.start()-130):m.end()+230])
for pattern in ('RabbitTemp', 'tags', 'populationMeta'):
    for m in list(re.finditer(pattern, r.text))[:4]:
        print(pattern, r.text[max(0,m.start()-100):m.end()+150])
