from pathlib import Path
import json
from PIL import ImageFont

root=Path(__file__).parent
episodes=json.loads((root/'episodes.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',82)
for ep in episodes:
 rows=[]
 for kind,text,display in ep['rows']:
  lines=[];current=''
  for word in text.strip('.').split():
   candidate=(current+' '+word).strip()
   if current and font.getlength(candidate)>880:lines.append(current);current=word
   else:current=candidate
  if current:lines.append(current)
  if len(lines)>3:
   # Split long speech into readable caption units, preserving every word.
   half=len(lines)//2
   for group in [lines[:half],lines[half:]]:
    segment=' '.join(group)
    rows.append((kind,segment+'.','\n'.join(group)))
  else:rows.append((kind,text,'\n'.join(lines)))
 ep['rows']=rows
template=(root.parent/'release-2026-10-08/build_three.py').read_text(encoding='utf-8')
start=template.index('episodes=[');end=template.index('norm=lambda')
code=template[:start]+'episodes='+repr(episodes)+'\n'+template[end:]
start=code.index(' frames=round(duration*30)')
end=code.index(' for name,at in',start)
replacement=''' output=ROOT/f'{ep["slug"]}.mp4'
 background=ROOT/'backgrounds'/f'{ep["background"]}-motion.mp4'
 assert background.exists(),str(background)
 vf=f'scale=1080:1920,ass={ep["slug"]}/subtitles.ass,format=yuv420p'
 run(['-v','warning','-stream_loop','-1','-i',str(background),'-i',str(work/'mix.wav'),'-vf',vf,'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','19','-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],work/'render.log')
'''
code=code[:start]+replacement+code[end:]
code=code.replace("event(0,duration,'Reference',ep['ref'],1505,54)","event(0,duration,'Reference',ep['ref'],1505,42 if len(ep['ref'])>15 else 54)")
code=code.replace('오늘 업로드할 영상 3편','오늘 업로드할 영상 5편').replace('승인한 성화 배경','새 성화 배경과 풍경 영역 애니메이션').replace('3편의 첫 반응','5편의 첫 반응').replace('배경: AI 생성 성화.','배경: AI 생성 성화에 물결과 구름 움직임을 합성했습니다.')
exec(compile(code,str(root/'build_five.py'),'exec'))
