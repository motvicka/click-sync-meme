# Writing the cursor script (scene.js)

## Engine API

`engine.js` exposes one call. All coordinates are local to `origin` (usually the top-left of the fake app's canvas);
all times are seconds of the **source** clip.

```js
Engine.run({
  start:  [x, y],            // cursor position at frame 0
  origin: [sx, sy],          // screen position of the local coordinate system
  moves, events,             // see below
  onPress(e, ctx), onRelease(e, ctx),   // your app logic; ctx = {cur:[x,y], i, t, startDrag(obj)}
  snapshot(ctx) -> s,        // once per frame, AFTER moves/events/drag: return everything apply() needs (+ cursor:'arrow'|'move'|'hand')
  apply(s, frame, i),        // put snapshot s on the DOM; frame = {cx, cy, ripples, s}
});
```

The engine simulates all frames up front (state is deterministic and seekable, so single frames can be previewed),
draws cursor and click ripples itself, and sets `window.READY`, `window.renderFrame(i)` and `window.EVENTS`.

### moves
```js
{ t0, t1, to: [x, y] }            // absolute target
{ t0, t1, to: () => [x, y] }      // resolved when the move STARTS — use for anything that may have moved or resized
{ t0, t1, by: [dx, dy] }          // relative; use for drags and nudges
  // optional: prof: 'hand' (default) | 'ease' | 'easeOut',   arc: px of sideways bow
```
Sorted, non-overlapping. Inside `[t0,t1]` progress = share of the real hand's path length covered so far, so the cursor
inherits every acceleration and hesitation. Windows may be generous: where the hand is still, the cursor is still.
If the hand moved < 0.8 px in the whole window the engine silently falls back to `ease`.

### events
```js
{ t, type: 'press' | 'release', ...anything your onPress/onRelease wants (grab:'title', btn:'bigger', ...) }
  // synthetic: true   no audible click exists here -> a cloned click is mixed into the audio
  // reinforce: true   a real click exists but is faint -> a quieter clone is layered on top
```
An event fires on the video frame nearest to `t`. A drag is: `press` → `ctx.startDrag(obj)` in `onPress` → one or more
`by` moves → `release`. While dragging, `obj.x/obj.y` follow the cursor (rounded to whole pixels).

## How to get from beats to a script

1. List the clip's clicks and movement bursts (`beats.md`, `clicks.json`, or the burst list printed by `track_hand.py`).
2. Assign meaning: which bursts are drags (need press before, release after), which are free travel, which clicks press buttons.
3. Only then lay out the screen — **put things where the cursor will be**, not the other way round. Two clicks with a
   motionless hand between them must hit the same control, so design a control that makes sense to press twice and
   place it a short move away from where the previous action ended.
4. Write moves with `by` for drags and lazy `to: () => ...` for travel to objects/buttons.

## Rules of thumb that made the example feel real

- **Timing beats direction.** From a side-on camera nobody can tell which way the mouse went, but everybody sees *when*
  the hand moves and hears *when* it clicks. Keep direction roughly plausible (see the hints in `beats.md`), spend your
  care on timing.
- **Scale.** A hand moving 1 px in a 1080p picture ≈ 9–15 px of cursor on a 1080-wide fake screen. A 20 px burst can
  carry a 200–300 px drag; a 2 px drift should not carry the cursor across the screen (keep it under ~100 px, `prof:'ease'`).
- **Use the human imperfections.** Out-and-back bursts become "dragged it too far, pulled it back". A fast push followed
  by a partial return becomes an overshoot and correction. Tiny movements while the person leans into the monitor become
  pixel-peeping nudges. These are what make people laugh, because they recognise themselves.
- **Blind spots.** When the hand is just returning to the mouse the tracker is unreliable (`valid` ranges in `clip.json`
  exclude those frames, speed = 0 there). Put travel there with `prof:'ease'`.
- **UI that reacts to a click must not move under the cursor.** In the example the title grows with its bottom edge fixed,
  so the floating toolbar below it stays under the motionless cursor for the second click.
- **Release mid-move is fine** (the object drops, the cursor keeps drifting) — it looks more natural than stopping dead.
- **State changes on release, pressed look on press** for buttons; selections and grabs happen on press.
- **Synthetic clicks only where unavoidable** — a drag that starts or ends where the mic caught nothing. They are cloned
  from the clip's own mouse, so they blend in, but real ones are better. Never leave a loud real click without an on-screen consequence.
- **End state early.** Finish the last action at the last real click, then leave ~2 s of nothing before the person's
  reaction; if the clip later shows the real monitor, `make_patches.py` composites your final frame onto it.
- **Readability on a phone:** big objects, few of them, high contrast; the cursor is already drawn 1.4x and every press
  leaves a yellow ripple. UI chrome can be tiny — it is set dressing.
- **Set dressing sells it:** real OS locale of the person, plausible file name with a modified asterisk after the first
  edit, status bar that follows the cursor, a taskbar clock that ticks, and any true detail from the footage
  (the example reuses the real "Activate Windows" watermark).

## Converting times

`frame = round(t * fps)`; output time = `t - start_frame / fps` (default start frame of the bundled clip: 140 = 5.839 s).
