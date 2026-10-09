from pathlib import Path
import json, math, subprocess, re
import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter1d
from PIL import ImageFont
from supertonic import TTS
import imageio_ffmpeg

ROOT=Path(__file__).parent
BASE=ROOT.parent/'sample-b-v1'
FF=imageio_ffmpeg.get_ffmpeg_exe()
SR=44100
episodes=[
 {'slug':'01-fear','title':'걱정이 많아 마음이 불안할 때','ref':'이사야 41장 10절','source':'https://www.bible.com/ko/bible/88/ISA.41.10.KRV','verse':'두려워 말라 내가 너와 함께 함이니라 놀라지 말라 나는 네 하나님이 됨이니라 내가 너를 굳세게 하리라 참으로 너를 도와 주리라 참으로 나의 의로운 오른손으로 너를 붙들리라','rows':[
 ('도입','걱정이 많아 마음이 불안하신가요?','걱정이 많아\n마음이 불안하신가요?'),
 ('말씀','두려워 말라 내가 너와 함께 함이니라.','두려워 말라\n내가 너와 함께 함이니라'),
 ('말씀','놀라지 말라 나는 네 하나님이 됨이니라.','놀라지 말라\n나는 네 하나님이 됨이니라'),
 ('말씀','내가 너를 굳세게 하리라.','내가 너를\n굳세게 하리라'),
 ('말씀','참으로 너를 도와 주리라.','참으로 너를\n도와 주리라'),
 ('말씀','참으로 나의 의로운 오른손으로 너를 붙들리라.','참으로 나의 의로운\n오른손으로 너를 붙들리라'),
 ('묵상','두려움 속에서도 하나님께 마음을 맡겨 봅니다.','두려움 속에서도\n하나님께 마음을 맡겨 봅니다'),
 ('기도','주님, 오늘도 제 손을 붙드시고 한 걸음 걸을 힘을 주세요. 아멘.','주님, 제 손을 붙드시고\n한 걸음 걸을 힘을 주세요. 아멘')
 ]},
 {'slug':'02-rest','title':'가족을 위해 애쓰느라 지친 당신에게','ref':'마태복음 11장 28절','source':'https://www.bible.com/ko/bible/88/MAT.11.28.KRV','verse':'수고하고 무거운 짐진 자들아 다 내게로 오라 내가 너희를 쉬게 하리라','rows':[
 ('도입','가족을 위해 애쓰느라, 내 마음은 돌보지 못하셨나요?','가족을 위해 애쓰느라\n내 마음은 돌보지 못하셨나요?'),
 ('말씀','수고하고 무거운 짐진 자들아.','수고하고\n무거운 짐진 자들아'),
 ('말씀','다 내게로 오라 내가 너희를 쉬게 하리라.','다 내게로 오라\n내가 너희를 쉬게 하리라'),
 ('묵상','예수님은 지친 우리를, 당신께로 부르십니다.','예수님은 지친 우리를\n당신께로 부르십니다'),
 ('묵상','혼자 감당하려던 마음의 짐을, 기도로 내려놓아 봅니다.','혼자 감당하려던 마음의 짐을\n기도로 내려놓아 봅니다'),
 ('기도','주님, 제 수고와 지친 마음을 주님께 맡깁니다.','주님, 제 수고와 지친 마음을\n주님께 맡깁니다'),
 ('기도','주님께 배우며, 오늘 필요한 쉼을 누리게 해 주세요. 아멘.','주님께 배우며\n오늘 필요한 쉼을 누리게 해 주세요'),
 ('기도','아멘.','아멘')
 ]},
 {'slug':'03-peace','title':'잠들기 전 걱정을 내려놓는 말씀','ref':'시편 4편 8절','source':'https://www.bible.com/ko/bible/88/PSA.4.8.KRV','verse':'내가 평안히 눕고 자기도 하리니 나를 안전히 거하게 하시는 이는 오직 여호와시니이다','rows':[
 ('도입','잠자리에 누워도, 내일 걱정이 떠오르시나요?','잠자리에 누워도\n내일 걱정이 떠오르시나요?'),
 ('말씀','내가 평안히 눕고 자기도 하리니.','내가 평안히 눕고\n자기도 하리니'),
 ('말씀','나를 안전히 거하게 하시는 이는 오직 여호와시니이다.','나를 안전히 거하게 하시는 이는\n오직 여호와시니이다'),
 ('묵상','다 풀지 못한 걱정도, 하나님께 말씀드려 봅니다.','다 풀지 못한 걱정도\n하나님께 말씀드려 봅니다'),
 ('묵상','오늘의 수고를 내려놓고, 주님을 의지하며 하루를 마무리합니다.','오늘의 수고를 내려놓고\n주님을 의지하며 하루를 마무리합니다'),
 ('기도','주님, 저와 사랑하는 가족을 돌보아 주세요.','주님, 저와 사랑하는 가족을\n돌보아 주세요'),
 ('기도','이 밤에도 주님을 신뢰하며, 평안히 쉬게 해 주세요.','이 밤에도 주님을 신뢰하며\n평안히 쉬게 해 주세요'),
 ('기도','아멘.','아멘')
 ]}
]
# Keep prayer audio and displayed wording aligned.
episodes[0]['rows'][-1]=('기도','주님, 제 손을 붙드시고 한 걸음 걸을 힘을 주세요. 아멘.','주님, 제 손을 붙드시고\n한 걸음 걸을 힘을 주세요. 아멘')
episodes[1]['rows'][-2]=('기도','주님께 배우며, 오늘 필요한 쉼을 누리게 해 주세요.','주님께 배우며\n오늘 필요한 쉼을 누리게 해 주세요')
norm=lambda s:re.sub(r'[\s.,?]','',s)
tts=TTS(auto_download=False)
style=tts.get_voice_style(voice_name='M2')
header=(BASE/'work/subtitles.ass').read_text(encoding='utf-8-sig').split('[Events]')[0]
header+='[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
def stamp(t):
 n=round(t*100);return f'{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}'
