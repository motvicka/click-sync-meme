#!/usr/bin/env python3
"""Prove the result is in sync instead of eyeballing it.

  verify_sync.py [--project DIR]

1. Frame alignment: a few frames of the finished video's top pane are matched against source frames k-3..k+3;
   the best match must be the expected one (output frame k == source frame k + start_frame).
2. Click alignment: every press/release in build/events.json must have an audio transient within one video frame
   (42 ms at 24 fps) in the FINAL file. A real click that is too faint to detect shows up as "none" — consider
   reinforce:true for it in the scene.
"""
import argparse, json, subprocess, tempfile, os
import cv2, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
from scipy.ndimage import median_filter
from _common import project, clip_pack, fps_of

ap = argparse.ArgumentParser(); ap.add_argument('--project', default='.'); a = ap.parse_args()
proj, pj = project(a.project); pack, clip = clip_pack(pj['clip'], proj); fps = fps_of(clip)
lb = json.loads((proj / 'build' / 'last_build.json').read_text()); start, th, sw = lb['start_frame'], lb['top_h'], lb['width']
ev = json.loads((proj / 'build' / 'events.json').read_text())['events']
outv = str(proj / lb['out']); src = cv2.VideoCapture(str(proj / 'src' / 'clip.mp4')); res = cv2.VideoCapture(outv)
n_out = int(res.get(cv2.CAP_PROP_FRAME_COUNT)); shots = clip['layout']['shots']; cw, ch = clip['layout']['crop']
def crop_x(n):
    x = shots[0]['crop_x']
    for s in shots[1:]:
        if n >= s['first_frame']: x = s['crop_x']
    return x
def src_top(n):
    src.set(cv2.CAP_PROP_POS_FRAMES, n); ok, f = src.read(); x = crop_x(n)
    return cv2.resize(f[:ch, x:x + cw], (sw, th), interpolation=cv2.INTER_AREA)
# pick frames where the picture actually changes (a still hand matches its neighbours equally well)
speed = json.loads((proj / 'screen' / 'hand.js').read_text().split('=', 1)[1].rstrip(';\n'))['speed'] if (proj / 'screen' / 'hand.js').exists() else []
cands = sorted(range(start + 5, min(len(speed), start + n_out) - 5), key=lambda i: -speed[i])[:400:100] or [start + n_out // 2]
ok_frames = True
print('frame alignment:')
for n in cands:
    k = n - start; res.set(cv2.CAP_PROP_POS_FRAMES, k); _, f = res.read(); top = f[:th]
    errs = {m: float(np.mean(cv2.absdiff(top, src_top(m)))) for m in range(n - 3, n + 4)}
    best = min(errs, key=errs.get); ok_frames &= best == n
    print(f'  output frame {k:4d} best matches source frame {best} (expected {n})  {"OK" if best == n else "MISMATCH"}')

wav = tempfile.mktemp(suffix='.wav'); subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', outv, '-ac', '1', '-ar', '48000', wav], check=True)
sr, x = wavfile.read(wav); os.unlink(wav); x = x.astype(np.float32) / 32768
h = sosfilt(butter(4, 6000, 'hp', fs=sr, output='sos'), x); hop = 96
env = np.array([np.sqrt(np.mean(h[i:i + hop] ** 2)) for i in range(0, len(h) - hop, hop)])
ratio = env / (median_filter(env, 251) + 1e-6)
on = [i * hop / sr for i in range(10, len(env) - 10) if ratio[i] > 4 and env[i] == env[i - 10:i + 11].max()]
print('click alignment (time in the finished video):')
worst, missing = 0, 0
for e in ev:
    te = e['t'] - start / fps
    if te < 0 or te > n_out / fps: continue
    near = min(on, key=lambda o: abs(o - te)) if on else None
    d = None if near is None or abs(near - te) > 0.12 else (near - te) * 1000
    tag = 'cloned' if e['synthetic'] else ('real+' if e['reinforce'] else 'real')
    if d is None: missing += 1; print(f"  {te:7.3f}s {e['type']:8s}{e['label']:10s}{tag:7s} none within 120 ms")
    else: worst = max(worst, abs(d)); print(f"  {te:7.3f}s {e['type']:8s}{e['label']:10s}{tag:7s} audio {d:+5.0f} ms")
frame_ms = 1000 / fps
print(f'\nframes {"OK" if ok_frames else "MISALIGNED"}; worst click offset {worst:.0f} ms (one frame = {frame_ms:.0f} ms); {missing} event(s) without an audible transient')
raise SystemExit(0 if ok_frames and worst <= frame_ms else 1)
