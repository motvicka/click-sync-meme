#!/usr/bin/env python3
"""Locate the four corners of a lit monitor in a (static) shot, for compositing the fake screen onto it.

  find_screen_quad.py VIDEO --frame N --roi x0,y0,x1,y1 [--thr 140] [--debug quad.jpg]

Thresholds the bright screen inside the ROI, then fits a straight line to the MIDDLE part of each side and
intersects the lines. Using only the middle of each side matters: corners are often polluted (a watermark,
a reflection, rounded bezel) and a plain contour->polygon approximation gets them wrong by tens of pixels.
Prints TL, TR, BR, BL — paste into clip.json -> monitor.quad. Check the debug image before trusting it.
"""
import argparse, json
import cv2, numpy as np
ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('--frame', type=int, required=True); ap.add_argument('--roi', required=True)
ap.add_argument('--thr', type=int, default=140); ap.add_argument('--debug')
a = ap.parse_args()
cap = cv2.VideoCapture(a.video); cap.set(cv2.CAP_PROP_POS_FRAMES, a.frame); ok, fr = cap.read()
x0, y0, x1, y1 = map(int, a.roi.split(','))
g = cv2.GaussianBlur(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (3, 3), 0)
m = np.zeros_like(g); m[y0:y1, x0:x1] = (g[y0:y1, x0:x1] > a.thr) * 255
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cnt = max(cs, key=cv2.contourArea); pts = cnt.reshape(-1, 2).astype(np.float32)
hull = cv2.convexHull(cnt)
for eps in (0.01, 0.02, 0.03, 0.05, 0.08):
    q = cv2.approxPolyDP(hull, eps * cv2.arcLength(hull, True), True)
    if len(q) == 4: break
q = q.reshape(-1, 2).astype(np.float32); s = q.sum(1); d = q[:, 0] - q[:, 1]
quad = np.array([q[s.argmin()], q[d.argmax()], q[s.argmax()], q[d.argmin()]], np.float32)     # TL TR BR BL

def inter(l1, l2):
    (p1, v1), (p2, v2) = l1, l2
    t = np.linalg.solve(np.array([[v1[0], -v2[0]], [v1[1], -v2[1]]]), p2 - p1)[0]; return p1 + v1 * t
for band in (45, 10, 5):                       # coarse -> fine: refit each side from contour points near its middle 60 %
    lines = []
    for k in range(4):
        p, r = quad[k], quad[(k + 1) % 4]; v = (r - p) / np.linalg.norm(r - p); L = np.linalg.norm(r - p)
        rel = pts - p; along = rel @ v; dist = np.abs(rel @ np.array([-v[1], v[0]]))
        sel = pts[(along > 0.2 * L) & (along < 0.8 * L) & (dist < band)]
        vx, vy, px, py = cv2.fitLine(sel, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel(); lines.append((np.array([px, py]), np.array([vx, vy])))
    quad = np.array([inter(lines[3], lines[0]), inter(lines[0], lines[1]), inter(lines[1], lines[2]), inter(lines[2], lines[3])], np.float32)
out = [[round(float(x), 1), round(float(y), 1)] for x, y in quad]
print(json.dumps(out))
if a.debug:
    dbg = fr.copy(); cv2.polylines(dbg, [quad.round().astype(np.int32)], True, (0, 0, 255), 1); cv2.imwrite(a.debug, dbg)
