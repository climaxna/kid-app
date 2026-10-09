from pathlib import Path
import subprocess, json
import numpy as np
import cv2
import imageio_ffmpeg

root=Path(__file__).parent/'backgrounds'
ff=imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS,SECONDS=720,1280,30,12
yy,xx=np.mgrid[:H,:W].astype(np.float32)
x,y=xx/W,yy/H
def smooth(a,b,z):
 t=np.clip((z-a)/(b-a),0,1);return t*t*(3-2*t)
def polygon(points):
 m=np.zeros((H,W),np.float32)
 cv2.fillPoly(m,[np.array([(int(px*W),int(py*H)) for px,py in points],np.int32)],1)
 return cv2.GaussianBlur(m,(0,0),6)
for name in ['lake','forest','meadow']:
 im=cv2.imread(str(root/f'{name}.png'))
 im=cv2.resize(im,(W,H),interpolation=cv2.INTER_AREA)
 # Animation applies to landscape areas; portrait and cross remain fixed.
 protect=smooth(.42,.50,x)*(1-smooth(.37,.42,y))
 sky=(1-smooth(.57,.65,y))*(1-protect)
 cloud=sky*(1-smooth(.37,.51,x))*smooth(.01,.08,x)
 water=np.zeros((H,W),np.float32)
 foliage=np.zeros_like(water)
 if name=='lake':
  water=polygon([(.27,.744),(.99,.744),(.99,.995),(.77,.995),(.48,.90),(.29,.835)])
 elif name=='forest':
  water=polygon([(.63,.792),(.89,.79),(.99,.93),(.91,.995),(.65,.995),(.59,.92)])
  foliage=(1-smooth(.29,.41,x))*(1-smooth(.48,.60,y))*smooth(.01,.08,x)
 else:
  foliage=smooth(.79,.88,y)*smooth(.50,.68,x)*(1-smooth(.95,1,x))
 water*=1-smooth(.98,1,y)
 moving=cloud+water+foliage
 out=root/f'{name}-motion.mp4'
 cmd=[ff,'-y','-hide_banner','-v','warning','-f','rawvideo','-pixel_format','bgr24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-threads','3','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
 samples=[]
 with (root/f'{name}-motion.log').open('wb') as log:
  p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  try:
   for i in range(FPS*SECONDS):
    phase=2*np.pi*i/(FPS*SECONDS)
    dx=cloud*(11*np.sin(phase)+3*np.sin(phase*2+y*8))
    dy=cloud*2*np.sin(phase+y*7)
    dx+=water*(6*np.sin(y*155-phase*3)+2*np.sin(x*25+y*55-phase*2))
    dy+=water*(3.2*np.sin(y*120+x*5-phase*3))
    dx+=foliage*(4.5*np.sin(phase*3+y*6)+1.8*np.sin(phase*5+y*14))
    dy+=foliage*1.3*np.sin(phase*3+x*7)
    frame=cv2.remap(im,(xx+dx).astype(np.float32),(yy+dy).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    if i in [0,90,180,270]:samples.append(frame.copy())
    p.stdin.write(np.ascontiguousarray(frame).tobytes())
  finally:p.stdin.close()
  if p.wait():raise RuntimeError('background encode failed')
 # Compare frames away from portrait to demonstrate motion; assert portrait invariant.
 face=(x>.54)&(y<.35)
 max_face_diff=max(int(np.max(np.abs(a[face].astype(int)-samples[0][face].astype(int)))) for a in samples)
 assert max_face_diff==0
 region=moving>.4
 differences=[float(np.mean(np.abs(a[region].astype(float)-samples[0][region].astype(float)))) for a in samples[1:]]
 assert max(differences)>1
 result={'source':name+'.png','video':out.name,'duration':SECONDS,'fps':FPS,'method':'Localized image warping for cloud drift, water ripples and foliage sway. Not generated live-action video. No global zoom.','portrait_pixel_difference':max_face_diff,'motion_region_mean_pixel_difference':differences,'loop_period_seconds':SECONDS}
 (root/f'{name}-motion-QA.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(name+' motion ready',flush=True)
 print(json.dumps(result),flush=True)
