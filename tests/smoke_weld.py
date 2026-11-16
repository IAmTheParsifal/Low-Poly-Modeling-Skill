"""Smoke test for the weld helpers. Runs inside Blender, no scene required.

    import sys; sys.path.insert(0, "scripts")
    exec(open("tests/smoke_weld.py").read())

Builds the smallest model that exercises both kinds of join:

  * a limb bridged into a body with `bridge()` — loops of 8 and 4 verts, which is the
    case that has no equal-count shortcut;
  * a digit extruded from four existing verts with `Build.extrude()`, the join that the
    fingers of a hand use.

Then `check()` must come back clean, and `boundary` must be 0: every seam is stitched, so
the result is one closed shell. If `boundary` is nonzero, a ring was copied instead of
shared — the failure mode this test exists for.
"""
import sys

sys.path.insert(0, "scripts")
from psx_build import Build, ring, bridge, finish, check

b = Build()

# body: a closed bottom, an open top waiting for the limb
a = b.loft([ring(0, 0, 0.0, 0.10, 0.10, 8),
            ring(0, 0, 0.20, 0.10, 0.10, 8)],
           cap_start=True, cap_end=False, part="body")

# limb: open bottom, capped tip — 4 verts, so the seam has mismatched counts
c = b.loft([ring(0, 0, 0.30, 0.05, 0.05, 4),
            ring(0, 0, 0.40, 0.05, 0.06, 4)],
           cap_start=False, cap_end=True, part="limb")

# seam: the body's top ring to the limb's bottom ring, wound to agree with a body face
b.add_faces(bridge(b.v,
                   [a + 8 + i for i in range(8)],
                   [c + i for i in range(4)],
                   [a + 0, a + 1, a + 9, a + 8]),
            part="seam")

# digit: four new verts plus a cap, then a welded extrusion that shares them
q = b.add([(-0.02, -0.02, 0.40), (0.02, -0.02, 0.40),
           (0.02, 0.02, 0.40), (-0.02, 0.02, 0.40)],
          [(0, 1, 2, 3)], part="pad")
b.extrude([q, q + 1, q + 2, q + 3],
          [((0, 0, 1), 0.05, 1.0), ((0, 0.3, 1), 0.04, 0.7)],
          part="digit")

ob = finish("SmokeTest", b)
ok = check(ob)
print("SMOKE", "PASS" if ok else "FAIL")
bpy.data.objects.remove(ob, do_unlink=True)   # noqa: F821 — bpy is present inside Blender
