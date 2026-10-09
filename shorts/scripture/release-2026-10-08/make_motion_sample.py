from pathlib import Path
import subprocess,json
import numpy as np
from scipy.ndimage import gaussian_filter
import imageio_ffmpeg

ROOT=Path(__file__).parent
FF=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=540,960,30
duration=34
rng=np.random.default_rng(41)
noise=np.zeros((H,W*2),dtype=np.float32)
for sigma,weight in [(16,.3),(38,.5),(80,.2)]:
 a=gaussian_filter(rng.normal(size=(H,W*2)).astype(np.float32),sigma)
 a=(a-a.mean())/(a.std()+1e-6);noise+=a*weight
y,x=np.mgrid[:H,:W].astype(np.float32)
mist_band=np.exp(-((y-530)/145)**2)
# Keep the portrait and bottom attribution unobstructed.
mist_band*=np.clip((y-340)/100,0,1)*np.clip((790-y)/90,0,1)
ray_angle=np.arctan2(y-38,x-375)
ray_distance=np.sqrt((x-375)**2+(y-38)**2)
ray_mask=np.clip((y-220)/100,0,1)*np.clip((720-y)/200,0,1)*np.exp(-ray_distance/700)
overlay=ROOT/'01-fear'/'atmosphere-overlay.mp4'
cmd=[FF,'-hide_banner','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-crf','19','-preset','fast','-pix_fmt','yuv420p','-threads','2',str(overlay)]
with (ROOT/'01-fear/motion-overlay.log').open('wb') as log:
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 try:
  for i in range(duration*FPS):
   t=i/FPS; shift=int(t*4)
   a=noise[:,shift:shift+W]
   mist=np.clip((a+.5)/3,0,1)*mist_band*.068
   rays=(.5+.5*np.sin(ray_angle*19+.035*np.sin(t*.25)))**12
   rays*=ray_mask*(.023+.012*np.sin(t*.4))
   light=np.clip(mist+rays,0,.09)
   frame=np.stack([light*.94,light*.87,light*.72],axis=2)
   proc.stdin.write(np.ascontiguousarray(np.uint8(frame*255)).tobytes())
 finally:proc.stdin.close()
 if proc.wait():raise RuntimeError('overlay render failed')
out=ROOT/'01-fear-motion.mp4'
cmd=[FF,'-hide_banner','-y','-v','warning','-i',str(ROOT/'01-fear.mp4'),'-i',str(overlay),'-filter_complex','[0:v]format=gbrp[base];[1:v]scale=1080:1920,format=gbrp[fx];[base][fx]blend=all_mode=screen:shortest=1,format=yuv420p[v]','-map','[v]','-map','0:a','-c:v','libx264','-crf','19','-preset','fast','-threads','4','-c:a','copy','-movflags','+faststart',str(out)]
r=subprocess.run(cmd,capture_output=True);(ROOT/'01-fear/motion-render.log').write_bytes(r.stderr)
if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-2000:])
r=subprocess.run([FF,'-v','error','-i',str(out),'-f','null','-'],capture_output=True)
if r.returncode:raise RuntimeError('decode failed')
for second in [5,15]:
 subprocess.run([FF,'-y','-v','error','-ss',str(second),'-i',str(out),'-frames:v','1',str(ROOT/f'01-fear/motion-{second}.jpg')],check=True)
(ROOT/'01-fear/MOTION_QA.json').write_text(json.dumps({'duration':duration,'full_decode':True,'effects':'Slow drifting atmospheric mist and gently varying rays composited over approved painting. Existing subtle zoom retained. Figure is not animated. Audio and subtitles unchanged.'},indent=2),encoding='utf-8')
print(str(out))
