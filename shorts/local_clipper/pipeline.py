"""Local-only clip preparation, transcription and repeatable rendering."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import wave

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import av
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
JOBS = ROOT / 'jobs'
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = 'C:/Windows/Fonts/malgunbd.ttf'

def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def media_info(path):
    with av.open(str(path)) as c:
        v = next(iter(c.streams.video), None)
        if v is None:
            raise ValueError('영상 트랙이 없습니다.')
        duration = float(c.duration / av.time_base) if c.duration else float(v.duration * v.time_base)
        return {'duration': duration, 'width': v.width, 'height': v.height,
                'audio': bool(c.streams.audio)}

def stamp(seconds):
    minutes, seconds = divmod(float(seconds), 60)
    return f'{int(minutes):02}:{seconds:05.2f}'

def parse_time(value):
    parts = str(value).strip().split(':')
    if len(parts) > 3:
        raise ValueError('시간은 초 또는 분:초 형식입니다.')
    result = 0.0
    for p in parts:
        result = result * 60 + float(p)
    if not math.isfinite(result) or result < 0:
        raise ValueError('시간은 0 이상의 유한한 수여야 합니다.')
    return result

def run(cmd, log):
    with Path(log).open('w', encoding='utf-8') as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)
    if p.returncode:
        tail = Path(log).read_text(encoding='utf-8', errors='replace')[-2200:]
        raise RuntimeError(f'작업 실패. 로그: {log}\n{tail}')

def prepare(source, model='small', log=print):
    local = Path(source).expanduser()
    is_local = local.is_file()
    if not is_local and not re.match(r'^https://(?:www\.)?(?:youtube\.com/|youtu\.be/)', source):
        raise ValueError('YouTube HTTPS 링크 또는 로컬 영상 파일을 입력하세요.')
    identity = str(local.resolve()) + str(local.stat().st_mtime_ns) if is_local else source.split('&')[0].split('?si=')[0]
    job = JOBS / hashlib.sha256(identity.encode()).hexdigest()[:14]
    job.mkdir(parents=True, exist_ok=True)
    if (job/'source.json').exists():
        meta = read_json(job/'source.json')
        video = Path(meta['file'])
    elif is_local:
        video = local.resolve()
        meta = {'file':str(video), 'url':None, 'title':video.stem, 'uploader':'로컬 원본'}
    else:
        log('원본 다운로드 중 — 한국어 음성 우선')
        run([sys.executable,'-m','yt_dlp','--no-playlist','--no-progress','--js-runtimes','node',
             '--ffmpeg-location',FF,'-f','bv*[height<=1080]+ba[language^=ko]/b[language^=ko]/bv*[height<=1080]+ba/b',
             '--merge-output-format','mp4','--write-info-json','-o',str(job/'source.%(ext)s'),source],job/'download.log')
        info = read_json(job/'source.info.json')
        video = job/'source.mp4'
        if not video.exists():
            candidates = [p for p in job.glob('source.*') if p.suffix in ('.mkv','.webm','.mp4')]
            if len(candidates) != 1:
                raise RuntimeError('다운로드한 영상 파일을 확인할 수 없습니다.')
            video = candidates[0]
        meta = {'file':str(video.resolve()),'input':source,'url':info.get('webpage_url',source),
                'title':info.get('title',''),'uploader':info.get('uploader','')}
    meta.update(media_info(video))
    write_json(job/'source.json',meta)
    transcript_file = job/f'transcript-{model}.json'
    if transcript_file.exists():
        log('저장된 대사 재사용')
        transcript = read_json(transcript_file)
    else:
        log(f'로컬 음성인식 중 ({model}, CPU) — 처음에는 몇 분 걸릴 수 있습니다.')
        from faster_whisper import WhisperModel
        import numpy as np
        started = time.monotonic()
        wav = job/'speech-16k.wav'
        if not wav.exists():
            run([FF,'-y','-v','error','-i',str(video),'-map','0:a:0','-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(wav)],job/'audio.log')
        with wave.open(str(wav),'rb') as w:
            samples=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
        engine = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=6)
        segments, info = engine.transcribe(samples,language='ko',beam_size=5,vad_filter=True,
                                          condition_on_previous_text=False)
        transcript = []
        for s in segments:
            transcript.append({'start':round(s.start,2),'end':round(s.end,2),'text':s.text.strip()})
            log(f'대사 인식 {stamp(s.end)} / {stamp(meta["duration"])}')
        if not transcript:
            raise RuntimeError('인식된 대사가 없습니다. 원본 음성을 확인하세요.')
        write_json(transcript_file,transcript)
        write_json(job/f'transcription-{model}-stats.json',{'seconds':round(time.monotonic()-started,1),'device':'cpu','model':model})
    (job/'transcript.txt').write_text('\n'.join(f'[{stamp(s["start"])}–{stamp(s["end"])}] {s["text"]}' for s in transcript),encoding='utf-8')
    candidates = propose(transcript,meta['duration'])
    write_json(job/'candidates.json', candidates)
    brief = ['# 클립 구간 검토 요청',f'원본: {meta["title"]}',f'출처: {meta.get("url") or meta["file"]}',
             '자동 음성인식이므로 오인식 가능. 아래 후보는 키워드 기반 초안이며 재미 순위가 아님.',
             '독립적으로 이해되는 구간 1~3개와 제목 2줄, 짧은 상황 자막을 제안해 주세요.']
    for i,c in enumerate(candidates):
        brief += [f'\n## 후보 {i+1}: {stamp(c["start"])}–{stamp(c["end"])}',c['text']]
    (job/'review-brief.md').write_text('\n'.join(brief),encoding='utf-8')
    cards=''.join(f'<button data-start="{c["start"]}" data-end="{c["end"]}"><b>후보 {i+1} · {stamp(c["start"])}–{stamp(c["end"])}</b><p>{html.escape(c["text"])}</p></button>' for i,c in enumerate(candidates))
    review='''<!doctype html><meta charset="utf-8"><title>클립 후보 검토</title>
<style>body{background:#17171b;color:#eee;font:16px sans-serif;max-width:1100px;margin:30px auto}video{width:100%;max-height:60vh;background:#000}button{display:block;width:100%;padding:16px;text-align:left;margin:12px 0;background:#29292f;color:white;border:1px solid #555;border-radius:10px;cursor:pointer}button:hover{border-color:#ffe34b}p{line-height:1.6}#clock{color:#ffe34b}</style>
<h1>클립 후보 검토</h1><p>버튼을 누르면 해당 구간을 재생하고 끝에서 멈춥니다. 대사는 자동 인식 초안입니다.</p>
<video id="video" controls preload="metadata" src="SOURCE"></video><p id="clock"></p>CARDS
<script>const v=document.querySelector('video');let stop=null;document.querySelectorAll('button').forEach(b=>b.onclick=()=>{v.currentTime=Number(b.dataset.start);stop=Number(b.dataset.end);v.play()});v.ontimeupdate=()=>{document.querySelector('#clock').textContent='원본 '+v.currentTime.toFixed(2)+'초';if(stop!==null&&v.currentTime>=stop){v.pause();stop=null}};</script>'''
    (job/'review.html').write_text(review.replace('SOURCE',html.escape(video.resolve().as_uri(),quote=True)).replace('CARDS',cards),encoding='utf-8')
    log(f'준비 완료: {job}')
    return job

def propose(segments, duration, limit=6):
    """Cheap text heuristic; deliberately not presented as a humor model."""
    pool=[]
    for i,s in enumerate(segments):
        selected=[]
        for t in segments[i:]:
            if t['end']-s['start'] > 33:
                break
            selected.append(t)
            if t['end']-s['start'] >= 22:
                break
        if not selected or selected[-1]['end']-s['start'] < 12:
            continue
        text=' '.join(t['text'] for t in selected)
        score=sum(text.count(w) for w in ('왜','뭐','아니','근데','진짜','갑자기','어떻게','?'))
        pool.append({'start':max(0,round(s['start']-.25,2)),
                     'end':min(duration,round(selected[-1]['end']+.4,2)), 'text':text,'heuristic_score':score})
    picks=[]
    for c in sorted(pool,key=lambda c:c['heuristic_score'],reverse=True):
        if any(max(0,min(c['end'],p['end'])-max(c['start'],p['start'])) > .35*min(c['end']-c['start'],p['end']-p['start']) for p in picks):
            continue
        picks.append(c)
        if len(picks)>=limit: break
    return sorted(picks,key=lambda c:c['start'])

def center(draw,text,y,size,color,max_width=970):
    while size>=20:
        font=ImageFont.truetype(FONT,size)
        box=draw.textbbox((0,0),text,font=font)
        if box[2]-box[0] <= max_width: break
        size-=2
    if box[2]-box[0] > max_width:
        raise ValueError('문구가 너무 깁니다. 더 짧게 입력하세요.')
    draw.text(((1080-(box[2]-box[0]))/2,y),text,font=font,fill=color)

def validate_spec(spec):
    info=media_info(spec['source'])
    start,end=float(spec['start']),float(spec['end'])
    if not all(math.isfinite(n) for n in (start,end)) or start<0 or end<=start or end>info['duration']+.05:
        raise ValueError('시작·종료 시간이 원본 범위를 벗어납니다.')
    if end-start>90:
        raise ValueError('이 템플릿은 90초 이하 클립용입니다.')
    title=spec.get('title',[])
    if not isinstance(title,list) or len(title)!=2 or not all(isinstance(s,str) and s.strip() for s in title):
        raise ValueError('제목 두 줄을 입력하세요.')
    captions=spec.get('captions',[])
    if len(captions)>8:
        raise ValueError('상황 자막은 최대 8개입니다.')
    last=0
    for c in captions:
        a,b=float(c['start']),float(c['end'])
        if not all(math.isfinite(n) for n in (a,b)) or a<last or b<=a or b>end-start+.001:
            raise ValueError('상황 자막은 클립 기준 초이며, 겹치지 않는 순서여야 합니다.')
        last=b
    return info

def render(spec, output, log=print):
    info=validate_spec(spec)
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(json.dumps(spec,ensure_ascii=False,sort_keys=True).encode()+str(Path(spec['source']).stat().st_mtime_ns).encode()).hexdigest()[:12]
    folder=output/key
    folder.mkdir(exist_ok=True)
    target=folder/'clip.mp4'
    if target.exists() and (folder/'verified.json').exists():
        log('같은 설정의 완성본 재사용')
        return target
    write_json(folder/'edit.json',spec)
    base=Image.new('RGBA',(1080,1920),(12,12,15,255))
    d=ImageDraw.Draw(base)
    center(d,spec.get('series','하이라이트'),140,32,'#b6b6bf')
    center(d,spec['title'][0],225,80,'white')
    center(d,spec['title'][1],328,80,'#ffe34b')
    d.rounded_rectangle((474,462,606,470),radius=4,fill='#ffe34b')
    center(d,spec.get('footer',''),1660,32,'#b6b6bf')
    center(d,spec.get('credit',''),1715,27,'#777781')
    base.save(folder/'layout.png')
    length=float(spec['end'])-float(spec['start'])
    cmd=[FF,'-y','-hide_banner','-loglevel','error','-ss',str(spec['start']),'-t',str(length),'-i',spec['source'],
         '-loop','1','-i',str(folder/'layout.png')]
    captions=spec.get('captions',[])
    for i,c in enumerate(captions):
        im=Image.new('RGBA',(1080,1920))
        center(ImageDraw.Draw(im),c['text'],1440,48,'#ffe34b')
        im.save(folder/f'caption-{i}.png')
        cmd+=['-loop','1','-i',str(folder/f'caption-{i}.png')]
    graph='[0:v]split=2[sharp][blur];[blur]scale=1080:900:force_original_aspect_ratio=increase,crop=1080:900,gblur=sigma=36,eq=brightness=-0.20[bg];[sharp]scale=1080:900:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1[fg];[1:v][bg]overlay=0:520:shortest=1[b];[b][fg]overlay=(W-w)/2:520+(900-h)/2:shortest=1[v0];'
    for i,c in enumerate(captions):
        graph+=f"[v{i}][{i+2}:v]overlay=0:0:enable='gte(t,{float(c['start'])})*lt(t,{float(c['end'])})':shortest=1[v{i+1}];"
    cmd+=['-filter_complex',graph.rstrip(';'),'-map',f'[v{len(captions)}]']
    if info['audio']:
        cmd+=['-map','0:a:0','-af',f'afade=t=out:st={max(0,length-.15)}:d=0.15','-c:a','aac','-b:a','192k']
    cmd+=['-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','30','-movflags','+faststart','-t',str(length),str(folder/'rendering.mp4')]
    log('세로 영상 렌더링 중')
    run(cmd,folder/'render.log')
    run([FF,'-v','error','-xerror','-i',str(folder/'rendering.mp4'),'-f','null','-'],folder/'decode-check.log')
    result=media_info(folder/'rendering.mp4')
    if abs(result['duration']-length)>.15 or (result['width'],result['height'])!=(1080,1920) or result['audio']!=info['audio']:
        raise RuntimeError('완성본 길이·해상도·음성 검사에 실패했습니다.')
    (folder/'rendering.mp4').replace(target)
    run([FF,'-y','-v','error','-ss',str(length/2),'-i',str(target),'-frames:v','1',str(folder/'preview.jpg')],folder/'preview.log')
    write_json(folder/'verified.json',result)
    log(f'완료: {target}')
    return target

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('source');a.add_argument('--model',choices=['base','small','medium'],default='small')
    a=sub.add_parser('render');a.add_argument('spec');a.add_argument('--output',default=str(ROOT/'renders'))
    a=sub.add_parser('batch');a.add_argument('specs',nargs='+');a.add_argument('--output',default=str(ROOT/'renders'))
    args=p.parse_args()
    if args.command=='prepare': print(prepare(args.source,args.model))
    else:
        for path in ([args.spec] if args.command=='render' else args.specs):
            print(render(read_json(path),args.output))

if __name__=='__main__': main()
