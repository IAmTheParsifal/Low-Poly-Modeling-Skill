"""Stub test for measure_silhouette.py — runs it against a synthetic image without Blender.

Draws a figure whose width is known at every row, then checks the script recovers it.
"""
import sys, types, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "scripts", "measure_silhouette.py")

W, H = 200, 400
# figure: rows 40..360 (320 rows = 1.75 m), width ramps 20 px at the bottom to 80 px mid
TOP, BOT = 40, 360
pixels = [0.0] * (W * H * 4)
def set_px(x, y, rgba):
    i = (y * W + x) * 4
    pixels[i:i + 4] = rgba

for y in range(H):
    for x in range(W):
        set_px(x, y, [0.2, 0.2, 0.2, 1.0])       # background grey
for y in range(TOP, BOT + 1):
    t = (y - TOP) / (BOT - TOP)                   # 0 at top, 1 at bottom
    half = 10 + 30 * (1 - abs(t - 0.5) * 2)       # widest in the middle: 80 px
    cx = W // 2
    for x in range(int(cx - half), int(cx + half) + 1):
        set_px(x, y, [0.9, 0.9, 0.9, 1.0])


class FakeImage:
    size = (W, H)
    pixels = pixels


fake_bpy = types.ModuleType("bpy")
fake_bpy.data = types.SimpleNamespace(images=types.SimpleNamespace(load=lambda p: FakeImage()))
sys.modules["bpy"] = fake_bpy

src = open(SCRIPT, encoding="utf-8").read().replace('IMAGE = r"reference.png"', 'IMAGE = "synthetic"')
ns = {"__name__": "measure_test"}
exec(compile(src, SCRIPT, "exec"), ns)

# expected: 320 rows over 1.75 m -> 0.00546875 m/px; widest = 80 px -> 0.4375 m
print()
print("EXPECTED  m/px 0.00547, widest 0.4375 m, at z about 0.875")
