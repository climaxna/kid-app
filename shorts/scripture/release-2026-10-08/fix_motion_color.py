from pathlib import Path
import subprocess
import imageio_ffmpeg
root=Path(__file__).parent
ff=imageio_ffmpeg.get_ffmpeg_exe()
out=root/'01-fear-motion.mp4'
vf='[0:v]format=gbrp[base];[1:v]scale=1080:1920,format=gbrp[fx];[base][fx]blend=all_mode=screen:shortest=1,format=yuv420p[v]'
r=subprocess.run([ff,'-y','-v','warning','-i',str(root/'01-fear.mp4'),'-i',str(root/'01-fear/atmosphere-overlay.mp4'),'-filter_complex',vf,'-map','[v]','-map','0:a','-c:v','libx264','-crf','19','-preset','fast','-threads','4','-c:a','copy','-movflags','+faststart',str(out)],capture_output=True)
(root/'01-fear/motion-render.log').write_bytes(r.stderr)
if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-2000:])
subprocess.run([ff,'-v','error','-i',str(out),'-f','null','-'],check=True)
for t in [5,15]:subprocess.run([ff,'-y','-v','error','-ss',str(t),'-i',str(out),'-frames:v','1',str(root/f'01-fear/motion-{t}.jpg')],check=True)
print(str(out))
