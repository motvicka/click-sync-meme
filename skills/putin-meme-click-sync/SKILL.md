---
name: putin-meme-click-sync
description: Putin meme generator — make a "what is he really doing on that computer" meme video. Real footage of someone using a mouse on top (bundled and fully measured: Putin voting online from the Kremlin, Sept 2026), a fake screen recording underneath whose cursor moves, clicks and drags are frame-accurately synchronised with the person's real hand movement and audible mouse clicks. Ships with a fully measured clip (Putin voting online, Sept 2026 — click times, per-frame hand motion, monitor corners, watermark removal) so a new meme only needs a new fake screen. Use this whenever the user wants a split-screen / fake-screen / "what's on his monitor" meme, wants to sync an animation to mouse clicks or hand movement in a video, mentions the Putin voting clip, or asks to remake/parody such a video with their own text, poster, app or joke — even if they just say "udělej mi video kde Putin kliká na ..." or "make him do X on the computer".
---

# putin-meme-click-sync

A Putin meme generator (and, with your own footage, a generator for anyone filmed using a mouse). The result is a vertical (4:5) video: the real clip on top, a fake screen recording below. It is funny only if it is
believable, and it is believable only if the fake cursor moves **when the real hand moves** and things happen on
screen **on the audible clicks**. Everything in this skill serves that.

Core idea: you script *where* the cursor goes; *when* and how fast it moves inside each time window is taken from the
measured speed of the real hand, frame by frame. Clicks are pinned to real audio transients. Where your story needs a
click that the microphone did not catch, a click cloned from the clip's own audio is mixed in.

`SKILL` below means this skill's base directory (shown when the skill loads). `PY` is the venv python from setup.

## 0. Setup (once)

```bash
sh "$SKILL/scripts/setup.sh"          # venv with numpy/scipy/opencv/playwright + headless Chromium; needs ffmpeg, yt-dlp
PY=~/.cache/putin-meme-click-sync/venv/bin/python
```

## 1. Start a project

```bash
$PY "$SKILL/scripts/new_project.py" --project <empty dir>        # bundled clip: putin-vote-2026
```
This downloads the clip to `src/clip.mp4`, copies the screen template to `screen/` and puts the clip's measured
`hand.js` next to it. Every script takes `--project DIR` (default: current directory) and has a real `--help`. Using different footage? Read `references/new-clip.md` first — you must measure it before
anything else makes sense.

## 2. Learn the clip before writing the story

Read `clips/<id>/beats.md` (what the person does, second by second) and `clips/<id>/clicks.json` (audible clicks and
what each is good for). The story must be written **around** these — you cannot move them:

- every audible click needs something visible happening on it (a selection appears, a button does something, an object
  drops). A loud click with nothing happening reads as out of sync just as much as a silent action does;
- the cursor may only travel while the hand moves, and must freeze while the hand is off the mouse;
- the last click before the "satisfied" reaction must complete the job, and the screen must sit in its final state
  for a second or two before the reaction;
- reaction beats (leaning in, gesturing) are gifts: make sure what is on screen at that moment deserves the reaction.

Before laying anything out, check how far the cursor can plausibly travel in each window you intend to use:
```bash
$PY "$SKILL/scripts/bursts.py" --windows 7.15-7.6 8.84-9.55 25.3-26.6      # or no --windows: list every burst
```
Small hand movements can only carry the cursor a short way, and that decides where buttons and targets must sit.

Then tell the user the plan as a short table (time → what he does → what happens on screen) before building it.
It is cheap to change at this point and expensive later.

## 3. Build the fake screen

`screen/screen.html` is a plain 1080x675 web page (rendered at 1x on purpose — it should look like a real low-DPI
screen capture). `screen/engine.js` is generic and stays untouched. **`screen/scene.js` is yours**: the bundled one is a
complete worked example (a fake MS Paint in which an ugly flyer gets rearranged) — keep its structure, replace its
content. Replace the app markup in `screen.html` with whatever app the joke needs.

Read `references/choreography.md` before writing `moves`/`events`; it explains the engine API and the rules of thumb
that make the result feel real (drag = press + moves + release, lazy targets, `prof:'ease'` where tracking is blind,
where to put UI so that both clicks of a double click land on it, synthetic vs. reinforced clicks).

