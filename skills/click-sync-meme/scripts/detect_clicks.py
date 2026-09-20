#!/usr/bin/env python3
"""Find mouse clicks (and other sharp transients) in a clip's audio.

  detect_clicks.py VIDEO [--out clicks_raw.json] [--hp 6000] [--ratio 5] [--from S] [--to S]

Why it works: a mouse click is a ~2 ms broadband tick, so above ~6 kHz it towers over speech and room tone even
when you can barely hear it. We high-pass, take a 2 ms RMS envelope and keep peaks that exceed `ratio` x the local
median. Two peaks 80-250 ms apart are usually one click (button down + button up).
Not every transient is a click (chair creaks, a hand landing on the desk, camera shutters) — look at the video
around each time before you pin an on-screen event to it.
"""
import argparse, json, subprocess, tempfile, os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
from scipy.ndimage import median_filter

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('--out', default='clicks_raw.json')
ap.add_argument('--hp', type=float, default=6000); ap.add_argument('--ratio', type=float, default=5)
ap.add_argument('--from', dest='t0', type=float, default=0); ap.add_argument('--to', dest='t1', type=float, default=1e9)
a = ap.parse_args()

wav = tempfile.mktemp(suffix='.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-ac', '1', '-ar', '48000', wav], check=True)
sr, x = wavfile.read(wav); os.unlink(wav); x = x.astype(np.float32) / 32768
h = sosfilt(butter(4, a.hp, 'hp', fs=sr, output='sos'), x)
hop = 96                                    # 2 ms
env = np.array([np.sqrt(np.mean(h[k:k + hop] ** 2)) for k in range(0, len(h) - hop, hop)])
ratio = env / (median_filter(env, 251) + 1e-6)
peaks = [(round(k * hop / sr, 3), round(float(ratio[k]), 1)) for k in range(10, len(env) - 10)
         if ratio[k] > a.ratio and env[k] == env[k - 10:k + 11].max() and a.t0 <= k * hop / sr <= a.t1]
out = []
for i, (t, r) in enumerate(peaks):
    pair = ''
    if i + 1 < len(peaks) and 0.08 <= peaks[i + 1][0] - t <= 0.25: pair = 'down?'
    if i > 0 and 0.08 <= t - peaks[i - 1][0] <= 0.25: pair = 'up?'
    out.append(dict(t=t, strength=r, pair=pair))
json.dump(dict(video=os.path.basename(a.video), highpass_hz=a.hp, transients=out), open(a.out, 'w'), indent=1)
print(f'{len(out)} transients -> {a.out}')
for o in out: print(f"  {o['t']:8.3f}s  x{o['strength']:<6} {o['pair']}")
