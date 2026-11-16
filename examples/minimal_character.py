"""Minimal end-to-end blockout: a 1.75 m humanoid, mesh only, in about 60 lines.

Run from the repo root inside Blender:

    import sys; sys.path.insert(0, "scripts")
    exec(open("examples/minimal_character.py").read())

Every shape is a table of numbers. Change a number, re-run, look at the render — that is
the whole loop.

This is a **blockout**: the shells are capped and pushed into each other, because
proportions come first and topology second. The finished asset welds those joints into a
single surface — cut a shoulder socket and bridge the arm's first ring into it, split the
pelvis rim into the two legs, extrude the fingers off the palm's own vertices. See "One
surface, not a bag of parts" in SKILL.md. Leaving shells butted and hiding the crossing
under a garment is exactly what reads as amateur in a close-up.
"""
import sys

sys.path.insert(0, "scripts")
from psx_build import Build, ring, finish

b = Build()

# torso, waist to neck. e=2.3 keeps the cross-section boxy like the era's meshes.
b.loft([ring(0, 0, z, rx, ry, 10, 2.3) for z, rx, ry in (
    (0.86, 0.145, 0.100),
    (1.02, 0.118, 0.088),
    (1.14, 0.098, 0.080),
    (1.24, 0.126, 0.092),
    (1.33, 0.150, 0.095),
    (1.42, 0.070, 0.062),
)], cap_start=True, cap_end=True, part="torso")

# one leg, mirrored. The last ring sits on Z=0, so the sole is flat on the floor.
m = b.mark()
b.loft([ring(0.085, 0, z, rx, ry, 8, 2.2) for z, rx, ry in (
    (0.92, 0.092, 0.100),
    (0.62, 0.078, 0.085),
    (0.46, 0.062, 0.068),
    (0.12, 0.062, 0.068),
    (0.00, 0.070, 0.098),
)], cap_start=True, cap_end=True, part="leg")
b.mirror_x(m)

# one arm, mirrored. axis="X" lays the rings in YZ; the radii become Y and Z.
m = b.mark()
b.loft([ring(x, 0, z, r, r, 8, 2.1, axis="X") for x, r, z in (
    (0.14, 0.062, 1.36),
    (0.35, 0.048, 1.35),
    (0.56, 0.038, 1.33),
    (0.70, 0.030, 1.32),
)], cap_start=True, cap_end=True, part="arm")
b.mirror_x(m)

# head
b.loft([ring(0, 0.004, z, rx, ry, 10, 2.1) for z, rx, ry in (
    (1.44, 0.050, 0.055),
    (1.52, 0.072, 0.082),
    (1.60, 0.076, 0.090),
    (1.68, 0.064, 0.076),
    (1.73, 0.038, 0.046),
    (1.75, 0.012, 0.014),
)], cap_start=True, cap_end=True, part="head")

finish("Character", b)
