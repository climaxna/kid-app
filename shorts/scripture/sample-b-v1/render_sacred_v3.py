from pathlib import Path
import json, subprocess
import imageio_ffmpeg

root=Path(__file__).parent
ff=imageio_ffmpeg.get_ffmpeg_exe()
qa=json.loads((root/'QA.json').read_text(encoding='utf-8'))
duration=qa['duration']
frames=round(duration*30)
subs=(root/'work/subtitles.ass').read_text(encoding='utf-8-sig')
subs=subs.replace(r'\pos(495,570)',r'\pos(495,810)').replace(r'\pos(495,600)',r'\pos(495,810)').replace(r'\pos(495,745)',r'\pos(495,955)')
(root/'work/subtitles-sacred-v3.ass').write_text(subs,encoding='utf-8-sig')
output=root/'isaiah41-10-B-sacred-v3.mp4'
def run(args,log):
    result=subprocess.run([ff,'-hide_banner','-y',*args],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (root/'work'/log).write_text(result.stderr,encoding='utf-8')
    if result.returncode: raise RuntimeError(result.stderr[-3000:])
vf=(f'scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,'
    f"zoompan=z='1+0.018*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1080x1920:fps=30,"
    'ass=work/subtitles-sacred-v3.ass,format=yuv420p')
run(['-v','warning','-i','jesus-sacred-painting-v3.png','-i','work/mix.wav','-vf',vf,'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','19','-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],'render-sacred-v3.log')
for name,at in [('cover',.7),('verse',2.5),('last-verse',qa['timing'][-1]['start']+.5)]:
    run(['-v','error','-ss',str(at),'-i',str(output),'-frames:v','1','-q:v','2',str(root/f'sacred-v3-{name}.jpg')],f'sacred-v3-{name}.log')
run(['-v','error','-i',str(output),'-f','null','-'],'decode-sacred-v3.log')
qa.update({'background':'jesus-sacred-painting-v3.png','subtitle_y':[810,955],'output':output.name,'full_decode':True})
(root/'QA-sacred-v3.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(output))
