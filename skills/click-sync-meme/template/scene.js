// Example scene: a fake MS Paint session in which an ugly "Kytarobraní" flyer gets rearranged.
// Replace this file (and the app markup in screen.html) with your own story; engine.js stays as it is.
// Times below are seconds of the SOURCE clip putin-vote-2026 — see clips/putin-vote-2026/beats.md for what
// the man is doing at each moment and clicks.json for the audible clicks the events are pinned to.

const CX = 8, CY = 142;              // canvas origin in screen px (all scene coordinates are canvas-local)
const CW = 840, CH = 440;
const $ = (id) => document.getElementById(id);

/* ------------------------------------------------------------------ static UI bits */
const PALETTE = ['#000000', '#7f7f7f', '#880015', '#ed1c24', '#ff7f27', '#fff200', '#22b14c', '#00a2e8', '#3f48cc', '#a349a4',
                 '#ffffff', '#c3c3c3', '#b97a57', '#ffaec9', '#ffc90e', '#efe4b0', '#b5e61d', '#99d9ea', '#7092be', '#c8bfe7',
                 '', '', '', '', '', '', '', '', '', ''];
$('pal').innerHTML = PALETTE.map(c => `<i style="background:${c || '#f5f6f7'}"></i>`).join('');
const SH = ['M1 12L12 1', 'M1 10C4 0 8 14 12 3', 'M6.5 1.5a5 5 0 100 10a5 5 0 100-10', 'M1.5 2.5h10v8h-10z', 'M1.5 2.5h10v8h-10z', 'M2 11L6 2l5 4-3 5z', 'M6.5 1.5l5 9h-10z', 'M1.5 1.5v9h10z',
            'M6.5 1l5.5 5.5L6.5 12 1 6.5z', 'M6.5 1l5.5 4-2 6.5h-7l-2-6.5z', 'M3.5 1.5h6l3 5-3 5h-6l-3-5z', 'M1 5h7V2l4 4.5L8 11V8H1z', 'M12 5H5V2L1 6.5 5 11V8h7z', 'M5 12V5H2l4.5-4L11 5H8v7z', 'M5 1v7H2l4.5 4L11 8H8V1z', 'M6.5 1l1.5 4 4-1-3 3 3 3-4-1-1.5 4-1.5-4-4 1 3-3-3-3 4 1z',
            'M6.5 1l1.7 3.6 3.8.5-2.8 2.7.7 3.9-3.4-1.9-3.4 1.9.7-3.9L1 5.1l3.8-.5z', 'M6.5 1l1.2 2.8 3-.6-1 2.9 2.4 1.9-2.8 1 .2 3-2.9-1.2L3.8 12l.1-3-2.8-1 2.4-1.9-1-2.9 3 .6z', 'M1.5 2.5h10v6h-5l-3 3v-3h-2z', 'M6.5 2a5 3.5 0 100 7l-3 3 .5-3.2', 'M1 8a3 3 0 013-3 3.5 3.5 0 016.5 1A2.5 2.5 0 0110 11H3.5A2.5 2.5 0 011 8z', 'M6.5 11.5C1 7 1 2.5 4 2.5c1.4 0 2.5 1.5 2.5 1.5S7.6 2.5 9 2.5c3 0 3 4.500-2.500 9z', 'M7 1L3 7h3l-1 5 5-7H7z', ''];
$('shapes').innerHTML = SH.map(d => `<svg viewBox="0 0 13 13"><path d="${d}" fill="none" stroke="#3b4a5e" stroke-width="1"/></svg>`).join('');

