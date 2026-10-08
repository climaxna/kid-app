from pathlib import Path
import json, html, zipfile

root=Path(__file__).parent
episodes=json.loads((root/'episodes.json').read_text(encoding='utf-8'))
qa={e['id']:e for e in json.loads((root/'QA.json').read_text(encoding='utf-8'))}
out=root/'ready-to-upload'
credit='''피아노 샘플: Salamander Grand Piano — Alexander Holm (CC BY 3.0)
https://github.com/Tonejs/audio/tree/master/salamander
https://creativecommons.org/licenses/by/3.0/
개별 음 샘플로 새 선율을 구성했으며 음높이·잔향·길이를 조정했습니다.'''
cards=[]
guide=['# 오늘 올릴 성경 쇼츠 3편','', '대상: 50대 이상 한국어권 개신교 시청자. 밝은 배경, 큰 자막, 차분한 한국어 AI 낭독, 피아노 반주.', '',
       '영상은 1080×1920 세로형, H.264/AAC MP4입니다. 직접 게시하지 않았습니다.', '',
       '## 파일과 업로드 문구','']
for ep in episodes:
    eid=ep['id']; duration=qa[eid]['duration']
    caption=f'''{ep['description']}

성경: 성경전서 개역한글판, 대한성서공회. {ep['reference']}.
{ep['source']}
성경 본문과 별도로 작성한 묵상·기도를 함께 담았습니다.
AI 생성 이미지와 AI 낭독을 사용했습니다.

{credit}

{ep['tags']}'''
    text=f"제목\n{ep['title']}\n\n설명\n{caption}\n"
    (out/f'{eid}-upload.txt').write_text(text,encoding='utf-8-sig')
    guide += [f"### {ep['title']}",'',f"- 영상: `{eid}.mp4` ({duration:.1f}초)",
              f"- 표지: `{eid}-cover.jpg`",f"- 복사용 문구: `{eid}-upload.txt`",f"- 자막 원본: `{eid}.srt`",'']
    cards.append(f'''<article>
<div class="film"><video controls playsinline preload="metadata" poster="ready-to-upload/{eid}-cover.jpg" aria-label="{html.escape(ep['title'])}"><source src="ready-to-upload/{eid}.mp4" type="video/mp4"></video></div>
<div class="details"><span class="reference">{html.escape(ep['reference'])} · {duration:.1f}초</span><h2>{html.escape(ep['title'])}</h2>
<p>{html.escape(ep['description'])}</p><a class="download" download href="ready-to-upload/{eid}.mp4">영상 저장</a> <a download href="ready-to-upload/{eid}-cover.jpg">표지 저장</a>
<label for="title-{eid}">제목</label><input id="title-{eid}" value="{html.escape(ep['title'])}" readonly><button data-copy="title-{eid}">제목 복사</button>
<label for="caption-{eid}">설명과 출처</label><textarea id="caption-{eid}" readonly>{html.escape(caption)}</textarea><button data-copy="caption-{eid}">설명 복사</button>
</div></article>''')
guide += ['## 게시 순서','',
          '1. 영상 3편을 재생해 목소리와 배경음의 균형을 확인합니다.',
          '2. 각 MP4를 클립에 업로드하고 해당 upload.txt의 제목·설명·태그를 복사합니다.',
          '3. 음악 출처 문구는 설명에 그대로 유지합니다. 플랫폼에 AI 제작 여부 입력 항목이 있으면 표시합니다.',
          '4. 별도 배경음악을 추가하지 않아도 됩니다. 영상에 음악과 낭독이 이미 들어 있습니다.',
          '5. 플랫폼이 자동 자막을 추가했다면 내장 자막과 겹치지 않는지 확인합니다. SRT는 보관용으로도 제공하며, 추가 업로드는 필수가 아닙니다.',
          '', '## 확인 범위','',
          '- 성경 인용문은 개역한글 자료와 대조. 개역개정과 섞지 않았습니다.',
          '- 낭독 입력과 분할된 성경 자막을 합쳐 전체 구절 일치 확인.',
          '- 자막 폭, 글자 크기, 음성·자막 시간, 오디오 피크, 전체 영상 디코딩 검사 완료.',
          '- 대표 화면을 직접 시각 검수했습니다. 음성 자연스러움은 최종 재생에서 확인해 주세요.',
          '- 성경 본문: https://www.bskorea.or.kr/bbs/board.php?bo_table=copyright_faq&wr_id=5',
          '- 피아노 샘플 출처: 위 설명에 명시. 곡 구성과 영상 편집은 이 프로젝트에서 새로 제작.',
          '', '## 반응 기록','',
          '게시 후 같은 경과 시간에 조회수·좋아요·저장·댓글·팔로우 변화를 기록합니다. 제공되지 않는 지표는 비워 둡니다.',
          '', '| 영상 | 게시 시각 | 24시간 조회수 | 좋아요 | 저장 | 댓글 | 팔로우 변화 |',
          '|---|---|---|---|---|---|---|',
          '| 잠들기 전 위로 | | | | | | |',
          '| 자녀 걱정 | | | | | | |',
          '| 지친 하루 | | | | | | |']
