#!/usr/bin/env python3
"""Render the fake screen (screen/screen.html) frame by frame with headless Chromium.

  render_screen.py [--project DIR] [--size 1080x675]                 all frames
  render_screen.py --events                                          previews: the frame after every press/release (+ 1 frame before each press)
  render_screen.py --times 7.7 20.2 33.0 | --frames 185 484 792      previews at source-clip seconds / frame numbers

Writes build/frames/NNNNN.png, build/events.json (the scene's press/release list, used by build_video.py
and verify_sync.py) and build/final_screen.png (last frame, used for the on-monitor composite).
Preview modes write to build/preview/ (named by frame number) and leave build/frames alone.
"""
import argparse, json, pathlib, sys
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--project', default='.', help='project directory (default: current dir)')
ap.add_argument('--size', default='1080x675', help='viewport of screen.html (default 1080x675 = 16:10, matches the top pane)')
ap.add_argument('--frames', nargs='*', type=int, help='preview these source frame numbers')
ap.add_argument('--times', nargs='*', type=float, help='preview these source-clip seconds')
ap.add_argument('--events', action='store_true', help='preview around every scripted press/release')
a = ap.parse_args()
proj = pathlib.Path(a.project).resolve()
w, h = map(int, a.size.split('x'))
page_url = (proj / 'screen' / 'screen.html').as_uri()
preview = bool(a.frames or a.times or a.events)
out = proj / 'build' / ('preview' if preview else 'frames'); out.mkdir(parents=True, exist_ok=True)
if not preview:
    for f in out.glob('*.png'): f.unlink()

errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport=dict(width=w, height=h), device_scale_factor=1)
    pg.on('console', lambda m: print('console:', m.text))
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(page_url)
    try:
        pg.wait_for_function('window.READY === true', timeout=30000)
    except Exception:
        sys.exit('screen.html never set window.READY — page errors: ' + ('; '.join(errors) or 'none (did Engine.run() get called?)'))
    n = pg.evaluate('HAND.n')
    (proj / 'build' / 'events.json').write_text(json.dumps(dict(fps=pg.evaluate('HAND.fps'), frames=n, events=pg.evaluate('window.EVENTS')), indent=1))
    fps = pg.evaluate('HAND.fps'); todo = range(n)
    if preview:
        want = set(a.frames or []) | {round(t * fps) for t in (a.times or [])}
        if a.events:
            for e in pg.evaluate('window.EVENTS'):
                f = round(e['t'] * fps); want |= {f + 1} | ({f - 1} if e['type'] == 'press' else set())
        todo = sorted(f for f in want if 0 <= f < n)
    for i in todo:
        pg.evaluate(f'renderFrame({i})')
        pg.screenshot(path=str(out / f'{i:05d}.png'), clip=dict(x=0, y=0, width=w, height=h))
    if not preview:
        pg.evaluate(f'renderFrame({n - 1})')
        pg.screenshot(path=str(proj / 'build' / 'final_screen.png'), clip=dict(x=0, y=0, width=w, height=h))
    b.close()
if errors: print('page errors:', errors)
print(f'rendered {len(list(todo))} frame(s) -> {out}')
