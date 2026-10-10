from pathlib import Path
import subprocess, json, shutil, re
import imageio_ffmpeg
import soundfile as sf
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).parent
OLD=ROOT.parent/'release-2026-10-08'/'03-peace'
FF=imageio_ffmpeg.get_ffmpeg_exe()
qa=json.loads((OLD/'QA.json').read_text(encoding='utf-8'))
duration=qa['duration']
WORK=ROOT/'work';WORK.mkdir(exist_ok=True)
def run(args,name):
 p=subprocess.run([FF,'-hide_banner','-y',*args],capture_output=True,text=True,encoding='utf-8',errors='replace')
 (WORK/f'{name}.log').write_text(p.stderr,encoding='utf-8')
 if p.returncode:raise RuntimeError(p.stderr[-3000:])

# Reuse the approved voice, piano mix, and wording to compare the visual format.
shutil.copy2(OLD/'mix.wav',WORK/'mix.wav')
ass=(OLD/'subtitles.ass').read_text(encoding='utf-8-sig')
for old,new in [(1066,1296),(938,1168),(810,1040),(718,948)]:
 ass=ass.replace(f'pos(495,{old})',f'pos(495,{new})')
ass=ass.replace('Dialogue: 0,0:00:01.00,','Dialogue: 0,0:00:00.00,')
(WORK/'subtitles.ass').write_text(ass,encoding='utf-8-sig')

shots=[('lighting',0,6),('cross',0,8),('sky',4,9),('cross',5,7),('lighting',5,duration-27.8)]
transition=.55
for i,(name,start,length) in enumerate(shots):
 out=WORK/f'shot{i}.mp4'
 if not out.exists():
  run(['-v','warning','-ss',str(start),'-i',str(ROOT/'assets'/f'{name}.mp4'),'-an','-t',str(length),'-vf','scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=30,eq=saturation=0.82:brightness=-0.045,format=yuv420p','-c:v','libx264','-preset','fast','-crf','18','-threads','3',str(out)],f'shot{i}')
 print(f'shot {i+1} ready',flush=True)

current=WORK/'shot0.mp4';elapsed=shots[0][2];cuts=[]
for i in range(1,len(shots)):
 offset=elapsed-transition;cuts.append(round(offset,3));out=WORK/f'joined{i}.mp4'
 if not out.exists() or out.stat().st_size<10000:
  run(['-v','warning','-i',str(current),'-i',str(WORK/f'shot{i}.mp4'),'-filter_complex_threads','1','-filter_complex',f'[0:v]setpts=PTS-STARTPTS,fps=30,settb=1/30[a];[1:v]setpts=PTS-STARTPTS,fps=30,settb=1/30[b];[a][b]xfade=transition=fade:duration={transition}:offset={offset}[v]','-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3',str(out)],f'join{i}')
 current=out;elapsed+=shots[i][2]-transition
 print(f'transition {i} ready',flush=True)
assert abs(elapsed-duration)<.01,(elapsed,duration)

output=ROOT/'peace-live-motion-sample.mp4'
run(['-v','warning','-i',str(current),'-i',str(WORK/'mix.wav'),'-vf','scale=1080:1920,ass=work/subtitles.ass,fade=t=in:st=0:d=0.25,fade=t=out:st=34.23:d=0.8,format=yuv420p','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','19','-threads','3','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],'final')
run(['-v','error','-i',str(output),'-f','null','-'],'decode')
frames=[]
for i,t in enumerate([1.6,8.5,16,24.5,30.5]):
 p=WORK/f'frame{i}.jpg'
 run(['-v','error','-ss',str(t),'-i',str(output),'-frames:v','1','-q:v','2',str(p)],f'frame{i}')
 frames.append(p)
board=Image.new('RGB',(1250,485),(20,20,20));draw=ImageDraw.Draw(board)
for i,p in enumerate(frames):
 im=Image.open(p);im.thumbnail((250,445));board.paste(im,(250*i,30));draw.text((250*i+10,8),f'{[1.6,8.5,16,24.5,30.5][i]}s',fill='white')
board.save(ROOT/'contact-sheet.jpg')
a,sr=sf.read(WORK/'mix.wav')
qa.update({'format':'Real stock footage montage, 5 shots, 4 cross-dissolves','shot_plan':shots,'transition_starts':cuts,'transition_seconds':transition,'decode_passed':True,'audio_reused_from':str(OLD/'mix.wav'),'audio_peak':float(np.max(np.abs(a))),'output':str(output)})
(ROOT/'QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'COMPLETE: {output} / {duration:.2f}s',flush=True)
