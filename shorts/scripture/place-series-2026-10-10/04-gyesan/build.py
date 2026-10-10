from pathlib import Path
import json, subprocess, math
import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter1d
from PIL import Image, ImageDraw, ImageFont
from supertonic import TTS
import imageio_ffmpeg

R=Path(__file__).parent; W=R/'work'; SR=44100
FF=imageio_ffmpeg.get_ffmpeg_exe()
rows=json.loads((R/'script.json').read_text(encoding='utf-8'))
def run(args,name):
 p=subprocess.run([FF,'-hide_banner','-y',*args],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (W/(name+'.log')).write_text(p.stderr,encoding='utf-8')
 if p.returncode: raise RuntimeError(p.stderr[-3000:])

tts=TTS(auto_download=False); style=tts.get_voice_style(voice_name='M2')
clips=[]
for i,(text,display) in enumerate(rows):
 path=W/f'voice{i}.wav'
 if not path.exists():
  wav,_=tts.synthesize(text=text,voice_style=style,total_steps=12,speed=.90,lang='ko');tts.save_audio(wav,str(path))
 a,sr=sf.read(path);assert sr==SR;a=np.squeeze(a)
 active=np.flatnonzero(abs(a)>.002)
 a=a[max(0,active[0]-int(.06*SR)):min(len(a),active[-1]+int(.13*SR))]
 clips.append(a);print('voice',i,round(len(a)/SR,2),flush=True)
speech=sum(len(a)/SR for a in clips)
gap=.48; duration=math.ceil(max(32,.35+speech+gap*5+1.6)*30)/30
assert duration<=40,(speech,duration)
voice=np.zeros(round(duration*SR));timings=[];cursor=.35
for i,a in enumerate(clips):
 start=round(cursor*SR);voice[start:start+len(a)]=a
 timings.append(dict(start=cursor,voice_end=cursor+len(a)/SR,text=rows[i][0],display=rows[i][1]))
 cursor+=len(a)/SR+gap
for i,t in enumerate(timings):t['end']=timings[i+1]['start'] if i<5 else duration
voice*=min(.8/max(abs(voice)),10**(-19/20)/np.sqrt(np.mean(voice[abs(voice)>.01]**2)))
sf.write(W/'narration.wav',voice,SR,subtype='PCM_24')
run(['-v','error','-stream_loop','1','-i',str(R.parent.parent/'audio/piano_prayer_30s_v2.wav'),'-t',str(duration),'-ar',str(SR),str(W/'music.wav')],'music')
music,_=sf.read(W/'music.wav',always_2d=True);music=music[:len(voice)]
envelope=np.full(len(voice),.15)
for t in timings:envelope[max(0,int((t['start']-.15)*SR)):int((t['voice_end']+.2)*SR)]=.075
envelope=uniform_filter1d(envelope,int(.16*SR));mix=voice[:,None]+music*envelope[:,None]
sec=np.arange(len(voice))/SR;mix*=np.minimum(np.clip(sec/.2,0,1),np.clip((duration-sec)/1.3,0,1))[:,None]
sf.write(W/'mix.wav',mix,SR,subtype='PCM_24')
header=(R.parent.parent/'sample-b-v1/work/subtitles.ass').read_text(encoding='utf-8-sig').split('[Events]')[0]+'[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
events=[]
def stamp(t):
 n=round(t*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
def ev(start,end,text,y,size=78,sty='Verse',color='FFFFFF'):
 text=text.replace('\n',r'\N');events.append(f'Dialogue: 0,{stamp(start)},{stamp(end)},{sty},,0,0,0,,{{\\pos(510,{y})\\fs{size}\\c&H{color}&\\fad(120,100)}}{text}')
ev(0,duration,'사진으로 만나는 신앙의 장소',138,38,'Reference','B7DCEB')
ev(0,duration,'대구 계산성당',207,62,'Verse')
displays=[['불을 겪고', '다시 일어선 성당의 이야기'], ['대구 계산성당', '처음 세운 성당은', '화재로 소실됐습니다'], ['그 뒤 다시 세운 성당이', '오늘 우리가 보는', '믿음의 자리입니다'], ['하늘을 향한 두 첨탑', '다시 시작할 용기를', '생각합니다'], ['무너지는 날이 있어도', '그날이 끝은 아니기를'], ['주님, 지친 마음을', '일으켜 주시고', '다시 한 걸음 걷게 해 주세요']]
font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',76)
for i,t in enumerate(timings):
 for j,line in enumerate(displays[i]):
  size=76
  while ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',size).getlength(line)>880:size-=1
  ev(0 if i==0 else t['start'],t['end'],line,1110+j*104,size)
 if i>=4:ev(t['start'],t['end'],'묵상 · 창작 기도',1030,36,'Reference','B7DCEB')
ev(timings[-1]['voice_end']-.6,duration,'아멘',1420,55)
ev(0,duration,'자료 사진: 대한민국역사박물관 · 2016',1515,32,'Credit')
ev(0,duration,'공공누리 제1유형 · 사진 확대·이동 편집',1560,29,'Credit')
ev(0,duration,'archive.much.go.kr · 자료집 684',1602,28,'Credit')
ev(0,duration,'AI 낭독 · 피아노 샘플 Alexander Holm',1650,26,'Credit')
ev(0,duration,'Salamander Grand Piano · CC BY 3.0 · 선율 편집',1690,25,'Credit')
(W/'subtitles.ass').write_text(header+'\n'.join(events),encoding='utf-8-sig')
# Alternate directions and photograph angles. No generated architecture or fake filmed motion.
photos=['photo0.jpg','photo1.jpg','photo2.jpg','photo3.jpg','photo4.jpg','photo0.jpg']
starts=[0]+[t['start'] for t in timings[1:]]; transition=.45
for i,name in enumerate(photos):
 end=starts[i+1]+transition if i<5 else duration
 length=end-starts[i];frames=math.ceil(length*30)
 z=f'1.02+0.075*on/{frames}' if i%2==0 else f'1.095-0.075*on/{frames}'
 vf=f"scale=1440:2560:force_original_aspect_ratio=increase,crop=1440:2560,zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=720x1280:fps=30,eq=saturation=0.87,format=yuv420p"
 out=W/f'shot{i}.mp4'
 if not out.exists():run(['-v','warning','-i',str(R/'assets'/name),'-vf',vf,'-t',str(length),'-an','-c:v','libx264','-crf','18','-preset','fast','-threads','3',str(out)],f'shot{i}')
 print('shot',i,flush=True)
current=W/'shot0.mp4'
for i in range(1,6):
 out=W/f'join{i}.mp4'
 if not out.exists():run(['-v','warning','-i',str(current),'-i',str(W/f'shot{i}.mp4'),'-filter_complex_threads','1','-filter_complex',f'[0:v]setpts=PTS-STARTPTS,fps=30,settb=1/30[a];[1:v]setpts=PTS-STARTPTS,fps=30,settb=1/30[b];[a][b]xfade=transition=fade:duration={transition}:offset={starts[i]}[v]','-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3',str(out)],f'join{i}')
 current=out;print('transition',i,flush=True)
out=R/'04-gyesan.mp4'
shades=[f'drawbox=x=0:y={y}:w=iw:h=24:color=black@{min(.58,max(0,(y-750)/900)*.58):.3f}:t=fill' for y in range(744,1920,24)]
shades += [f'drawbox=x=0:y={y}:w=iw:h=24:color=black@{.34*(1-y/384):.3f}:t=fill' for y in range(0,384,24)]
vf='scale=1080:1920,'+','.join(shades)+',ass=work/subtitles.ass,format=yuv420p'
run(['-v','warning','-i',str(current),'-i',str(W/'mix.wav'),'-vf',vf,'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','19','-threads','3','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(out)],'final')
run(['-v','error','-i',str(out),'-f','null','-'],'decode')
board=Image.new('RGB',(1500,480),(18,18,18))
for i,t in enumerate(starts):
 p=W/f'frame{i}.jpg';run(['-v','error','-ss',str(t+.8),'-i',str(out),'-frames:v','1','-q:v','2',str(p)],f'frame{i}')
 im=Image.open(p);im.thumbnail((250,445));board.paste(im,(i*250,25));ImageDraw.Draw(board).text((i*250+8,5),f'{t+.8:.1f}s',fill='white')
board.save(R/'contact-sheet.jpg')
qa=dict(duration=duration,voice='Supertonic3 M2 speed .90',timings=timings,shot_starts=starts,photos=photos,decode_passed=True,audio_peak=float(abs(mix).max()),output=str(out),published=False)
(R/'QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE',duration,str(out),flush=True)