/* ------------------------------------------------------------------ ugly background doodles */
let seed = 7;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const jit = (a) => (rnd() - 0.5) * 2 * a;
function wobble(pts, a) { return 'M' + pts.map(p => `${(p[0] + jit(a)).toFixed(0)} ${(p[1] + jit(a)).toFixed(0)}`).join('L'); }
function note(x, y, s) {
  return `<g transform="translate(${x} ${y}) scale(${s})"><ellipse cx="0" cy="0" rx="9" ry="6.5" fill="#000" transform="rotate(-20)"/><path d="M8 -2 L9 -42 L26 -33 L25 -24 L10 -32" fill="none" stroke="#000" stroke-width="4"/></g>`;
}
function tree(x, y, s) {
  return `<g transform="translate(${x} ${y}) scale(${s})"><path d="M-7 0 L-5 -62 L8 -60 L9 0 Z" fill="#b97a57" stroke="#000" stroke-width="3"/>
    <path d="${wobble([[-38, -62], [-48, -92], [-30, -122], [-4, -136], [26, -126], [44, -98], [36, -66], [6, -54], [-20, -55]], 4)}Z" fill="#22b14c" stroke="#000" stroke-width="3"/>
    <path d="M-20 -96 l8 -6 l7 8 M8 -106 l9 -5 l6 9 M-2 -78 l9 -6 l7 8" fill="none" stroke="#b5e61d" stroke-width="3"/></g>`;
}
(function drawBg() {
  let s = '';
  // sun + rays
  for (let k = 0; k < 10; k++) {
    const a = (k / 10) * Math.PI * 2 + 0.2, r0 = 50 + jit(4), r1 = 80 + jit(12);
    s += `<path d="M${(72 + Math.cos(a) * r0).toFixed(0)} ${(64 + Math.sin(a) * r0).toFixed(0)}L${(72 + Math.cos(a) * r1).toFixed(0)} ${(64 + Math.sin(a) * r1).toFixed(0)}" stroke="#ff7f27" stroke-width="6" stroke-linecap="round"/>`;
  }
  s += `<path d="${wobble([[34, 64], [44, 36], [72, 25], [100, 36], [111, 64], [100, 92], [72, 104], [44, 92]], 3)}Z" fill="#fff200" stroke="#ff7f27" stroke-width="5"/>`;
  s += `<circle cx="60" cy="56" r="4" fill="#000"/><circle cx="86" cy="55" r="4" fill="#000"/><path d="M56 76 C64 90 82 90 90 75" fill="none" stroke="#000" stroke-width="4"/>`;
  // grass: zigzag strip
  const g = [[0, 440], [0, 398]];
  for (let x = 0; x <= 840; x += 14) g.push([x + 7, 384 + jit(7)], [x + 14, 404 + jit(5)]);
  g.push([840, 440]);
  s += `<path d="M${g.map(p => p.map(v => v.toFixed(0)).join(' ')).join('L')}Z" fill="#22b14c"/>`;
  for (let k = 0; k < 16; k++) { const x = 20 + k * 52 + jit(14), y = 418 + jit(10); s += `<path d="M${x.toFixed(0)} ${y.toFixed(0)} l6 -14 l6 14 l7 -12 l5 12" fill="none" stroke="#b5e61d" stroke-width="3"/>`; }
  // trees
  s += tree(62, 400, 1.0) + tree(150, 392, 0.72);
  // erased "mistake": white eraser smear with leftovers
  s += `<path d="M196 300 L292 296 M200 314 L288 312 M204 328 L280 326" stroke="#fff" stroke-width="18" stroke-linecap="square"/>`;
  s += `<path d="M206 322 l10 -20 M282 300 l8 12 M240 333 l12 3" stroke="#ed1c24" stroke-width="4"/>`;
  // notes
  s += note(752, 96, 1) + note(800, 164, 0.8) + note(236, 250, 0.9) + note(592, 346, 0.75);
  // a bucket-fill leak: white pixels left around the sun rays
  for (let k = 0; k < 26; k++) s += `<rect x="${(20 + rnd() * 120).toFixed(0)}" y="${(8 + rnd() * 120).toFixed(0)}" width="2" height="2" fill="#fff"/>`;
  $('bg').innerHTML = s;
})();

/* ------------------------------------------------------------------ objects */
const TITLE_LAYERS = [[9, 9, '#00a2e8'], [6, 6, '#22b14c'], [3, 3, '#fff200'], [0, 0, '#ed1c24']];
$('title').innerHTML = TITLE_LAYERS.map(([x, y, c]) => `<span class="txt" style="left:${x}px;top:${y}px;color:${c}">Kytarobraní</span>`).join('');
function measureTitle(size) {
  const el = $('title'); el.style.fontSize = size + 'px';
  const sp = el.lastChild; return [sp.offsetWidth + 9, sp.offsetHeight + 9];
}
const SIZES = [58, 70, 84];
let sizeIdx = 0;
const obj = {
  title: { x: 0, y: 72, w: 0, h: 0 },
  guitar: { x: 322, y: 118, w: 180, h: 250, flip: false },
  sub: { x: 292, y: 370, w: $('sub').offsetWidth, h: $('sub').offsetHeight },
};
[obj.title.w, obj.title.h] = measureTitle(SIZES[0]);
obj.title.x = Math.round(426 - obj.title.w / 2 - 172);   // he will drag it ~172 px right

