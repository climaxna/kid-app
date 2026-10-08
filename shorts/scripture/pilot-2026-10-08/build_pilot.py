from pathlib import Path
import asyncio, json, math, re, subprocess
import numpy as np
import soundfile as sf
import edge_tts
import imageio_ffmpeg
from scipy.signal import resample_poly
from PIL import ImageFont

ROOT = Path(__file__).parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
FPS = 30
FONT_PATH = 'C:/Windows/Fonts/malgunbd.ttf'
EPISODES = json.loads((ROOT/'episodes.json').read_text(encoding='utf-8'))
VOICE = 'ko-KR-SunHiNeural'
OUTPUT = ROOT/'ready-to-upload'
OUTPUT.mkdir(exist_ok=True)
WORK = ROOT/'work'
WORK.mkdir(exist_ok=True)

def run(args, log=None):
    result = subprocess.run([FF,'-hide_banner','-y',*args],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=ROOT)
    if log:
        log.write_text(result.stderr,encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result

def stamp(t):
    ticks = round(t*100)
    return f'{ticks//360000}:{ticks//6000%60:02}:{ticks//100%60:02}.{ticks%100:02}'

def srt_stamp(t):
    n = round(t*1000)
    return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'

async def synthesize():
    semaphore = asyncio.Semaphore(2)
    async def one(ep, i, seg):
        path = WORK/f'{ep["id"]}-{i:02}.mp3'
        if path.exists() and path.stat().st_size>1000:
            return
        async with semaphore:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(seg['text'],VOICE,rate='-12%',pitch='-2Hz').save(str(path))
                    print(f'Voice {ep["id"]} {i+1} done',flush=True)
                    return
                except Exception:
                    if attempt==2:
                        raise
                    await asyncio.sleep(1)
    tasks=[]
    for ep in EPISODES:
        last=ep['segments'][-1]
        if last['text'].endswith(' 아멘.'):
            last['text']=last['text'][:-4]
            ep['segments'].append({'kind':'prayer','text':'아멘.','display':'아멘'})
        # Exact verse wording across pages, with only punctuation and whitespace normalized.
        verse=' '.join(s['text'] for s in ep['segments'] if s['kind']=='verse')
        normal=lambda x:re.sub(r'[\s.,!?]','',x)
        assert normal(verse)==normal(ep['verse_exact'])
        for i,seg in enumerate(ep['segments']):
            tasks.append(one(ep,i,seg))
    await asyncio.gather(*tasks)

HEADER='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Malgun Gothic,80,&H001E292B,&H001E292B,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Title,Malgun Gothic,76,&H001E292B,&H001E292B,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Label,Malgun Gothic,36,&H003C594C,&H003C594C,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Source,Malgun Gothic,30,&H00455155,&H00455155,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''

def render_episode(ep):
    eid=ep['id']
    items=[]
    cursor=0.25
    voice_parts=[]
    for i,seg in enumerate(ep['segments']):
        a,rate=sf.read(WORK/f'{eid}-{i:02}.mp3',always_2d=True)
        a=a.mean(axis=1)
        if rate!=SR:
            a=resample_poly(a,SR,rate)
        # Remove codec silence only; retain a short natural lead and tail.
        active=np.flatnonzero(np.abs(a)>0.002)
        if len(active):
            a=a[max(0,active[0]-int(.065*SR)):min(len(a),active[-1]+int(.15*SR))]
        length=len(a)/SR
        hold=max(length+0.55,2.25)
        items.append({**seg,'start':cursor,'voice_end':cursor+length,'end':cursor+hold})
        voice_parts.append((cursor,a))
        cursor+=hold
    duration=math.ceil((cursor+2.8)*FPS)/FPS
    voice=np.zeros(round(duration*SR))
    for start,a in voice_parts:
        start=round(start*SR)
        voice[start:start+len(a)]+=a
    # Consistent voice level; music remains approximately 20 dB quieter while speaking.
    active=voice[np.abs(voice)>.01]
    gain=min(10**(-19/20)/np.sqrt(np.mean(active**2)),0.80/np.max(np.abs(voice)))
    voice*=gain
    music,rate=sf.read(ROOT.parent/'audio/piano_prayer_30s_v2.wav',always_2d=True)
    # Stretch the existing original piano arrangement gently to match narration.
    tempo=30/duration
    music_path=WORK/f'{eid}-music.wav'
    run(['-loglevel','error','-i',str(ROOT.parent/'audio/piano_prayer_30s_v2.wav'),'-af',f'atempo={tempo:.6f}', '-ar',str(SR),str(music_path)])
    music,rate=sf.read(music_path,always_2d=True)
    music=np.pad(music,((0,max(0,len(voice)-len(music))),(0,0)))[:len(voice)]
    envelope=np.ones(len(voice))*0.18
    for item in items:
        a=max(0,round((item['start']-.12)*SR)); b=min(len(voice),round((item['voice_end']+.25)*SR))
        envelope[a:b]=.095
    # Smooth ducking with a 120 ms window.
    from scipy.ndimage import uniform_filter1d
    envelope=uniform_filter1d(envelope,size=int(SR*.12))
    music*=envelope[:,None]
    fade=np.clip((duration-np.arange(len(voice))/SR)/1.8,0,1)
    combined=(voice[:,None]+music)*fade[:,None]
    assert np.isfinite(combined).all() and np.max(np.abs(combined))<0.99
    audio=WORK/f'{eid}-mix.wav'
    sf.write(audio,combined,SR,subtype='PCM_24')
    sf.write(WORK/f'{eid}-voice.wav',voice,SR,subtype='PCM_24')

    events=[]
    def event(start,end,style,text,x,y,size=None,fade=False):
        tags=f'\\pos({x},{y})'
        if size:tags+=f'\\fs{size}'
        if fade:tags+='\\fad(120,100)'
        text=text.replace('\n','\\N')
        events.append(f'Dialogue: 0,{stamp(start)},{stamp(end)},{style},,0,0,0,,{{{tags}}}{text}')
    event(0,duration,'Label','하루 한 말씀',96,155)
    event(0,duration,'Title',ep['headline'],96,250)
    # Quiet typographic rule, not a large opaque card.
    event(0,duration,'Label','─'*18,96,474,28)
    labels={'intro':'잠시 마음을 쉬어가세요','reference':'오늘의 성경 말씀','verse':'성경 말씀',
            'reflection':'짧은 묵상','prayer':'함께 드리는 기도'}
    for item in items:
        start=0 if item is items[0] else item['start']
        event(start,item['end'],'Label',labels[item['kind']],96,586)
        lines=item['display'].splitlines()
        assert len(lines)<=2
        size=82
        while max(ImageFont.truetype(FONT_PATH,size).getlength(line) for line in lines)>824:
            size-=1
        assert size>=62,(eid,item['display'],size)
        item['font_size']=size
        for j,line in enumerate(lines):
            event(start,item['end'],'Main',line,96,684+j*118,size,True)
        if item['kind'] in ['verse','reference']:
            event(start,item['end'],'Source',ep['reference']+'  ·  개역한글',96,982,34)
            event(start,item['end'],'Source','성경전서 개역한글판 · 대한성서공회',96,1043,28)
        elif item['kind'] in ['prayer','reflection']:
            event(start,item['end'],'Source','말씀을 바탕으로 작성한 '+('기도' if item['kind']=='prayer' else '묵상'),96,982,30)
    for j,line in enumerate(ep['closing'].splitlines()):
        event(cursor,duration,'Main',line,96,684+j*118,68,True)
    event(cursor,duration,'Label','평안한 하루를 기도합니다',96,586)
    ass=WORK/f'{eid}.ass'
    ass.write_text(HEADER+'\n'.join(events)+'\n',encoding='utf-8-sig')
    srt=[]
    for i,item in enumerate(items,1):
        srt.append(f'{i}\n{srt_stamp(item["start"])} --> {srt_stamp(item["end"])}\n{item["text"]}\n')
    (OUTPUT/f'{eid}.srt').write_text('\n'.join(srt),encoding='utf-8-sig')

    frames=round(duration*FPS)
    # Slow 2% zoom; subtitles are overlaid after movement and stay stationary.
    vf=(f'scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,'
        f"zoompan=z='1+0.020*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1080x1920:fps={FPS},"
        f"ass=work/{eid}.ass,format=yuv420p")
    movie=OUTPUT/f'{eid}.mp4'
    run(['-loglevel','warning','-i',str(ROOT/'assets'/f'{eid}.png'),'-i',str(audio),
         '-vf',vf,'-t',f'{duration:.3f}','-c:v','libx264','-preset','fast','-crf','20',
         '-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(movie)],WORK/f'{eid}-render.log')
    for name,at in [('cover',0.8),('verse',next(s['start']+.5 for s in items if s['kind']=='verse')),
                    ('prayer',next(s['start']+.5 for s in items if s['kind']=='prayer'))]:
        destination=OUTPUT/f'{eid}-cover.jpg' if name=='cover' else WORK/f'{eid}-{name}.jpg'
        run(['-loglevel','error','-ss',str(at),'-i',str(movie),'-frames:v','1','-q:v','2',str(destination)])
    # Decode full export and check silence/peaks; record measurable checks honestly.
    run(['-v','error','-i',str(movie),'-f','null','-'],WORK/f'{eid}-decode-check.log')
    metadata={'id':eid,'duration':duration,'width':1080,'height':1920,'fps':FPS,
              'voice':VOICE,'voice_rate':'-12%','voice_peak':float(np.max(np.abs(voice))),
              'mix_peak':float(np.max(np.abs(combined))),'size_bytes':movie.stat().st_size,
              'min_subtitle_font':min(s['font_size'] for s in items),
              'exact_scripture_match':True,'full_decode_ok':True,'segments':items}
    (WORK/f'{eid}-timing.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in metadata.items() if k!='segments'},ensure_ascii=False),flush=True)
    return metadata

asyncio.run(synthesize())
all_results=[]
for episode in EPISODES:
    all_results.append(render_episode(episode))
(ROOT/'QA.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2),encoding='utf-8')
print('DONE',flush=True)