def run(args,log):
 r=subprocess.run([FF,'-hide_banner','-y',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 log.write_text(r.stderr,encoding='utf-8')
 if r.returncode:raise RuntimeError(r.stderr[-3000:])
reports=[]
for ep in episodes:
 work=ROOT/ep['slug'];work.mkdir(exist_ok=True)
 if (work/'QA.json').exists() and (ROOT/f'{ep["slug"]}.mp4').exists():
  reports.append(json.loads((work/'QA.json').read_text(encoding='utf-8')))
  print(f'{ep["slug"]}: using checked completed file',flush=True)
  continue
 assert norm(' '.join(x[1] for x in ep['rows'] if x[0]=='말씀'))==norm(ep['verse'])
 clips=[]
 for i,(kind,text,display) in enumerate(ep['rows']):
  assert norm(text)==norm(display)
  path=work/f'voice-{i}.wav'
  if not path.exists():
   wav,_=tts.synthesize(text=text,voice_style=style,total_steps=12,speed=.90,lang='ko');tts.save_audio(wav,str(path))
  a,sr=sf.read(path);assert sr==SR
  a=np.squeeze(a);active=np.flatnonzero(np.abs(a)>.002)
  if len(active):a=a[max(0,active[0]-int(.055*SR)):min(len(a),active[-1]+int(.14*SR))]
  clips.append(a)
 speech=sum(len(a)/SR for a in clips)
 gap=max(.8,(34-1.0-3.0-speech)/(len(clips)-1))
 gap=min(gap,1.4)
 duration=math.ceil(max(34,1+speech+gap*(len(clips)-1)+3)*30)/30
 assert 30<=duration<=40,(ep['slug'],speech,duration)
 voice=np.zeros(round(duration*SR));timing=[];cursor=1.
 for i,(row,a) in enumerate(zip(ep['rows'],clips)):
  start=round(cursor*SR);voice[start:start+len(a)]=a
  end=cursor+len(a)/SR
  timing.append({'kind':row[0],'text':row[1],'display':row[2],'start':cursor,'voice_end':end,'end':end+gap if i<len(clips)-1 else duration})
  cursor=end+gap
 loud=voice[np.abs(voice)>.01];voice*=min(10**(-19/20)/np.sqrt(np.mean(loud**2)),.8/np.max(np.abs(voice)))
 sf.write(work/'narration.wav',voice,SR,subtype='PCM_24')
 run(['-v','error','-stream_loop','1','-i',str(ROOT.parent/'audio/piano_prayer_30s_v2.wav'),'-t',str(duration),'-ar',str(SR),str(work/'music.wav')],work/'music.log')
 music,sr=sf.read(work/'music.wav',always_2d=True)
 music=np.pad(music,((0,max(0,len(voice)-len(music))),(0,0)))[:len(voice)]
 envelope=np.full(len(voice),.16)
 for row in timing:envelope[max(0,int((row['start']-.15)*SR)):min(len(voice),int((row['voice_end']+.2)*SR))]=.08
 envelope=uniform_filter1d(envelope,int(.18*SR));mix=voice[:,None]+music*envelope[:,None]
 t=np.arange(len(voice))/SR;mix*=np.minimum(np.clip(t/.4,0,1),np.clip((duration-t)/1.8,0,1))[:,None]
 assert np.max(np.abs(mix))<.99;sf.write(work/'mix.wav',mix,SR,subtype='PCM_24')
 events=[]
 def event(start,end,sty,text,y,size):
  text=text.replace('\n',r'\N');events.append(f'Dialogue: 0,{stamp(start)},{stamp(end)},{sty},,0,0,0,,{{\\pos(495,{y})\\fs{size}\\fad(130,80)}}{text}')
 for row in timing:
  size=100
  while max(ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',size).getlength(line) for line in row['display'].splitlines())>890:size-=1
  if size<78:
   size=82; lines=[];current='';font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',size)
   for word in row['display'].replace('\n',' ').split():
    candidate=(current+' '+word).strip()
    if current and font.getlength(candidate)>890:lines.append(current);current=word
    else:current=candidate
   if current:lines.append(current)
   assert len(lines)<=3
   row['display']='\n'.join(lines)
  assert size>=78
  row['font_size']=size
  for j,line in enumerate(row['display'].splitlines()):event(row['start'],row['end'],'Verse',line,810+j*128,size)
  event(row['start'],row['end'],'Reference',row['kind'] if row['kind']!='도입' else '오늘의 말씀',718,40)
 event(0,duration,'Reference',ep['ref'],1505,54)
 event(0,duration,'Credit','개역한글 · 대한성서공회',1588,30)
 (work/'subtitles.ass').write_text(header+'\n'.join(events),encoding='utf-8-sig')
 frames=round(duration*30)
 vf=(f'scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,'f"zoompan=z='1+0.018*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1080x1920:fps=30,"f'ass={ep["slug"]}/subtitles.ass,format=yuv420p')
 output=ROOT/f'{ep["slug"]}.mp4'
 run(['-v','warning','-i',str(BASE/'jesus-sacred-painting-v3.png'),'-i',str(work/'mix.wav'),'-vf',vf,'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','19','-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],work/'render.log')
 for name,at in [('cover',timing[0]['start']+.3),('verse',timing[1]['start']+.3),('prayer',timing[-2]['start']+.3)]:run(['-v','error','-ss',str(at),'-i',str(output),'-frames:v','1','-q:v','2',str(work/f'{name}.jpg')],work/f'{name}.log')
 run(['-v','error','-i',str(output),'-f','null','-'],work/'decode.log')
 report={**ep,'duration':duration,'timing':timing,'peak':float(np.max(np.abs(mix))),'decode_passed':True,'voice':'Supertonic3 M2 B speed .90','video':'1080x1920 30fps H264 AAC'}
 (work/'QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');reports.append(report)
 print(f'{ep["slug"]}: {duration:.2f} seconds complete',flush=True)
(ROOT/'manifest.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
credits='피아노 음원 샘플: Salamander Grand Piano — Alexander Holm (CC BY 3.0)\nhttps://github.com/Tonejs/audio/tree/master/salamander\nhttps://creativecommons.org/licenses/by/3.0/\n개별 피아노 샘플로 선율을 새로 구성하고 잔향과 음량을 편집했습니다.\n배경: AI 생성 성화. 낭독: AI 음성. 묵상과 기도: 제작 문구.'
upload=['# 오늘 업로드할 영상 3편\n','같은 B 목소리와 승인한 성화 배경으로 제작했습니다. 말씀과 제작 묵상·기도를 영상 내 표기로 구분합니다. 아직 게시하지 않았습니다.\n']
for ep in reports:
 body=f'{ep["title"]}\n\n{ep["ref"]} 말씀을 함께 듣고 잠깐 묵상하며 기도합니다.\n성경전서 개역한글판 · 대한성서공회\n본문 확인: {ep["source"]}\n\n{credits}\n\n#성경말씀 #말씀묵상 #기도 #예수님 #마음의평안'
 (ROOT/f'{ep["slug"]}-upload.txt').write_text(body,encoding='utf-8')
 upload.append(f'## {ep["title"]}\n\n파일: {ep["slug"]}.mp4\n길이: {ep["duration"]:.2f}초\n\n'+body+'\n')
upload.append('## 반응 기록\n\n업로드 시각, 24시간 조회수, 평균 시청시간·완주율(제공될 경우), 좋아요, 댓글, 새 팔로워를 편별로 기록합니다. 3편의 첫 반응만으로 성패를 단정하지 않습니다.\n')
(ROOT/'UPLOAD_GUIDE.md').write_text('\n'.join(upload),encoding='utf-8')
