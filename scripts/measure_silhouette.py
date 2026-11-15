"""Measure a reference figure: silhouette width at every height.

Point IMAGE at a T-pose or turnaround image with the figure on a plain background.
Uses alpha if the image has it, otherwise background-colour matching sampled from the
corners. Run inside Blender (it reads the PNG through bpy).

The point is to build the body tables from numbers instead of eyeballing: a waist 2 cm
off does not read as slightly wrong, it reads as a different character.
"""
import bpy

IMAGE = r"reference.png"
HEIGHT_M = 1.75   # what the figure represents in the world
STEPS = 33        # sample rows, evenly spaced over the figure

img = bpy.data.images.load(IMAGE)
W, H = img.size
px = list(img.pixels)          # RGBA, rows bottom-up
print("image %dx%d" % (W, H))


def at(x, y):
    i = (y * W + x) * 4
    return px[i], px[i + 1], px[i + 2], px[i + 3]


def corners():
    return [at(0, 0), at(W - 1, 0), at(0, H - 1), at(W - 1, H - 1)]


use_alpha = all(c[3] < 0.02 for c in corners())   # transparent background
bg = [sum(c[k] for c in corners()) / 4.0 for k in range(3)]
print("mask:", "alpha" if use_alpha else "background colour", [round(v, 3) for v in bg[:3]])


def is_fg(x, y):
    r, g, b, a = at(x, y)
    if use_alpha:
        return a > 0.5
    return abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 0.06


rows = []
for y in range(H):
    xs = [x for x in range(0, W, 2) if is_fg(x, y)]
    if xs:
        rows.append((y, min(xs), max(xs)))
if not rows:
    raise SystemExit("nothing found — wrong IMAGE, or the background is not plain")

bot = min(r[0] for r in rows)
top = max(r[0] for r in rows)
scale = HEIGHT_M / (top - bot)
print("figure spans %d rows, %.4f m/px" % (top - bot, scale))
print()
print(" z (m)   width (m)")
for i in range(STEPS):
    y = int(bot + (top - bot) * i / (STEPS - 1))
    xs = [x for x in range(0, W, 2) if is_fg(x, y)]
    if not xs:
        continue
    z = (y - bot) * scale
    print("  %.3f     %.3f" % (z, (max(xs) - min(xs)) * scale))

best = max(rows, key=lambda r: r[2] - r[1])
print()
print("widest row: %.3f m at z=%.3f" % ((best[2] - best[1]) * scale, (best[0] - bot) * scale))
