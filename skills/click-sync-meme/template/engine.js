// click-sync engine: turns a script of cursor moves + mouse events into one state per video frame.
//
// The point of the whole technique lives here: a move only says WHERE the cursor goes; WHEN and how fast
// it travels inside its time window is taken from the measured speed of the real hand (HAND.speed, one
// value per video frame, exported by scripts/track_hand.py). So the fake cursor accelerates, hesitates
// and stops exactly when the person on the video does.
//
// Requires hand.js (defines HAND = {fps, n, speed[]}) to be loaded first. A scene calls Engine.run({...}).
//
//   moves   [{t0, t1, to:[x,y] | to:()=>[x,y] | by:[dx,dy], prof?, arc?}]   sorted, non-overlapping, seconds of the SOURCE clip
//             to  = absolute target; a function is resolved when the move starts (so it can follow objects that moved)
//             by  = relative to wherever the cursor is when the move starts
//             prof = 'hand' (default) | 'ease' | 'easeOut'   use ease* where tracking is unreliable or the hand barely moves
//             arc = px of sideways bow, makes free moves look human
//   events  [{t, type:'press'|'release', synthetic?, reinforce?, label?, ...your own fields}]   sorted by t
//             t should sit on a real audio transient (see clips/<id>/clicks.json). Where the story needs a click the
//             microphone did not catch, set synthetic:true and the build mixes a cloned click sound in at that time;
//             reinforce:true does the same, quieter, on top of a real but faint click.
//             label names the row in verify_sync.py's table (defaults to e.grab or e.btn).
//           {t, type:'call', fn(ctx)}   silent timed hook for things the mouse did not do (the computer's reply in a game,
//             a dialog popping up): no ripple, no sound, not part of the sync check.
//   onPress(e, ctx) / onRelease(e, ctx)   scene logic. ctx = {cur:[x,y], i, t, startDrag(obj)}; obj needs numeric x,y.
//             A drag ends automatically on the next release (after onRelease ran).
//   snapshot(ctx) -> any   called once per frame after moves/events/drag were applied; return everything apply() needs,
//             including cursor:'arrow'|'move'|'hand'. ctx = {cur, i, t, dragging}. Runs for every frame in order, so it may
//             also derive per-frame things (hover highlights, blinking) from ctx.i / ctx.t.
//   apply(s, frame, i)     put snapshot s on the DOM. frame = {cx, cy, ripples, s}
//   start   [x,y] initial cursor position;  origin [x,y] screen position of the coordinate system used by moves
//
// All coordinates are local to `origin` (typically the top-left of the fake app's canvas).

