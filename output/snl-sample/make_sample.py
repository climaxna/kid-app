from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

P = Path(__file__).resolve().parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = 'C:/Windows/Fonts/malgunbd.ttf'

def center(d, text, y, size, color):
    font = ImageFont.truetype(FONT, size)
    box = d.textbbox((0, 0), text, font=font)
    d.text(((1080 - (box[2]-box[0])) / 2, y), text, font=font, fill=color)

base = Image.new('RGBA', (1080,1920), (12,12,15,255))
d = ImageDraw.Draw(base)
center(d, 'SNL 코리아  ·  MZ 오피스', 140, 32, '#b6b6bf')
center(d, '업무 부탁했다가', 225, 80, 'white')
center(d, '눈치 보게 된 이유', 328, 80, '#ffe34b')
d.rounded_rectangle((474,462,606,470), radius=4, fill='#ffe34b')
center(d, '전종서 편 하이라이트', 1660, 32, '#b6b6bf')
center(d, '출처  쿠팡플레이 공식 YouTube', 1715, 27, '#777781')
base.save(P/'layout.png')

labels=[('자료 정리 부탁했을 뿐인데…',0,7),('대답은 평범한데 눈빛이…',7,13.5),('부탁한 사람이 눈치 보는 중',13.5,22.2)]
for i,(text,start,end) in enumerate(labels):
    im=Image.new('RGBA',(1080,1920))
    center(ImageDraw.Draw(im),text,1440,48,'#ffe34b')
    im.save(P/f'caption-{i}.png')

cmd=[FF,'-y','-hide_banner','-loglevel','error','-ss','119.6','-t','22.2','-i',str(P/'source.mp4'),'-loop','1','-i',str(P/'layout.png')]
for i in range(3): cmd+=['-loop','1','-i',str(P/f'caption-{i}.png')]
graph='[0:v]split=2[sharp][blur];[blur]scale=1080:900:force_original_aspect_ratio=increase,crop=1080:900,gblur=sigma=36,eq=brightness=-0.20[bg];[sharp]scale=1080:608,setsar=1[fg];[1:v][bg]overlay=0:520:shortest=1[b];[b][fg]overlay=0:666:shortest=1[v0];'
for i,(_,start,end) in enumerate(labels):
    graph+=f"[v{i}][{i+2}:v]overlay=0:0:enable='between(t,{start},{end})':shortest=1[v{i+1}];"
graph=graph.rstrip(';')
cmd+=['-filter_complex',graph,'-map','[v3]','-map','0:a:0','-af','afade=t=out:st=22.05:d=0.15','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','192k','-metadata:s:a:0','language=kor','-movflags','+faststart','-t','22.2',str(P/'snl-vertical-sample.mp4')]
subprocess.run(cmd,check=True)
subprocess.run([FF,'-y','-hide_banner','-loglevel','error','-ss','11','-i',str(P/'snl-vertical-sample.mp4'),'-frames:v','1',str(P/'preview.jpg')],check=True)
print(P/'snl-vertical-sample.mp4')