Preview often, look at the PNGs, fix, repeat:
```bash
$PY "$SKILL/scripts/render_screen.py" --events                 # frame after every press/release (+ one before each press)
$PY "$SKILL/scripts/render_screen.py" --times 20.2 33.0        # any other moment, e.g. the extremes of a drag  -> build/preview/NNNNN.png
```
Check at least one frame per event, and the extremes of every drag.

What the engine needs from `screen.html` is marked `REQUIRED BY ENGINE` in the template (`#cursor`, `#ripples` and their
CSS, `cursor:none`, the fixed 1080x675 `#screen`, script order `hand.js` → `engine.js` → `scene.js`); the rest is the example app.
Text for the viewer ("VYHRÁL JSI!", captions) belongs inside the fake screen — there is no overlay on the real-footage pane.

## 4. Render, patch, assemble, verify

```bash
$PY "$SKILL/scripts/render_screen.py"      # all frames -> build/frames, build/events.json, build/final_screen.png
$PY "$SKILL/scripts/make_patches.py"       # watermark removal + your final screen on the real monitor (if the clip pack defines them)
$PY "$SKILL/scripts/build_video.py"        # -> meme.mp4 (1080x1350). --start-frame N to keep/cut the intro
$PY "$SKILL/scripts/verify_sync.py"        # exit 0 + last line like: frames OK; worst click offset 33 ms (one frame = 42 ms); 0 event(s) without an audible transient
```
Look at `build/patch_*_preview.jpg` and at a few frames of the finished video (`ffmpeg -ss T -i meme.mp4 -frames:v 1 x.png`)
yourself before showing it — especially the final shot with the composited monitor.

`verify_sync.py` is the acceptance test: it matches output frames back to source frames and measures the distance
between every scripted press/release and the nearest audio transient **in the finished file**. It passes when every
matched frame is the expected one and the worst click offset is at most one video frame; `real` / `real+` / `cloned`
in its table say whether the sound is the clip's own click, a reinforced one, or a synthetic one. Report its numbers to
the user rather than saying "it should be in sync". If it fails, the usual causes are an event time that is not on a
transient (check `clicks.json`), or a synthetic click without `synthetic:true`.

## Things that bite

- **Phones and sound.** The clip's audio after the voice-over is room tone plus clicks. It is there, but quiet; people
  watching muted will not notice clicks at all, so the visual click ripple (built into the engine) matters.
- **Fonts.** The template uses Comic Sans MS, Times New Roman, Tahoma (present on macOS/Windows). On Linux install
  `ttf-mscorefonts-installer` or swap fonts, otherwise text widths and therefore positions change.
- **Tweaking a bundled clip pack** (different crop, monitor quad, start frame): copy `clips/<id>/` to `<project>/clip/` and
  edit there — a project-local `clip/clip.json` wins over the bundled one. `project.json` holds `start_frame` and `out`.
- **Monitor composite covers the whole panel**, so your fake screen's own taskbar/dock replaces the real one. If you measure
  a monitor yourself, remember a dark taskbar is not part of the lit area (`find_screen_quad.py --dark-bottom`).
- **Do not re-encode or re-time the source** before measuring or building; all data is indexed by source frame number.
  `new_project.py` warns if the download's fps/frame count differs from the pack.
- **The clip itself is not in this repo** (third-party footage); it is downloaded on demand. If the URL dies, any copy of
  the same footage works after re-measuring (`references/new-clip.md`).
- This is satire about public figures' footage. Keep it obviously a joke: do not make fake screens that impersonate
  real documents, ballots, bank or login pages, or that could pass as evidence of something the person did.

## Files

| path | what |
|---|---|
| `scripts/new_project.py` | project scaffold + clip download |
| `scripts/contact_sheet.py` | timestamped tile sheet of any part of a clip — how you *see* the beats |
| `scripts/bursts.py` | hand travel per burst / per planned window → how far the cursor may go |
| `scripts/detect_clicks.py` | audible clicks from the audio track |
| `scripts/track_hand.py` | per-frame hand position/speed → `hand.js` |
| `scripts/find_screen_quad.py` | corners of a real monitor in a shot |
| `scripts/render_screen.py` · `make_patches.py` · `build_video.py` · `verify_sync.py` | the pipeline |
| `template/` | `screen.html`, `engine.js` (generic), `scene.js` (example story) |
| `clips/putin-vote-2026/` | `clip.json` (all measured geometry/timing config), `beats.md`, `clicks.json`, `hand.js`, `track.json` |
| `references/choreography.md` | engine API + how to write a believable cursor script |
| `references/new-clip.md` | measuring your own footage |
