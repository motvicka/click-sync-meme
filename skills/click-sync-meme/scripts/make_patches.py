#!/usr/bin/env python3
"""Build full-frame RGBA overlays for the top (real) video: build/patch_<shot>.png

  make_patches.py [--project DIR]

Two optional jobs, both driven by the clip pack:
  logo     remove a broadcaster watermark that is a semi-transparent box + opaque white glyphs.
           The box is UN-BLENDED analytically: sample a bright and a dark surface inside and outside the box,
           solve  seen = real*(1-a) + c*a  for a and c per channel, invert. That restores the true pixels instead of
           smearing them (what delogo/inpainting would do). Only the opaque glyphs need filling, and they are filled by
           interpolating ALONG the straight edges that run through them (monitor edge, bezel), so edges stay straight.
  monitor  put the finished fake screen (build/final_screen.png) onto the real monitor in a static shot.
           The real screen shows a mostly white page, so its blurred image doubles as an illumination map:
           multiplying the fake screen by it inherits the camera's colour cast, vignetting and glare for free.

The edge directions used for filling are specific to where the watermark sits in putin-vote-2026 (over a monitor's
back in one shot, over a monitor's top-left bezel corner in the other). For another clip keep the un-blend and the
illumination trick, and adapt the fill directions to the straight structures under YOUR watermark.
"""
import argparse, json
import cv2, numpy as np
from _common import project, clip_pack

ap = argparse.ArgumentParser(); ap.add_argument('--project', default='.'); ap.add_argument('--preview', action='store_true')
a = ap.parse_args()
proj, pj = project(a.project); pack, clip = clip_pack(pj['clip'], proj)
logo, mon = clip.get('logo'), clip.get('monitor')
if not logo and not mon: raise SystemExit('clip pack has neither "logo" nor "monitor" — nothing to do')
shots = clip['layout']['shots']
cap = cv2.VideoCapture(str(proj / 'src' / 'clip.mp4'))
W, H = clip['size']

def median(rng):
    fr = []
    for i in range(*rng):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read(); fr.append(f)
    return np.median(np.stack(fr), axis=0).astype(np.float32)
