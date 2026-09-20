#!/usr/bin/env python3
"""Assemble the meme: real clip on top, fake screen recording below, original audio + cloned clicks.

  build_video.py [--project DIR] [--start-frame N] [--out FILE] [--crf 17]

Top pane   = source clip, optional build/patch_<shot>.png overlaid per shot, cropped per shot (layout in clip.json)
Bottom pane= build/frames/%05d.png (one PNG per SOURCE frame, so frame k of both panes is the same instant)
Audio      = original track; for every event flagged synthetic/reinforce in build/events.json a click cloned from
             the clip's own audio (clip.json -> audio.click_samples) is mixed in, so added clicks sound like his mouse.
Trimming happens last, on the stacked video and the mixed audio together, which is why sync survives any --start-frame.
"""
import sys; sys.dont_write_bytecode = True      # keep the skill directory clean
import argparse, json, subprocess
from _common import project, clip_pack, fps_of

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--project', default='.', help='project directory (default: current dir)')
ap.add_argument('--start-frame', type=int, help='first SOURCE frame to keep (default: project.json start_frame, else the clip pack default; 0 = whole clip)')
ap.add_argument('--out', help='output file name inside the project (default: project.json out, else meme.mp4)')
ap.add_argument('--crf', type=int, default=17, help='x264 quality, lower = better/bigger (default 17)')
a = ap.parse_args()
proj, pj = project(a.project); pack, clip = clip_pack(pj['clip'], proj)
fps = fps_of(clip); FPS = clip['fps']
start = a.start_frame if a.start_frame is not None else (pj.get('start_frame') if pj.get('start_frame') is not None else clip.get('default_start_frame', 0))
out = a.out or pj.get('out', 'meme.mp4')
ev = json.loads((proj / 'build' / 'events.json').read_text())['events']
shots = clip['layout']['shots']; cw, ch = clip['layout']['crop']
import glob, cv2
first = cv2.imread(sorted(glob.glob(str(proj / 'build' / 'frames' / '*.png')))[0]); sw = first.shape[1]
th = int(round(sw * ch / cw))
if (th + first.shape[0]) % 2: th -= 1          # x264 needs an even total height

inputs = ['-i', str(proj / 'src' / 'clip.mp4'), '-framerate', FPS, '-i', str(proj / 'build' / 'frames' / '%05d.png')]
fg, last, k = [], '[0:v]', 2
for si, s in enumerate(shots):
    p = proj / 'build' / f"patch_{s['name']}.png"
    if not p.exists(): continue
    f0 = s['first_frame']; f1 = shots[si + 1]['first_frame'] if si + 1 < len(shots) else 10 ** 9
    inputs += ['-loop', '1', '-framerate', FPS, '-i', str(p)]
    fg.append(f'[{k}:v]scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuva420p[p{k}]')
    fg.append(f"{last}[p{k}]overlay=enable='between(n,{f0},{f1 - 1})':shortest=1[v{k}]"); last = f'[v{k}]'; k += 1
xexpr = str(shots[0]['crop_x'])
for s in shots[1:]: xexpr = f"if(gte(n,{s['first_frame']}),{s['crop_x']},{xexpr})"
fg.append(f"{last}crop={cw}:{ch}:x='{xexpr}':y=0,scale={sw}:{th}:flags=lanczos,setsar=1[top]")
fg.append('[1:v]scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1[bot]')
fg.append(f'[top][bot]vstack=shortest=1,trim=start_frame={start},setpts=PTS-STARTPTS,format=yuv420p[v]')

au = clip.get('audio', {}); cs = au.get('click_samples'); lead = au.get('click_sample_lead_ms', 20)
extra = [e for e in ev if e['synthetic'] or e['reinforce']]
if extra and not cs:
    print('WARNING: scene has synthetic clicks but clip.json has no audio.click_samples — they will be silent'); extra = []
t0 = start / fps
tail = f"atrim=start={t0},asetpts=N/SR/TB,afade=t=in:d=0.12,volume={au.get('gain_db', 0)}dB,alimiter=limit=0.89:level=disabled[a]"
if extra:
    kinds = {'press': [e for e in extra if e['type'] == 'press'], 'release': [e for e in extra if e['type'] == 'release']}
    fg.append(f"[0:a]asplit={1 + sum(1 for v in kinds.values() if v)}[a0]" + ''.join(f'[s_{n}]' for n, v in kinds.items() if v))
    mix = ['[a0]']
    for n, lst in kinds.items():
        if not lst: continue
        s0, s1 = cs[n]; d = s1 - s0
        fg.append(f"[s_{n}]atrim={s0}:{s1},asetpts=N/SR/TB,afade=t=in:d=0.003,afade=t=out:st={d - 0.02:.3f}:d=0.018,asplit={len(lst)}" + ''.join(f'[{n}{i}]' for i in range(len(lst))))
        for i, e in enumerate(lst):
            vol = 0.6 if e['reinforce'] else 0.9
            fg.append(f"[{n}{i}]adelay={max(0, int(round(e['t'] * 1000 - lead)))}:all=1,volume={vol}[{n}{i}d]"); mix.append(f'[{n}{i}d]')
    fg.append(''.join(mix) + f'amix=inputs={len(mix)}:normalize=0:duration=first,' + tail)
else:
    fg.append('[0:a]' + tail)

cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *inputs, '-filter_complex', ';'.join(fg), '-map', '[v]', '-map', '[a]',
       '-c:v', 'libx264', '-preset', 'slow', '-crf', str(a.crf), '-pix_fmt', 'yuv420p', '-r', FPS,
       '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
       '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(proj / out)]
subprocess.run(cmd, check=True)
(proj / 'build' / 'last_build.json').write_text(json.dumps(dict(out=out, start_frame=start, screen_h=first.shape[0], top_h=th, width=sw)))
print(f'wrote {proj / out}  ({sw}x{th + first.shape[0]}, from source frame {start}, {len(extra)} cloned click(s) mixed in)')