const Engine = (() => {
  const FPS = HAND.fps, N = HAND.n;
  const cum = [0]; for (let i = 1; i < N; i++) cum[i] = cum[i - 1] + HAND.speed[i];
  function cumAt(t) { const f = Math.max(0, Math.min(N - 1, t * FPS)); const i = Math.floor(f), a = f - i; return cum[i] + (cum[Math.min(N - 1, i + 1)] - cum[i]) * a; }
  const ease = (p) => p * p * (3 - 2 * p);
  const easeOut = (p) => 1 - Math.pow(1 - p, 2.2);
  function progress(m, t) {
    const p = Math.max(0, Math.min(1, (t - m.t0) / (m.t1 - m.t0)));
    if (m.prof === 'ease') return ease(p);
    if (m.prof === 'easeOut') return easeOut(p);
    const a = cumAt(m.t0), b = cumAt(m.t1);
    if (b - a < 0.8) return ease(p);                 // the hand practically did not move in this window: fall back
    return (cumAt(Math.max(m.t0, Math.min(m.t1, t))) - a) / (b - a);
  }

  // cursors are drawn 1.375x so they survive phone-sized playback
  const CURSORS = {
    arrow: { hot: 1, svg: `<svg width="33" height="33" viewBox="0 0 24 24"><path d="M1 1v17l4.2-4 3 7 2.6-1.1-3-6.9H14z" fill="#fff" stroke="#000" stroke-width="1.1" stroke-linejoin="round"/></svg>` },
    move: { hot: 16, svg: `<svg width="33" height="33" viewBox="0 0 24 24"><path d="M12 1l4 4.500h-2.700V10.700H18.500V8l4.500 4-4.500 4v-2.700H13.300V18.500H16L12 23l-4-4.500h2.700V13.300H5.500V16L1 12l4.500-4v2.700h5.200V5.500H8z" fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round"/></svg>` },
    hand: { hot: 9, svg: `<svg width="33" height="33" viewBox="0 0 24 24"><path d="M8 11V3.500a1.500 1.500 0 013 0V10h.7V8.500a1.400 1.400 0 012.800 0V10h.7V9.300a1.400 1.400 0 012.800 0V15c0 4-2.300 7-6 7-3 0-4.500-1.400-6.300-4.300L3.300 14c-.8-1.400.9-2.600 2-1.500L8 15z" fill="#fff" stroke="#000" stroke-width="1" stroke-linejoin="round"/></svg>` },
  };
  const RIPPLE_FRAMES = 8;
  let frames = [], cfg = null;

  function run(c) {
    cfg = c; frames = [];
    const moves = c.moves || [], events = c.events || [];
    let cur = c.start.slice(), mi = 0, from = cur.slice(), target = null, drag = null, ei = 0;
    const ripples = [];
    const resolve = (m) => { from = cur.slice(); const v = m.to ? (typeof m.to === 'function' ? m.to() : m.to) : [cur[0] + m.by[0], cur[1] + m.by[1]]; target = [v[0], v[1]]; };
    for (let i = 0; i < N; i++) {
      const t = i / FPS;
      while (mi < moves.length && t >= moves[mi].t1) { if (!target) resolve(moves[mi]); cur = target.slice(); target = null; mi++; }
      if (mi < moves.length && t >= moves[mi].t0) {
        const m = moves[mi];
        if (!target) resolve(m);
        const p = progress(m, t), dx = target[0] - from[0], dy = target[1] - from[1], L = Math.hypot(dx, dy) || 1;
        const off = (m.arc || 0) * Math.sin(Math.PI * p);
        cur = [from[0] + dx * p + (-dy / L) * off, from[1] + dy * p + (dx / L) * off];
      }
      // an event fires on the video frame nearest to its time, so the on-screen change lands within half a frame of the sound
      while (ei < events.length && i >= Math.round(events[ei].t * FPS)) {
        const e = events[ei++];
        const ctx = { cur, i, t, startDrag: (o) => { drag = { o, ox: o.x - cur[0], oy: o.y - cur[1] }; } };
        if (e.type === 'call') { e.fn(ctx); continue; }
        if (e.type === 'press') { ripples.push({ x: cur[0], y: cur[1], f: i }); if (c.onPress) c.onPress(e, ctx); }
        else { if (c.onRelease) c.onRelease(e, ctx); drag = null; }
      }
      if (drag) { drag.o.x = Math.round(cur[0] + drag.ox); drag.o.y = Math.round(cur[1] + drag.oy); }
      frames.push({
        cx: cur[0], cy: cur[1],
        ripples: ripples.filter(r => i - r.f < RIPPLE_FRAMES).map(r => ({ x: r.x, y: r.y, p: (i - r.f) / RIPPLE_FRAMES })),
        s: c.snapshot({ cur, i, t, dragging: !!drag }),
      });
    }
    // read back by scripts/render_screen.py -> build/events.json (used for synthetic clicks and the sync check)
    window.EVENTS = events.filter(e => e.type !== 'call').map(e => ({ t: e.t, type: e.type, synthetic: !!e.synthetic, reinforce: !!e.reinforce, label: e.label || e.grab || e.btn || '' }));
    window.renderFrame = renderFrame;
    renderFrame(0);
    window.READY = true;
  }

  function renderFrame(i) {
    const f = frames[Math.max(0, Math.min(N - 1, i))];
    cfg.apply(f.s, f, i);
    const [ox, oy] = cfg.origin;
    const cdef = CURSORS[f.s.cursor] || CURSORS.arrow;
    const c = document.getElementById('cursor'); c.innerHTML = cdef.svg;
    c.style.left = Math.round(ox + f.cx - cdef.hot) + 'px'; c.style.top = Math.round(oy + f.cy - cdef.hot) + 'px';
    const rp = document.getElementById('ripples');
    if (rp) rp.innerHTML = f.ripples.map(r => { const R = 5 + 15 * r.p; return `<div class="ripple" style="left:${ox + r.x - R}px;top:${oy + r.y - R}px;width:${2 * R}px;height:${2 * R}px;opacity:${(1 - r.p).toFixed(2)}"></div>`; }).join('');
  }

  return { run, FPS, N, progress };
})();
