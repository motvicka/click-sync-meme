# Measuring your own footage

Good candidates: locked-off camera, the mouse hand visible, natural sound (no music bed), one or two shots.
A later shot that shows the person's real monitor is a bonus for the punchline.

```bash
$PY "$SKILL/scripts/new_project.py" --video my.mp4 --clip my-clip     # copies the video, writes clip/clip.json skeleton
```
A project-local clip pack (`clip/clip.json`, `clip/hand.js`, …) has the same format as `clips/putin-vote-2026/` —
use that pack's `clip.json` as the reference for every field mentioned below.

## 1. Look at it
```bash
$PY "$SKILL/scripts/contact_sheet.py" src/clip.mp4 build/sheet.jpg                      # whole clip, 1 fps
$PY "$SKILL/scripts/contact_sheet.py" src/clip.mp4 build/hand.jpg --fps 4 --from 12 --to 19 --crop 1300:800:0:280
```
Read the JPGs. Write down: shot changes (frame numbers), when the hand is on/off the mouse, posture changes
(leaning in, sitting back), reactions, and where a broadcaster logo or caption sits. This becomes your `beats.md`.
Decide `default_start_frame` (skip voice-overs and captions) and the `layout` (16:10 crop window per shot, so the top
pane matches a 1080x675 fake screen; choose `crop_x` per shot so the person and, if present, the monitor stay in frame).

## 2. Clicks
```bash
$PY "$SKILL/scripts/detect_clicks.py" src/clip.mp4 --out clip/clicks_raw.json
```
Clicks are ~2 ms broadband ticks: above 6 kHz they stand far above speech and room tone, even when barely audible.
Pairs 80–250 ms apart are button down + up. Check each against the picture — hands landing on desks, chairs and camera
shutters also tick. Pick one loud clean pair as `audio.click_samples` (start ~12 ms before the transient, ~70 ms long);
it is what synthetic clicks are cloned from. If the useful part of the clip is quiet, set `audio.gain_db`.

## 3. Hand motion
Fill `hand_tracking` in `clip/clip.json`:
- `crop`: a region containing hand + mouse in every posture (keeps matching fast);
- one `segment` per posture: `tref` = a moment when the hand rests on the mouse in that posture, `box` = tight rectangle
  around mouse + knuckles **inside the crop**, `t0..t1` = where to match, `valid` = where to trust it
  (exclude frames where the hand is arriving/leaving).
```bash
$PY "$SKILL/scripts/track_hand.py" && cp clip/hand.js screen/hand.js
```
Template matching gives absolute positions with ~0.1 px precision and no drift, but only while the hand looks the same;
scores printed in `clip/track.json` below ~0.7 mean "wrong posture or hand lifted". If a whole stretch scores low, add a
segment with its own `tref`. The printed burst list is the raw material for the cursor script. Sanity check: bursts
should line up with what you saw in the contact sheets, and clicks should sit at the start/end of bursts or in still periods.

Optical flow was tried first and rejected: it drifts, and the sleeve, arm and leaning body contaminate it.

## 4. Optional: watermark and monitor
- Monitor in shot: `find_screen_quad.py src/clip.mp4 --frame N --roi x0,y0,x1,y1 --debug build/quad.jpg` (add
  `--dark-bottom 0.025` when a dark taskbar sits under the lit page — it belongs to the panel too), check the debug image, paste the quad into `monitor.quad`, set `monitor.first_frame` to that shot's first frame (the shot must be static
  and the screen unobstructed; otherwise skip this).
- Watermark: if it is a flat semi-transparent box, the un-blend in `make_patches.py` restores the real pixels exactly —
  you need its rectangle/radius and four sample regions (a bright and a dark surface, each inside and outside the box).
  Opaque glyphs are then filled by interpolating along whatever straight structure runs under them; that part of
  `make_patches.py` is written for the bundled clip's geometry and needs adapting. If the logo sits on a busy or moving
  background, cropping it out is the better answer.

## 5. Share it
A finished pack (`clip.json`, `beats.md`, `clicks.json`, `hand.js`, `track.json`) dropped into `clips/<id>/` makes the
clip reusable by everyone — PRs welcome. Do not commit the footage itself; put its URL in `source`.
