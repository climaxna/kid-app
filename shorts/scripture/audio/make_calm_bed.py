"""Original synthesized ambient bed; no recordings or external samples."""
from pathlib import Path
import wave
import numpy as np

SR = 44100
DURATION = 30
t = np.arange(SR * DURATION) / SR
mix = np.zeros((len(t), 2), dtype=np.float64)

# Slowly overlapping, softly voiced Cmaj7 / Am7 / Fmaj7 / C6 chords.
chords = [(0, [48, 55, 59, 64]), (7, [45, 55, 60, 64]),
          (14, [41, 52, 57, 60]), (21, [48, 55, 57, 64])]
for start, notes in chords:
    age = t - start
    env = np.where((age >= 0) & (age < 12),
                   np.sin(np.pi * np.clip(age / 12, 0, 1)) ** 2, 0)
    for j, midi in enumerate(notes):
        freq = 440 * 2 ** ((midi - 69) / 12)
        for channel, detune in enumerate([-0.0007, 0.0007]):
            phase = 2 * np.pi * freq * (1 + detune) * t + j * 0.7
            tone = np.sin(phase) + 0.13 * np.sin(2 * phase) + 0.025 * np.sin(3 * phase)
            mix[:, channel] += env * tone * 0.16

# Sparse soft bell tones, with rounded attacks rather than sharp transients.
for start, midi in [(3, 76), (10, 74), (17, 72), (24, 67)]:
    age = np.maximum(t - start, 0)
    env = (t >= start) * (1 - np.exp(-age * 9)) * np.exp(-age / 2.2)
    freq = 440 * 2 ** ((midi - 69) / 12)
    bell = env * (np.sin(2*np.pi*freq*t) + 0.12*np.sin(2*np.pi*2*freq*t))
    mix += bell[:, None] * 0.045

fade = np.minimum(np.clip(t / 2.5, 0, 1), np.clip((DURATION-t) / 4, 0, 1))
mix *= (0.5 - 0.5 * np.cos(np.pi * fade))[:, None]
mix *= 0.20 / np.max(np.abs(mix))
pcm = np.round(mix * 32767).astype('<i2')
out = Path(__file__).with_name('calm_scripture_30s.wav')
with wave.open(str(out), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
with wave.open(str(out), 'rb') as w:
    assert w.getnframes() == SR * DURATION
    assert w.getnchannels() == 2
assert np.isfinite(mix).all()
assert np.max(np.abs(pcm.astype(float))) < 32767
print(f'{out}: {DURATION}s, stereo, {SR} Hz, peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS')
