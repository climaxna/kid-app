from pathlib import Path
from supertonic import TTS
root=Path(__file__).parent
source=(root/'build_five.py').read_text(encoding='utf-8').split('template=')[0]
exec(compile(source,str(root/'build_five.py'),'exec'))
tts=TTS(auto_download=False)
style=tts.get_voice_style(voice_name='M2')
for ep in episodes:
 work=root/ep['slug'];work.mkdir(exist_ok=True)
 for i,(kind,text,display) in enumerate(ep['rows']):
  path=work/f'voice-{i}.wav'
  if not path.exists():
   wav,_=tts.synthesize(text=text,voice_style=style,total_steps=12,speed=.90,lang='ko')
   tts.save_audio(wav,str(path))
 print(ep['slug']+' narration ready',flush=True)
