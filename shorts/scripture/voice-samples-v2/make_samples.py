from pathlib import Path
import json, subprocess
import numpy as np
import soundfile as sf
import imageio_ffmpeg
from supertonic import TTS

root=Path(__file__).parent
text='두려워 말라 내가 너와 함께 함이니라. 놀라지 말라 나는 네 하나님이 됨이니라.'
tts=TTS(auto_download=True)
results=[]
for label,voice in [('A','M1'),('B','M2'),('C','M3')]:
    print('Generating '+label+' '+voice,flush=True)
    wav,duration=tts.synthesize(text=text,voice_style=tts.get_voice_style(voice_name=voice),
                               total_steps=12,speed=0.90,lang='ko',silence_duration=0.9)
    target=root/f'{label}-{voice}.wav'
    tts.save_audio(wav,str(target))
    a,sr=sf.read(target)
    assert len(a)>sr*3 and np.isfinite(a).all()
    peak=np.max(np.abs(a))
    a=a*(0.80/peak)
    sf.write(target,a,sr,subtype='PCM_24')
    mp3=target.with_suffix('.mp3')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-v','error','-i',str(target),'-c:a','libmp3lame','-b:a','192k',str(mp3)],check=True)
    results.append({'label':label,'voice':voice,'seconds':len(a)/sr,'sample_rate':sr,'engine':'Supertonic','speed':0.90,'steps':12})
    print(results[-1],flush=True)
(root/'samples.json').write_text(json.dumps({'text':text,'samples':results,'note':'Preset voices; no voice cloning or reference audio upload. No music or effects. Direct listening assessment not performed.'},ensure_ascii=False,indent=2),encoding='utf-8')