/* ------------------------------------------------------------------ floating toolbar under the selection */
const state = { sel: null, down: null };
const TB = { w: 176, h: 34, btn: { rot: 19, flip: 49, bigger: 88, smaller: 118, del: 157 } };
const tb = { on: false, x: 0, y: 0 };
function spawnToolbar() {
  const o = obj[state.sel]; if (!o) { tb.on = false; return; }
  tb.on = true;
  tb.x = Math.round(Math.max(0, Math.min(CW - TB.w, o.x + o.w / 2 - TB.w / 2)));
  tb.y = Math.round(o.y + o.h + 12);
}
const btnCenter = (k) => [tb.x + TB.btn[k], tb.y + 17];
function btnAt(x, y) {
  if (!tb.on || y < tb.y + 3 || y > tb.y + 31) return null;
  for (const k in TB.btn) if (Math.abs(x - (tb.x + TB.btn[k])) <= 15) return k;
  return null;
}

/* ------------------------------------------------------------------ the script */
// `to` = absolute target (a function is resolved when the move starts), `by` = relative. Windows come from the
// hand-motion bursts in beats.md; inside a window the cursor follows the real hand's speed profile.
const moves = [
  { t0: 0.04, t1: 1.54, to: [452, 262], arc: -10 },
  { t0: 1.92, t1: 3.42, to: [372, 176], arc: 8 },
  { t0: 4.60, t1: 5.40, by: [-7, -9] },
  { t0: 7.15, t1: 7.60, to: () => [obj.title.x + obj.title.w * 0.42, obj.title.y + obj.title.h * 0.6], arc: 6 },   // onto the title
  { t0: 7.62, t1: 7.98, by: [208, 22] },        // drag title: too far right...
  { t0: 8.05, t1: 8.42, by: [-52, -27] },       // ...back a bit...
  { t0: 8.42, t1: 8.80, by: [26, 12] },         // ...settle (released mid-way)
  { t0: 8.84, t1: 9.55, to: () => btnCenter('bigger'), arc: -5 },
  { t0: 11.28, t1: 11.70, by: [4, -3] },
  { t0: 15.75, t1: 17.15, by: [6, 5] },         // leaning in, barely touching the mouse
  { t0: 18.72, t1: 19.38, to: () => [obj.guitar.x + 92, obj.guitar.y + 196], prof: 'ease', arc: 8 },   // hand is just returning to the mouse: tracking unreliable -> ease
  { t0: 19.44, t1: 20.17, by: [222, 158] },     // drag guitar: way down (half off the canvas)...
  { t0: 20.17, t1: 20.85, by: [84, -78] },      // ...no, back up
  { t0: 20.85, t1: 23.05, by: [16, -20], prof: 'easeOut' },
  { t0: 23.55, t1: 23.92, by: [5, -3] },
  { t0: 25.30, t1: 26.60, to: () => btnCenter('flip'), prof: 'ease', arc: 6 },
  { t0: 28.17, t1: 29.17, to: () => [obj.sub.x + obj.sub.w * 0.86, obj.sub.y + obj.sub.h * 0.55], arc: -9 },
  { t0: 29.17, t1: 30.45, by: [-8, 3], prof: 'ease' },
  { t0: 30.72, t1: 30.95, by: [-4, -2] },
  { t0: 32.36, t1: 33.05, by: [-66, -296], arc: -14 },   // drag subtitle: overshoots right over the title...
  { t0: 33.20, t1: 33.95, by: [38, 92] },                // ...and back down under it
  { t0: 33.97, t1: 34.62, by: [74, 40], prof: 'ease' },
  { t0: 35.15, t1: 36.80, by: [9, -30] },
];
// press/release times are real audio transients, except those marked synthetic (a cloned click gets mixed in there)
const events = [
  { t: 7.61, type: 'press', grab: 'title' },
  { t: 8.63, type: 'release', label: 'drop title' },
  { t: 9.78, type: 'press', btn: 'bigger' }, { t: 9.86, type: 'release', label: 'grow 1' },
  { t: 11.108, type: 'press', btn: 'bigger' }, { t: 11.226, type: 'release', label: 'grow 2' },
  { t: 19.40, type: 'press', grab: 'guitar', synthetic: true },
  { t: 23.88, type: 'release', label: 'drop guitar' },
  { t: 27.52, type: 'press', btn: 'flip', reinforce: true }, { t: 27.61, type: 'release', reinforce: true, label: 'flipped' },   // real click, but very faint
  { t: 30.514, type: 'press', grab: 'sub', clickOnly: true }, { t: 30.70, type: 'release', label: 'selected' },
  { t: 32.34, type: 'press', grab: 'sub', synthetic: true },
  { t: 33.97, type: 'release', synthetic: true, label: 'drop sub' },
  { t: 34.964, type: 'press', deselect: true, label: 'deselect' }, { t: 35.086, type: 'release', label: 'done' },
];

