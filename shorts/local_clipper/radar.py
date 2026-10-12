"""Bounded public Shorts search; snapshots are samples, never platform totals."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from yt_dlp import YoutubeDL
import pipeline as p

ROOT=p.ROOT/'radar'
QUERIES=['예능 레전드','드라마 명장면','한국 영화 명장면','무한도전','거침없이 하이킥','순풍산부인과']
FIELDS=['id','title','channel','channel_id','duration','view_count','upload_date','webpage_url']

def scan(day):
    datetime.strptime(day,'%Y-%m-%d')
    run=ROOT/day;run.mkdir(parents=True,exist_ok=True)
    if (run/'snapshot.json').exists() and p.read_json(run/'snapshot.json').get('method')=='youtube-relevance-short-candidates-v2':
        print('오늘 조사 재사용:',run/'snapshot.json');return
    entries={};queries=[]
    for query in QUERIES:
        # Shorts-specific search parsing returned no entries despite visible results.
        # Use supported relevance search; inspect dates rather than assuming recency.
        url='ytsearch12:'+query+' shorts'
        print('짧은 영상 후보 검색:',query,flush=True)
        try:
            with YoutubeDL({'quiet':True,'no_warnings':True,'extract_flat':True,'playlistend':12,'socket_timeout':20}) as y:
                result=y.extract_info(url,download=False)
            rows=list(result.get('entries',[]))[:12]
            queries.append({'query':query,'url':url,'count':len(rows),'ok':bool(rows)})
            for e in rows:
                if not e or not e.get('id'):continue
                if not e.get('duration') or e['duration']>180:continue
                if e['id'] not in entries:
                    entries[e['id']]={k:e.get(k) for k in FIELDS}
                    entries[e['id']]['queries']=[]
                entries[e['id']]['queries'].append(query)
        except Exception as e:queries.append({'query':query,'url':url,'ok':False,'error':str(e)[:400]})
    shortlist=[]
    for query in QUERIES:
        options=[e for e in entries.values() if query in e['queries'] and e not in shortlist]
        shortlist.extend(sorted(options,key=lambda e:e.get('view_count') or 0,reverse=True)[:1])
    shortlist+=sorted([e for e in entries.values() if e not in shortlist],key=lambda e:e.get('view_count') or 0,reverse=True)[:max(0,8-len(shortlist))]
    for e in shortlist:
        print('상위 후보 날짜 확인:',e['id'],flush=True)
        try:
            with YoutubeDL({'quiet':True,'no_warnings':True,'skip_download':True,'socket_timeout':20,'js_runtimes':{'node':{}}}) as y:
                full=y.extract_info('https://www.youtube.com/watch?v='+e['id'],download=False)
            e.update({k:full.get(k) for k in FIELDS})
            e['date_verified']=True
            e['shorts_status']='vertical_short_candidate' if (full.get('aspect_ratio') or 99)<=1 else 'unconfirmed'
            date=full.get('upload_date')
            e['age_days']=(datetime.strptime(day,'%Y-%m-%d')-datetime.strptime(date,'%Y%m%d')).days if date else None
            e['uploaded_last_7_days']=e['age_days'] is not None and 0<=e['age_days']<7
            e['description_excerpt']=full.get('description','')[:1400]
        except Exception as ex:e['detail_error']=str(ex)[:250]
    snapshot={'observed_date_kst':day,'method':'youtube-relevance-short-candidates-v2',
              'queries':queries,'videos':list(entries.values()),'shortlist_ids':[e['id'] for e in shortlist],
              'interpretation':'일반 관련성 검색에서 180초 이하 후보를 수집한 표본. Shorts 확정이나 최근 업로드를 뜻하지 않음. 전용 Shorts 필터 파싱 실패로 대체함. 전체 업로드 수가 아니며 조회수 누계와 증가량을 구별할 것.'}
    previous=[]
    for path in ROOT.glob('*/snapshot.json'):
        data=p.read_json(path)
        if data['observed_date_kst']<day and data['method']==snapshot['method'] and [q['query'] for q in data['queries']]==QUERIES and all(q['ok'] for q in data['queries']):previous.append(data)
    baseline=max(previous,key=lambda x:x['observed_date_kst']) if previous else None
    snapshot['comparison_date']=baseline['observed_date_kst'] if baseline else None
    old={e['id']:e for e in baseline['videos']} if baseline else {}
    for e in snapshot['videos']:
        e['newly_observed']=e['id'] not in old if baseline else None
        a,b=e.get('view_count'),old.get(e['id'],{}).get('view_count')
        e['view_delta']=a-b if isinstance(a,int) and isinstance(b,int) and a>=b else None
    p.write_json(run/'snapshot.json',snapshot)
    lines=[f'# 쇼츠 조사 {day}',snapshot['interpretation'],
           f'비교 기준: {snapshot["comparison_date"] or "없음 — 첫 관측, 급증 판정 불가"}',
           f'검색 표본 {len(entries)}개. 자세한 확인 {len(shortlist)}개.']
    for e in shortlist:
        lines += [f'\n## {e["title"]}',f'https://www.youtube.com/shorts/{e["id"]}',
                  f'채널: {e["channel"]} / 업로드: {e.get("upload_date") or "미확인"} / 조회수: {e.get("view_count")}',
                  f'검색어: {", ".join(e["queries"])}',e.get('description_excerpt','')]
    (run/'brief.md').write_text('\n'.join(lines),encoding='utf-8')
    print(run/'brief.md')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--date',required=True,help='사용자 기준 한국 날짜 YYYY-MM-DD')
    scan(parser.parse_args().date)
