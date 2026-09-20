#!/usr/bin/env python3
"""Start a meme project in a directory.

  new_project.py [--dir .] [--clip putin-vote-2026] [--video FILE] [--no-download] [--force]

With a bundled clip pack: downloads the source clip (yt-dlp) to src/clip.mp4, copies the screen template to screen/
and drops the pack's measured hand.js next to it — you can go straight to editing screen/scene.js.
With your own footage (--video FILE --clip my-name): copies the video and writes a skeleton clip/clip.json for you
to fill in while following references/new-clip.md.
"""
import argparse, json, pathlib, shutil, subprocess, sys
from _common import SKILL_DIR

ap = argparse.ArgumentParser()
ap.add_argument('--dir', default='.'); ap.add_argument('--clip', default='putin-vote-2026')
ap.add_argument('--video'); ap.add_argument('--no-download', action='store_true'); ap.add_argument('--force', action='store_true')
a = ap.parse_args()
proj = pathlib.Path(a.dir).resolve(); (proj / 'src').mkdir(parents=True, exist_ok=True); (proj / 'build').mkdir(exist_ok=True)
pack = SKILL_DIR / 'clips' / a.clip
target = proj / 'src' / 'clip.mp4'

def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames', '-of', 'json', str(path)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)['streams'][0]

if a.video:
    shutil.copy(a.video, target)
elif pack.exists() and not target.exists() and not a.no_download:
    src = json.loads((pack / 'clip.json').read_text())['source']
    print('downloading', src['url'])
    subprocess.run(['yt-dlp', '--no-update', '-q', '-f', src['format'], '--merge-output-format', 'mp4', '-o', str(target), src['url']], check=True)

if pack.exists():
    clip = json.loads((pack / 'clip.json').read_text())
    if target.exists():
        st = probe(target)
        if st['r_frame_rate'] != clip['fps'] or int(st.get('nb_frames', 0)) != clip['frames']:
            print(f"WARNING: downloaded clip is {st['r_frame_rate']} fps / {st.get('nb_frames')} frames, the pack was measured on {clip['fps']} / {clip['frames']}. "
                  'Timing data will not line up — re-run detect_clicks.py and track_hand.py (references/new-clip.md).')
else:
    if not target.exists(): sys.exit(f'unknown clip pack "{a.clip}" and no --video given')
    st = probe(target); w, h = st['width'], st['height']; cw = min(w, int(h * 1.6) // 2 * 2)
    (proj / 'clip').mkdir(exist_ok=True)
    skeleton = {
        'id': a.clip, 'title': '', 'fps': st['r_frame_rate'], 'frames': int(st.get('nb_frames', 0)), 'size': [w, h],
        'default_start_frame': 0,
        'layout': {'crop': [cw, h], 'shots': [{'name': 'main', 'first_frame': 0, 'crop_x': (w - cw) // 2}]},
        'audio': {'gain_db': 0},
        'hand_tracking': {'crop': [0, 0, w, h], 'min_score': 0.7, 'segments': []},
    }
    if not (proj / 'clip' / 'clip.json').exists() or a.force:
        (proj / 'clip' / 'clip.json').write_text(json.dumps(skeleton, indent=2))
    print('wrote skeleton clip/clip.json — follow references/new-clip.md to measure clicks and hand motion')

if not (proj / 'screen').exists() or a.force:
    shutil.copytree(SKILL_DIR / 'template', proj / 'screen', dirs_exist_ok=True)
if pack.exists() and (pack / 'hand.js').exists():
    shutil.copy(pack / 'hand.js', proj / 'screen' / 'hand.js')
pj = proj / 'project.json'
if not pj.exists() or a.force:
    pj.write_text(json.dumps({'clip': a.clip, 'start_frame': None, 'out': 'meme.mp4'}, indent=2))
print(f'project ready in {proj}\n  edit screen/scene.js (+ the app markup in screen/screen.html), then render_screen.py, make_patches.py, build_video.py, verify_sync.py')
