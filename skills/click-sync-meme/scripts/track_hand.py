#!/usr/bin/env python3
"""Measure how the hand on the mouse moves, frame by frame.

  track_hand.py [--project DIR] [--video FILE]

Reads the `hand_tracking` block of the clip pack:
  crop      [x0,y0,x1,y1]   region of the frame that contains hand + mouse in every posture
  segments  one entry per posture: {name, t0, t1, tref, box:[x0,y0,x1,y1] (inside crop), valid:[t0,t1]}
            the template is cut from the frame at `tref`; it is then matched in every frame of t0..t1
  min_score frames matching worse than this (hand lifted, occluded) hold the last good position

Why templates per posture: normalised template matching gives an ABSOLUTE position (no optical-flow drift) with
~0.1 px precision, but only while the hand looks the same. When the person leans in or re-grips, start a new segment.

Writes (into the project's clip/ dir, or next to the clip pack when run with --pack-out):
  track.json  per-frame x,y,score per segment
  hand.js     `const HAND = {fps, n, speed[]}` — px the hand moved between consecutive frames; this paces the fake cursor
and prints the movement bursts, which become the time windows of your cursor moves.
"""
import sys; sys.dont_write_bytecode = True      # keep the skill directory clean
import argparse, json, pathlib
import cv2, numpy as np
from scipy.ndimage import gaussian_filter1d
from _common import project, clip_pack

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--project', default='.', help='project directory (default: current dir)')
ap.add_argument('--video', help='video to measure (default: <project>/src/clip.mp4)')
ap.add_argument('--out', help='output directory for track.json and hand.js (default: <project>/clip)')
a = ap.parse_args()
proj, pj = project(a.project); pack, clip = clip_pack(pj['clip'], proj)
cfg = clip['hand_tracking']; video = a.video or str(proj / 'src' / 'clip.mp4')
out = pathlib.Path(a.out) if a.out else proj / 'clip'; out.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS)
cx0, cy0, cx1, cy1 = cfg['crop']; frames = []
while True:
    ok, fr = cap.read()
    if not ok: break
    frames.append(cv2.cvtColor(fr[cy0:cy1, cx0:cx1], cv2.COLOR_BGR2GRAY))
N = len(frames)

def sub(l, c, r):
    d = l - 2 * c + r; return 0.0 if abs(d) < 1e-9 else float(0.5 * (l - r) / d)
segs = {}
for s in cfg['segments']:
    x0, y0, x1, y1 = s['box']; tpl = frames[int(s['tref'] * fps)][y0:y1, x0:x1]; rows = []
    for i in range(int(s['t0'] * fps), min(N - 1, int(s['t1'] * fps)) + 1):
        g = frames[i][max(0, y0 - 70):y1 + 70, max(0, x0 - 90):x1 + 90]
        res = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED); _, sc, _, (x, y) = cv2.minMaxLoc(res)
        sx = sub(res[y, x - 1], res[y, x], res[y, x + 1]) if 0 < x < res.shape[1] - 1 else 0
        sy = sub(res[y - 1, x], res[y, x], res[y + 1, x]) if 0 < y < res.shape[0] - 1 else 0
        rows.append(dict(t=round(i / fps, 3), x=round(float(x + sx - min(90, x0)), 2), y=round(float(y + sy - min(70, y0)), 2), s=round(float(sc), 3)))
    segs[s['name']] = rows
(out / 'track.json').write_text(json.dumps(dict(fps=fps, segs=segs)))

speed = np.zeros(N)
for s in cfg['segments']:
    t0, t1 = s['valid']; rows = [r for r in segs[s['name']] if t0 <= r['t'] <= t1]
    x = np.array([r['x'] for r in rows]); y = np.array([r['y'] for r in rows]); ok = np.array([r['s'] for r in rows]) > cfg.get('min_score', 0.7)
    for i in range(1, len(x)):
        if not ok[i]: x[i], y[i] = x[i - 1], y[i - 1]
    v = np.hypot(np.diff(gaussian_filter1d(x, 1.0)), np.diff(gaussian_filter1d(y, 1.0))); v[v < 0.10] = 0     # below 0.1 px/frame is tracker noise
    f0 = int(round(rows[0]['t'] * fps)); speed[f0 + 1:f0 + 1 + len(v)] = v
(out / 'hand.js').write_text('const HAND = ' + json.dumps(dict(fps=fps, n=N, speed=[round(float(v), 3) for v in speed])) + ';\n')

print(f'{N} frames @ {fps:.3f} fps -> {out}/track.json, {out}/hand.js\nmovement bursts (candidate windows for cursor moves):')
act = speed > 0; i = 0
while i < N:
    if act[i]:
        j = i
        while j < N and (act[j] or (j + 2 < N and act[j + 1:j + 3].any())): j += 1
        if speed[i:j].sum() > 0.6: print(f'  {i / fps:6.2f}-{j / fps:6.2f}s  path {speed[i:j].sum():5.1f} px')
        i = j
    else: i += 1