(root/'UPLOAD_GUIDE.md').write_text('\n'.join(guide)+'\n',encoding='utf-8')
(out/'README.txt').write_text('업로드할 파일은 MP4 3개입니다. 각 upload.txt에 제목, 설명, 출처와 태그가 있습니다.\n음악 출처를 설명에 유지해주세요. 표지 JPG와 자막 SRT도 함께 제공합니다.\n영상은 생성 이미지와 AI 낭독을 사용했으며, 아직 게시하지 않았습니다.\n',encoding='utf-8-sig')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>하루 한 말씀 · 첫 3편</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f4f0e7;color:#302f27;font-family:"Malgun Gothic",sans-serif}main{max-width:1120px;margin:auto;padding:40px 24px}h1{font-size:36px;margin:10px 0}header p{line-height:1.8;color:#625f54}header{margin-bottom:36px}.eyebrow,.reference{color:#53674b;font-weight:bold}article{display:grid;grid-template-columns:300px 1fr;gap:32px;padding:26px;background:#fffdf7;border:1px solid #ddd5c4;border-radius:18px;margin:24px 0}.film video{width:100%;max-height:600px;display:block;background:#ddd4c2;border-radius:9px}h2{font-size:25px;line-height:1.5}.details p{line-height:1.8}label{display:block;font-weight:bold;margin:20px 0 8px}input,textarea{display:block;width:100%;padding:12px;border:1px solid #c8c3b7;background:#fcfaf4;border-radius:6px;font-family:inherit;font-size:15px}textarea{height:150px;line-height:1.6}button,.download{display:inline-block;padding:10px 16px;border:0;border-radius:6px;background:#43593b;color:white;cursor:pointer;text-decoration:none;font-size:15px;margin:10px 8px 0 0}a{color:#43593b}#status{position:fixed;bottom:20px;right:20px;background:#30432b;color:white;padding:12px 20px;border-radius:8px;display:none}footer{line-height:1.8;color:#625f54}@media(max-width:700px){article{grid-template-columns:1fr;padding:18px}.film{max-width:310px;margin:auto}main{padding:24px 14px}h1{font-size:28px}}</style>
<main><header><span class="eyebrow">하루 한 말씀 · 첫 3편</span><h1>오늘 전할 말씀과 기도</h1><p>큰 글씨 · 한국어 낭독 · 따뜻한 피아노<br>영상에 자막과 음악이 포함되어 있습니다. 재생 후 제목과 설명을 복사해 업로드하세요.</p><a class="download" download href="scripture-pilot-3-videos.zip">3편 한 번에 저장</a></header>'''+''.join(cards)+'''<footer>성경 본문과 직접 작성한 기도를 구분했습니다. 음악 출처 문구는 게시 설명에 유지해 주세요.<br>AI 생성 이미지 · AI 낭독. 공개 게시 전 최종 재생을 권합니다.</footer></main><div id="status" role="status"></div>
<script>document.querySelectorAll('button[data-copy]').forEach(b=>b.addEventListener('click',async()=>{let e=document.getElementById(b.dataset.copy);try{await navigator.clipboard.writeText(e.value)}catch(_){e.select();document.execCommand('copy')}let s=document.getElementById('status');s.textContent='복사했습니다';s.style.display='block';setTimeout(()=>s.style.display='none',2000)}));document.querySelectorAll('video').forEach(v=>v.addEventListener('play',()=>document.querySelectorAll('video').forEach(o=>{if(o!==v)o.pause()})));</script></html>'''
(root/'preview.html').write_text(page,encoding='utf-8')
with zipfile.ZipFile(root/'scripture-pilot-3-videos.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(out.iterdir()):
        z.write(f,'ready-to-upload/'+f.name)
    z.write(root/'preview.html','preview.html')
    z.write(root/'UPLOAD_GUIDE.md','UPLOAD_GUIDE.md')
print('Packaged 3 videos, covers, captions and upload text.')
