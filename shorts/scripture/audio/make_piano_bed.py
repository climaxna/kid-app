"""Original piano composition using CC BY 3.0 Salamander piano notes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
import json
import subprocess
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve
import imageio_ffmpeg

ROOT = Path(__file__).parent
CACHE = ROOT / 'piano_samples'
CACHE.mkdir(exist_ok=True)
SR, SECONDS = 44100, 30
B = 60 / 72
rng = np.random.default_rng(8421)
keys = {'C2':36, 'Fs2':42, 'A2':45, 'C3':48, 'Ds3':51, 'Fs3':54,
        'A3':57, 'C4':60, 'Ds4':63, 'Fs4':66, 'A4':69, 'C5':72}

def fetch(name):
    target = CACHE / (name + '.mp3')
    if not target.exists():
        data = urlopen('https://tonejs.github.io/audio/salamander/' + name + '.mp3', timeout=45).read()
        target.write_bytes(data)
    data, rate = sf.read(target, always_2d=True)
    if rate != SR:
        data = resample_poly(data, SR, rate)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    return keys[name], data[:, :2]

with ThreadPoolExecutor(max_workers=5) as pool:
    samples = dict(pool.map(fetch, keys))

mix = np.zeros((SR * SECONDS, 2))
notes = []
rendered = {}

def note(beat, midi, velocity, sustain):
    # Nearest recorded note; slight resampling preserves authentic hammer attack.
    if midi not in rendered:
        source = min(samples, key=lambda k: abs(k-midi))
        ratio = 2 ** ((midi-source)/12)
        rendered[midi] = resample_poly(samples[source], 10000, round(10000*ratio))
    sample = rendered[midi]
    duration = min(len(sample)/SR, sustain*B+1.15)
    audio = sample[:int(duration*SR)].copy()
    age = np.arange(len(audio))/SR
    release = np.clip((age-sustain*B)/1.15, 0, 1)
    env = np.cos(release*np.pi/2)**2
    env *= np.minimum(age/0.003, 1)
    audio *= env[:,None] * velocity
    start_time = max(0, 0.12 + beat*B + rng.uniform(-0.013, 0.013))
    start = int(start_time*SR)
    count = min(len(audio),len(mix)-start)
    if count > 0:
        mix[start:start+count] += audio[:count]
    notes.append(dict(beat=beat,midi=midi,velocity=velocity,sustain=sustain))

# Eight quiet bars: Cmaj9 - G/B - Am7 - Fmaj7 - C/E - Dm7 - Gsus/G - C.
voicings = [(36,[55,60,64]), (35,[55,59,62]), (33,[52,57,60]), (29,[53,57,60]),
            (40,[55,60,64]), (38,[53,57,60]), (31,[55,60,62]), (36,[55,60,64])]
for bar,(bass,chord) in enumerate(voicings):
    pos = bar*4
    note(pos,bass,0.34,3.9)
    for offset,pitch in zip([0.5,1.5,2.5],chord):
        note(pos+offset,pitch,0.22+rng.uniform(-0.025,0.025),2.1)
    if bar not in [3,7]:
        note(pos+3.25,chord[1],0.16,1.2)

# An original restrained melody, with breathing room at the end of each phrase.
melody = [(0,67,1.4),(1.5,71,0.9),(2.5,69,1.2),
          (4,67,1.9),(6.5,62,1.1),
          (8,64,1.4),(9.5,67,0.9),(10.5,69,1.3),
          (12,67,1.4),(13.5,64,2.0),
          (16,67,1.4),(17.5,72,1.2),(19,71,0.8),
          (20,69,1.4),(21.5,65,1.5),
          (24,67,1.4),(25.5,65,0.9),(26.5,62,1.2),
          (28,64,1.1),(29.25,60,3.6)]
for beat,pitch,length in melody:
    note(beat,pitch,0.46+rng.uniform(-0.035,0.035),length)

# Subtle dark room reverb, rather than a prominent synth pad or echo.
dry = sosfilt(butter(2, 4600, fs=SR, output='sos'),mix,axis=0)
reverb = np.zeros_like(dry)
for channel in range(2):
    size = int(1.7*SR)
    times = np.arange(size)/SR
    impulse = rng.normal(size=size)*np.exp(-times/0.32)
    impulse[:int(0.028*SR)] = 0
    impulse = sosfilt(butter(2,2800,fs=SR,output='sos'),impulse)
    impulse /= np.sqrt(np.sum(impulse**2))
    reverb[:,channel] = fftconvolve(dry[:,channel],impulse)[:len(dry)]
mix = dry + 0.075*reverb
time = np.arange(len(mix))/SR
fade = np.minimum(np.clip(time/0.035,0,1),np.clip((SECONDS-time)/2.8,0,1))
mix *= (np.sin(fade*np.pi/2)**2)[:,None]
mix *= 10**(-3/20)/np.max(np.abs(mix))

wav = ROOT / 'piano_prayer_30s_v2.wav'
mp3 = ROOT / 'piano_prayer_30s_v2.mp3'
sf.write(wav,mix,SR,subtype='PCM_24')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-i',str(wav),
                '-codec:a','libmp3lame','-b:a','192k',str(mp3)],check=True)
check,rate = sf.read(wav)
assert len(check)==SR*SECONDS and np.isfinite(check).all()
assert np.max(np.abs(check))<1
metrics = {'seconds':len(check)/rate,'sample_rate':rate,'channels':check.shape[1],
           'peak_dbfs':float(20*np.log10(np.max(np.abs(check)))),
           'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(check**2)))),
           'note_count':len(notes),'tempo_bpm':72,
           'validation':'File and signal checks only; not a listening review.'}
(ROOT/'piano_prayer_30s_v2.json').write_text(json.dumps({'metrics':metrics,'notes':notes},indent=2),encoding='utf-8')
print(json.dumps(metrics,indent=2))
print(mp3)
