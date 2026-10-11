from pathlib import Path
import json,zipfile
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parent
es=json.loads((r/'episodes.json').read_text(encoding='utf-8'))
audit=[]
board=Image.new('RGB',(1500,610),(239,234,222));d=ImageDraw.Draw(board)
font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',22)
for i,e in enumerate(es):
 p=r/e['slug'];q=json.loads((p/'QA.json').read_text(encoding='utf-8'));v=p/(e['slug']+'.mp4')
 reader=imageio_ffmpeg.read_frames(str(v));meta=next(reader);reader.close()
 assert meta['size']==(1080,1920) and meta['fps']==30
 assert 30<=meta['duration']<=40 and q['decode_passed'] and q['audio_peak']<.99
 assert v.stat().st_size>1000000
 cover=Image.open(p/'work/frame0.jpg');cover.save(p/'cover.jpg',quality=94)
 im=cover.copy();im.thumbnail((280,498));board.paste(im,(i*300+10,68))
 d.text((i*300+10,14),e['place'],font=font,fill='#352f28')
 d.text((i*300+10,577),str(round(meta['duration'],1))+'초',font=font,fill='#352f28')
 audit.append(dict(place=e['place'],file=str(v),duration=meta['duration'],width=1080,height=1920,fps=30,decode_passed=q['decode_passed'],audio_peak=q['audio_peak'],description_characters=len((p/'UPLOAD_TEXT.txt').read_text(encoding='utf-8')),photos_verified=5,published=False))
board.save(r/'five-episodes-preview.jpg',quality=94)
(r/'FINAL_QA.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
readme=['# 실제 장소 이야기와 짧은 기도 5편','', '1080×1920, 30fps, MP4. 실제 장소의 자료 사진을 확대·이동하고 장면을 전환했습니다. AI 낭독과 피아노 배경음을 사용했습니다.','', '## 완성 영상','']
for a in audit:readme.append('- '+a['place']+': '+str(round(a['duration'],1))+'초')
readme+=['','UPLOAD_GUIDE.md에 장소 태그 검색어·주소 확인용 정보·제목이 있습니다. 각 폴더의 UPLOAD_TEXT.txt는 복사 가능한 300자 이내의 설명문입니다. CREDITS.md에는 사진·음악의 출처와 이용 조건을 적었습니다.','', '모든 영상의 전체 재생 데이터 검사와 음량 검사를 완료했습니다. 출처 사진 25장의 공공누리 제1유형을 개별 확인했습니다.','', '업로드·발행은 하지 않았습니다.']
(r/'README.md').write_text('\n'.join(readme),encoding='utf-8')
files=[r/name for name in ['README.md','UPLOAD_GUIDE.md','SOURCE_AUDIT.json','FINAL_QA.json','episodes.json','five-episodes-preview.jpg','preview.html']]
for e in es:
 p=r/e['slug'];files += [p/name for name in [e['slug']+'.mp4','UPLOAD_TEXT.txt','CREDITS.md','SCRIPT.md','SOURCES.json','QA.json','cover.jpg','contact-sheet.jpg','source-contact.jpg']]
 for s in json.loads((p/'SOURCES.json').read_text(encoding='utf-8')):files.append(p/'assets'/(s['id']+'.json'))
 files.append(p/'assets/collection.json')
with zipfile.ZipFile(r/'faith-places-five-upload.zip','w',compression=zipfile.ZIP_STORED) as z:
 for f in files:z.write(f,f.relative_to(r).as_posix())
print(json.dumps(audit,ensure_ascii=False,indent=2))
print('ZIP',round((r/'faith-places-five-upload.zip').stat().st_size/1024/1024,1),'MiB')
