from pathlib import Path
import json, re, subprocess, math
import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter1d
from supertonic import TTS
from PIL import ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).parent
FF=imageio_ffmpeg.get_ffmpeg_exe()
SR=44100
FPS=30
WORK=ROOT/'work'
WORK.mkdir(exist_ok=True)
phrases=[
 ('두려워 말라 내가 너와 함께 함이니라.','두려워 말라\n내가 너와 함께 함이니라'),
 ('놀라지 말라 나는 네 하나님이 됨이니라.','놀라지 말라\n나는 네 하나님이 됨이니라'),
 ('내가 너를 굳세게 하리라.','내가 너를\n굳세게 하리라'),
 ('참으로 너를 도와 주리라.','참으로 너를\n도와 주리라'),
 ('참으로 나의 의로운 오른손으로 너를 붙들리라.','참으로 나의 의로운\n오른손으로 너를 붙들리라')
]
verse='두려워 말라 내가 너와 함께 함이니라 놀라지 말라 나는 네 하나님이 됨이니라 내가 너를 굳세게 하리라 참으로 너를 도와 주리라 참으로 나의 의로운 오른손으로 너를 붙들리라'
normalize=lambda s:re.sub(r'[\s.,]','',s)
assert normalize(' '.join(p[0] for p in phrases))==normalize(verse)

def run(args,log=None):
 r=subprocess.run([FF,'-hide_banner','-y',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 if log:log.write_text(r.stderr,encoding='utf-8')
 if r.returncode:raise RuntimeError(r.stderr[-3500:])
 return r

tts=TTS(auto_download=False)
style=tts.get_voice_style(voice_name='M2')
clips=[]
for i,(text,display) in enumerate(phrases):
 path=WORK/f'voice-{i}.wav'
 if not path.exists():
  wav,_=tts.synthesize(text=text,voice_style=style,total_steps=12,speed=.90,lang='ko')
  tts.save_audio(wav,str(path))
 a,rate=sf.read(path)
 assert rate==SR
 a=np.squeeze(a)
 active=np.flatnonzero(np.abs(a)>.002)
 if len(active):a=a[max(0,active[0]-int(.055*SR)):min(len(a),active[-1]+int(.14*SR))]
 assert np.isfinite(a).all() and len(a)>SR
 clips.append(a)
 print(f'Voice phrase {i+1}: {len(a)/SR:.2f}s',flush=True)

cursor=1.65
timing=[]
for i,((text,display),clip) in enumerate(zip(phrases,clips)):
 voiced=len(clip)/SR
 end=cursor+voiced+(1.0 if i<4 else 2.6)
 timing.append({'start':cursor,'voice_end':cursor+voiced,'end':end,'text':text,'display':display})
 cursor=end
duration=math.ceil(cursor*FPS)/FPS
voice=np.zeros(round(duration*SR))
for row,clip in zip(timing,clips):
 start=round(row['start']*SR)
 voice[start:start+len(clip)]=clip
voiced=voice[np.abs(voice)>.01]
voice*=min(10**(-19/20)/np.sqrt(np.mean(voiced**2)),.8/np.max(np.abs(voice)))
sf.write(ROOT/'B-narration.wav',voice,SR,subtype='PCM_24')
run(['-v','error','-i',str(ROOT.parent/'audio/piano_prayer_30s_v2.wav'),'-af',f'atempo={30/duration:.6f}', '-ar',str(SR),str(WORK/'music.wav')])
music,rate=sf.read(WORK/'music.wav',always_2d=True)
music=np.pad(music,((0,max(0,len(voice)-len(music))),(0,0)))[:len(voice)]
envelope=np.full(len(voice),.16)
for row in timing:
 start=max(0,int((row['start']-.15)*SR));end=min(len(voice),int((row['voice_end']+.2)*SR))
 envelope[start:end]=.08
envelope=uniform_filter1d(envelope,int(.18*SR))
music*=envelope[:,None]
mix=voice[:,None]+music
t=np.arange(len(voice))/SR
mix*=np.minimum(np.clip(t/.4,0,1),np.clip((duration-t)/1.7,0,1))[:,None]
assert np.max(np.abs(mix))<.99 and np.isfinite(mix).all()
sf.write(WORK/'mix.wav',mix,SR,subtype='PCM_24')

def stamp(t):
 n=round(t*100)
 return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Verse,Malgun Gothic,104,&H00FFFFFF,&H00FFFFFF,&H0014100D,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,8,0,0,0,1
Style: Reference,Malgun Gothic,54,&H00FFFFFF,&H00FFFFFF,&H0014100D,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,8,0,0,0,1
Style: Credit,Malgun Gothic,30,&H00FFFFFF,&H00FFFFFF,&H0014100D,&H80000000,0,0,0,0,100,100,0,0,1,2,1,8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
events=[]
def event(start,end,style,text,y,size=None,fade=True):
 tags=f'\\pos(495,{y})'
 if size:tags+=f'\\fs{size}'
 if fade:tags+='\\fad(150,100)'
 text=text.replace('\n','\\N')
 events.append(f'Dialogue: 0,{stamp(start)},{stamp(end)},{style},,0,0,0,,{{{tags}}}{text}')
event(0,1.6,'Verse','이사야\n41장 10절',570,112)
for row in timing:
 lines=row['display'].splitlines();size=104
 while max(ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',size).getlength(line) for line in lines)>900:size-=1
 assert size>=72
 row['font_size']=size
 for j,line in enumerate(lines):event(row['start'],row['end'],'Verse',line,600+j*145,size)
event(1.65,duration,'Reference','이사야 41장 10절',1505,54,False)
event(1.65,duration,'Credit','개역한글 · 대한성서공회',1588,30,False)
(WORK/'subtitles.ass').write_text(header+'\n'.join(events)+'\n',encoding='utf-8-sig')
frames=round(duration*FPS)
vf=(f'scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,'
 f"zoompan=z='1+0.018*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1080x1920:fps={FPS},"
 'ass=work/subtitles.ass,format=yuv420p')
output=ROOT/'isaiah41-10-B-sample.mp4'
run(['-v','warning','-i','cross-sunset.png','-i','work/mix.wav','-vf',vf,'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','19','-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],WORK/'render.log')
for name,at in [('cover',.7),('verse',2.5),('last-verse',timing[-1]['start']+.5)]:
 run(['-v','error','-ss',str(at),'-i',str(output),'-frames:v','1','-q:v','2',str(ROOT/f'{name}.jpg')])
run(['-v','error','-i',str(output),'-f','null','-'],WORK/'decode.log')
qa={'duration':duration,'voice':'B / M2','engine':'Supertonic 3','speed':.90,'steps':12,'video':'1080x1920,30fps,H264/AAC','mix_peak':float(np.max(np.abs(mix))),'exact_verse_text':True,'full_decode':True,'timing':timing,'note':'Signal and visual checks; voice tone selected by user. Listening assessment not claimed.'}
(ROOT/'QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in qa.items() if k!='timing'},ensure_ascii=False),flush=True)
