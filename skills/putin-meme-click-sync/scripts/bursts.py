#!/usr/bin/env python3
"""How far did the real hand travel, and so how far may the fake cursor plausibly go?

  bursts.py [--project DIR]                      list every movement burst in screen/hand.js
  bursts.py --windows 7.15-7.6 19.44-20.17       hand travel inside the time windows you plan to use for moves

"cursor budget" = hand px x 9..15 (what one source pixel of hand travel is worth on a 1080-px-wide fake screen).
Staying inside it keeps small hand movements from carrying the cursor across the whole screen, which is the most
common way these videos stop looking real. Lay out the fake UI AFTER looking at this, so targets are reachable.
"""
import argparse, json, pathlib
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--project', default='.', help='project directory (default: current dir)')
ap.add_argument('--windows', nargs='*', help='t0-t1 pairs in source-clip seconds')
a = ap.parse_args()
H = json.loads((pathlib.Path(a.project) / 'screen' / 'hand.js').read_text().split('=', 1)[1].rstrip(';\n'))
fps, sp = H['fps'], H['speed']; N = len(sp)
def row(t0, t1):
    px = sum(sp[max(0, int(t0 * fps) + 1):min(N, int(round(t1 * fps)) + 1)])
    note = 'hand practically still -> engine eases; keep travel short' if px < 0.8 else ''
    print(f'  {t0:6.2f}-{t1:6.2f}s  hand {px:5.1f} px   cursor budget ~{px * 9:4.0f}-{px * 15:4.0f} px   {note}')
if a.windows:
    for w in a.windows: t0, t1 = map(float, w.split('-')); row(t0, t1)
else:
    i = 0
    while i < N:
        if sp[i] > 0:
            j = i
            while j < N and (sp[j] > 0 or any(v > 0 for v in sp[j + 1:j + 3])): j += 1
            if sum(sp[i:j]) > 0.6: row(i / fps, j / fps)
            i = j
        else: i += 1
