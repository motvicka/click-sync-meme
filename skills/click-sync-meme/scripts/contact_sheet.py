#!/usr/bin/env python3
"""Timestamped tile sheet of a clip, so you can SEE what happens when (Read the resulting JPG).

  contact_sheet.py VIDEO OUT.jpg [--fps 1] [--from 0] [--to END] [--crop x:y:w:h] [--cols 6] [--width 480]

Typical use: whole clip at 1 fps for the story beats, then 4-6 fps with --crop around the hand for the moments
where the hand leaves or returns to the mouse.
"""
import argparse, math, subprocess, json
ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('out')
ap.add_argument('--fps', type=float, default=1); ap.add_argument('--from', dest='t0', type=float, default=0); ap.add_argument('--to', dest='t1', type=float)
ap.add_argument('--crop'); ap.add_argument('--cols', type=int, default=6); ap.add_argument('--width', type=int, default=480)
a = ap.parse_args()
dur = float(json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', a.video], capture_output=True, text=True).stdout)['format']['duration'])
t1 = min(a.t1 or dur, dur); n = max(1, int(math.ceil((t1 - a.t0) * a.fps))); rows = math.ceil(n / a.cols)
vf = [f'fps={a.fps}'] + ([f'crop={a.crop}'] if a.crop else []) + [f'scale={a.width}:-1',
      f"drawtext=text='%{{pts\\:hms\\:{a.t0}}}':x=6:y=6:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6", f'tile={a.cols}x{rows}']
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.t0), '-t', str(t1 - a.t0), '-i', a.video, '-vf', ','.join(vf), '-frames:v', '1', '-q:v', '3', a.out], check=True)
print(f'{n} tiles ({a.cols}x{rows}) -> {a.out}')