function onPress(e, ctx) {
  if (e.btn) state.down = e.btn;
  else if (e.deselect) { state.sel = null; tb.on = false; }
  else if (e.grab) {
    if (state.sel !== e.grab) { state.sel = e.grab; tb.on = false; }
    if (!e.clickOnly) { ctx.startDrag(obj[e.grab]); tb.on = false; }
  }
}
function onRelease(e, ctx) {
  if (state.down === 'bigger') {          // grows around its centre, bottom edge fixed, so the toolbar under it stays put
    const o = obj.title, cx = o.x + o.w / 2, bottom = o.y + o.h;
    sizeIdx = Math.min(SIZES.length - 1, sizeIdx + 1);
    [o.w, o.h] = measureTitle(SIZES[sizeIdx]); o.x = Math.round(cx - o.w / 2); o.y = Math.round(bottom - o.h);
  }
  if (state.down === 'flip') obj.guitar.flip = !obj.guitar.flip;
  state.down = null;
  if (state.sel && !tb.on) spawnToolbar();
}
function snapshot({ cur, dragging }) {
  const o = state.sel && obj[state.sel];
  const hov = btnAt(cur[0], cur[1]);
  const inSel = o && cur[0] >= o.x - 3 && cur[0] <= o.x + o.w + 3 && cur[1] >= o.y - 3 && cur[1] <= o.y + o.h + 3;
  return {
    cursor: (dragging || (inSel && !hov)) ? 'move' : 'arrow',
    title: { x: obj.title.x, y: obj.title.y, size: SIZES[sizeIdx] },
    guitar: { x: obj.guitar.x, y: obj.guitar.y, flip: obj.guitar.flip },
    sub: { x: obj.sub.x, y: obj.sub.y },
    sel: o ? { x: o.x, y: o.y, w: o.w, h: o.h } : null,
    tb: tb.on ? { x: tb.x, y: tb.y, hov, down: state.down } : null,
  };
}
function apply(s, f, i) {
  const T = $('title'); T.style.fontSize = s.title.size + 'px'; T.style.left = s.title.x + 'px'; T.style.top = s.title.y + 'px'; T.style.zIndex = 1;
  const G = $('guitar'); G.style.left = s.guitar.x + 'px'; G.style.top = s.guitar.y + 'px'; G.style.zIndex = 2; $('gsvg').style.transform = s.guitar.flip ? 'scaleX(-1)' : '';
  const S = $('sub'); S.style.left = s.sub.x + 'px'; S.style.top = s.sub.y + 'px'; S.style.zIndex = 3;
  const sel = $('sel');
  if (s.sel) { sel.style.display = 'block'; sel.style.left = (s.sel.x - 3) + 'px'; sel.style.top = (s.sel.y - 3) + 'px'; sel.style.width = (s.sel.w + 6) + 'px'; sel.style.height = (s.sel.h + 6) + 'px'; }
  else sel.style.display = 'none';
  const tbe = $('tb');
  if (s.tb) {
    tbe.style.display = 'flex'; tbe.style.left = s.tb.x + 'px'; tbe.style.top = s.tb.y + 'px';
    tbe.querySelectorAll('.b').forEach(b => { const k = b.dataset.k; b.className = 'b' + (s.tb.down === k ? ' dn' : (s.tb.hov === k ? ' hov' : '')); });
  } else tbe.style.display = 'none';
  const inC = f.cx >= 0 && f.cx < CW && f.cy >= 0 && f.cy < CH;
  $('st-pos').textContent = inC ? `${Math.round(f.cx)}, ${Math.round(f.cy)}пкс` : '';
  $('st-sel').textContent = s.sel ? `${s.sel.w} × ${s.sel.h}пкс` : '';
  const mins = 41 + Math.floor((i / Engine.FPS + 22) / 60); $('clk').textContent = '12:' + String(mins).padStart(2, '0');
  $('winname').textContent = (i / Engine.FPS > 8.63 ? '*' : '') + 'leták_kytarobraní_FINAL_v3_opravdu_final.bmp — Paint';
}

Engine.run({ start: [560, 418], origin: [CX, CY], moves, events, onPress, onRelease, snapshot, apply });