def shot_range(name):
    k = [s['name'] for s in shots].index(name); f0 = shots[k]['first_frame']
    f1 = shots[k + 1]['first_frame'] if k + 1 < len(shots) else clip['frames']
    return [f0 + 2, f1 - 1, max(1, (f1 - f0) // 15)]
def dir_fill(img, mask, dx, dy):
    """fill masked pixels by interpolating between the nearest clean pixels on both sides along (dx,dy)"""
    n = np.hypot(dx, dy); dx, dy = dx / n, dy / n
    out = img.copy(); ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        ends = []
        for s in (-1, 1):
            k = 1
            while k < 400:
                px, py = int(round(x + s * k * dx)), int(round(y + s * k * dy))
                if not (0 <= px < W and 0 <= py < H): break
                if not mask[py, px]:
                    qx, qy = int(round(x + s * (k + 1) * dx)), int(round(y + s * (k + 1) * dy))   # one px further from the mask = cleaner sample
                    ends.append((k, img[qy, qx] if (0 <= qx < W and 0 <= qy < H and not mask[qy, qx]) else img[py, px])); break
                k += 1
        if len(ends) == 2:
            (k0, p0), (k1, p1) = ends; out[y, x] = (p0 * k1 + p1 * k0) / (k0 + k1)
        elif ends: out[y, x] = ends[0][1]
    return out

main_name = shots[0]['name']
mon_name = next((s['name'] for s in shots if mon and s['first_frame'] == mon['first_frame']), None)
res, alpha = {}, {}

if logo:
    X0, Y0, X1, Y1 = logo['box']; R = logo['radius']; SOFT = logo.get('soft_right_edge', 0)
    mf = logo.get('median_frames', {})
    med = {n: median(mf.get(n) or shot_range(n)) for n in {main_name, mon_name} - {None}}
    m = med[main_name]
    reg = lambda img, r: np.median(img[r[2]:r[3], r[0]:r[1]].reshape(-1, 3), axis=0)
    sm = logo['alpha_samples']
    in_w, out_w, in_d, out_d = (reg(m, sm[k]) for k in ('bright_in', 'bright_out', 'dark_in', 'dark_out'))
    al = 1 - (in_w - in_d) / (out_w - out_d); col = (in_w - out_w * (1 - al)) / al
    print('watermark box: alpha per channel', al.round(3), 'colour (BGR)', col.round(1))
    k = 4; big = np.zeros((H * k // 2, W * k // 2), np.uint8)                   # supersampled rounded rect (top-left quadrant is enough here)
    bx0, by0, bx1, by1, br = [v * k for v in (X0, Y0, X1, Y1, R)]
    cv2.rectangle(big, (bx0 + br, by0), (bx1 - br, by1), 255, -1); cv2.rectangle(big, (bx0, by0 + br), (bx1, by1 - br), 255, -1)
    for cx, cy in ((bx0 + br, by0 + br), (bx1 - br, by0 + br), (bx0 + br, by1 - br), (bx1 - br, by1 - br)): cv2.circle(big, (cx, cy), br, 255, -1)
    bm = np.zeros((H, W), np.float32); bm[:H // 2, :W // 2] = cv2.resize(big, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    ring = cv2.dilate(((bm > 0.02) & (bm < 0.98)).astype(np.uint8), np.ones((3, 3), np.uint8))
    if SOFT: ring[Y0 - 2:Y1 + 2, X1 - SOFT + 2:X1 + 2] = 1
    unblend = lambda img: (img - col * bm[..., None] * al) / (1 - bm[..., None] * al)
    gx0, gy0, gx1, gy1 = logo['glyph_bbox']
    def glyphs(img):
        gl = (img.min(axis=2) > logo['glyph_min']).astype(np.uint8); keep = np.zeros_like(gl); keep[gy0:gy1, gx0:gx1] = 1
        return cv2.dilate(gl & keep, np.ones((7, 7), np.uint8))
    box_alpha = cv2.GaussianBlur(cv2.dilate((bm > 0).astype(np.float32), np.ones((13, 13))), (0, 0), 1.5)

    # main shot: every structure under the box runs (slightly slanted) vertically
    ring_m = ring.copy(); ring_m[:, X1 - SOFT:] = 0
    r = dir_fill(unblend(m), glyphs(m) | ring_m, logo['main_fill_slope'], 1)
    if SOFT:   # the soft right edge sits on a flat wall: replicate sideways, but leave anything darker (the flag) alone
        blk = r[Y0 - 3:Y1 + 3, X1 - SOFT:X1 + 1]; wallish = m[Y0 - 3:Y1 + 3, X1 - SOFT:X1 + 1].min(axis=2) > 170
        blk[wallish] = np.broadcast_to(r[Y0 - 3:Y1 + 3, X1 - SOFT - 1:X1 - SOFT], blk.shape)[wallish]
    res[main_name], alpha[main_name] = r, box_alpha

if mon:
    quad = np.array(mon['quad'], np.float32); TL, TR, BR, BL = quad
    l = med[mon_name] if logo else median(shot_range(mon_name))
    base = l.copy(); a_l = np.zeros((H, W), np.float32)
    if logo:
        Yg, Xg = np.mgrid[0:H, 0:W].astype(np.float32)
        side = lambda p0, p1: (p1[0] - p0[0]) * (Yg - p0[1]) - (p1[1] - p0[1]) * (Xg - p0[0])
        leftof = side(BL, TL) < 1.5; above = (side(TL, TR) < 1.5) & ~leftof; inside = ~above & ~leftof
        un, gl = unblend(l), glyphs(l); top_d, left_d = TR - TL, BL - TL
        ring_h = ring.copy(); ring_h[Y0 + R:, X0 + 3:] = 0                     # top edge + left edge + top corners
        ring_v = ring.copy(); ring_v[:Y1 - R] = 0; ring_v[:, X1 - R - 4:] = 0  # bottom edge + bottom-left corner
        base = dir_fill(un, ((gl & leftof) | (ring_v & ~inside)).astype(np.uint8), left_d[0], left_d[1])       # left bezel first...
        base = dir_fill(base, ((gl & above) | ring_h).astype(np.uint8) & ~inside.astype(np.uint8), top_d[0], top_d[1])   # ...then the top bezel can borrow from it
        for x in range(X1 - SOFT + 1, X1 + 3):
            for y in range(Y0 - 3, Y1 + 3):
                kk = x - (X1 - SOFT - 1); base[y, x] = base[int(round(y - kk * top_d[1] / top_d[0])), X1 - SOFT - 1]
        ox, oy, ovx, ovy = mon['outer_top_edge']                               # anything still bright on the black front bezel is glyph residue
        zone = (Xg > mon['bezel_x_min']) & (Xg < X1) & (Yg > Y0) & (Yg < Y1) & ~inside & ((Yg - (oy + (Xg - ox) * ovy / ovx)) > 5)
        bright = base.mean(axis=2) > 70; base[zone & bright] = np.median(base[zone & ~bright], axis=0)
        base = cv2.inpaint(np.clip(base, 0, 255).astype(np.uint8), (gl & inside).astype(np.uint8), 3, cv2.INPAINT_TELEA).astype(np.float32)
        a_l = box_alpha
    fake = cv2.imread(str(proj / 'build' / 'final_screen.png'))
    if fake is None: raise SystemExit('build/final_screen.png missing — run render_screen.py first')
    fake = fake.astype(np.float32); fh, fw = fake.shape[:2]
    Hm = cv2.getPerspectiveTransform(np.array([[0, 0], [fw, 0], [fw, fh], [0, fh]], np.float32), quad)
    real_rect = cv2.warpPerspective(l, np.linalg.inv(Hm), (fw, fh))
    core = real_rect[int(fh * .30):int(fh * .88), int(fw * .30):int(fw * .94)]          # stay away from watermark, browser tabs, taskbar
    illum = cv2.GaussianBlur(cv2.resize(cv2.GaussianBlur(core, (0, 0), 40), (fw, fh), interpolation=cv2.INTER_CUBIC), (0, 0), 25)
    illum /= np.percentile(illum.reshape(-1, 3), 99.5, axis=0)
    lit = np.clip(fake * (0.30 + 0.70 * illum) * 0.97 + 10, 0, 255)                     # +10: an LCD's black is never black on camera
    warped = cv2.GaussianBlur(cv2.warpPerspective(lit, Hm, (W, H), flags=cv2.INTER_AREA), (0, 0), 0.7)
    mask = cv2.warpPerspective(np.ones((fh, fw), np.float32), Hm, (W, H))
    mask = cv2.GaussianBlur(cv2.dilate(mask, np.ones((3, 3))), (0, 0), 0.8)
    res[mon_name] = base * (1 - mask[..., None]) + warped * mask[..., None]
    alpha[mon_name] = np.maximum(a_l, (cv2.dilate(mask, np.ones((7, 7))) > 0.01).astype(np.float32))

for n in res:
    cv2.imwrite(str(proj / 'build' / f'patch_{n}.png'), np.dstack([np.clip(res[n], 0, 255), np.clip(alpha[n], 0, 1) * 255]).astype(np.uint8))
    f0 = [s for s in shots if s['name'] == n][0]['first_frame']
    cap.set(cv2.CAP_PROP_POS_FRAMES, f0 + 20); ok, f = cap.read(); p = cv2.imread(str(proj / 'build' / f'patch_{n}.png'), cv2.IMREAD_UNCHANGED)
    al_ = p[..., 3:].astype(np.float32) / 255; cv2.imwrite(str(proj / 'build' / f'patch_{n}_preview.jpg'), (f * (1 - al_) + p[..., :3] * al_).astype(np.uint8))
    print(f'build/patch_{n}.png  (check build/patch_{n}_preview.jpg)')
