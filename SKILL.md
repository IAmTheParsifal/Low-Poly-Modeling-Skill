---
name: ps1-modeling
description: "Use when modeling, refining or reviewing a PS1/PSX-style low-poly character or prop in Blender — a retro game asset, a low-poly portrait from a turnaround reference, a faceted-hair game mesh, or anything that has to match the poly budget and conventions of PlayStation 1 assets. Covers the procedural build-script workflow, the loft library, measuring a reference for proportions, budgets, and the failure modes that cost the most time."
---

# PS1 / PSX low-poly modeling

## What the style is

PS1 style = **small poly budget + one painted texture atlas**. It is *not* flat shading.
The body is smooth-shaded; only hair and hard props stay faceted. Flat-shading the whole
model reads as 2005 low-poly, not 1997. Detail lives in the texture, so the mesh is judged
on silhouette and edge flow — never on surface detail.

## Conventions (measured from real PS1-era reference models, not guessed)

- +Z up, character faces **−Y**, feet on **Z=0**, metres.
- One object, one material, one texture atlas. The clothes *are* the mesh; there are no
  separate garment objects.
- 100% smooth shading, except hair and hard-surface props.
- No normal maps, no PBR, no shape keys.
- No loose vertices, no loose edges, no zero-area faces, no non-manifold garbage.
- Quads for body shells, triangles only where a shape needs them (tips, caps).

Budgets from three shipped reference models:

| model | verts | tris | notes |
|---|---|---|---|
| rigged male basemesh | 772 | 1540 | 84 bones, 256² atlas, A-pose, 1.98 m |
| Walking (PSXProp) | 349 | 645 | all tris, 512² atlas, T-pose, 1.77 m |
| LE0GAR | 548 | 943 | 9 objects, one 256² atlas, Rigify, 2.4 m |

That is a rigged **bare body**. Hair volume and accessories legitimately push past it — a
1225 v / 2294 tri character with a full mane, glasses, belt and boots is still a PS1
character. Never cut silhouette to hit a number derived from a bare body.

## Setup

`scripts/psx_build.py` is the library; the two harnesses are config-at-the-top scripts.

```
scripts/psx_build.py           ring / ring_dir / Build / finish / check / report
scripts/preview.py             ortho clay renders, shots derived from the bbox
scripts/compare.py             stats table + side-by-side against reference FBX/OBJ models
scripts/measure_silhouette.py  width-vs-height scan of a reference PNG
```

Put `scripts/` on `sys.path` and import, or copy a harness next to your build script.
Everything runs inside Blender:

```python
import sys
sys.path.insert(0, r"…/scripts")
from psx_build import Build, ring, finish
```

## The API

```python
ring(cx, cy, cz, rx, ry, n=12, e=2.0, axis="Z", phase=0.0, yoff=None)
```
One closed cross-section. `e` is the superellipse exponent: 2 = circle, higher = boxier.
Useful: 2.1 limbs and head, 2.2 legs, 2.3 torso and belt, 2.6 palm. `axis="X"` lays the
ring in YZ for limbs along X. `yoff={index: dy}` pushes single vertices — that is how a
bust bulge, lumbar curve or seat is made without adding rings.

```python
Build.loft(rings, cap_start=..., cap_end=..., flat=..., part="…")
Build.tube(path, rx, ry, n=4, e=2.0, caps=True, part="…")
Build.box(cx, cy, cz, sx, sy, sz, flat=True, part="…")
Build.add(verts, faces, flat=..., part="…")
Build.mark() → pass to Build.mirror_x(mark)
```
`tube()` takes a path of points and orients each ring along the local tangent — use it for
chains, fingers and anything swept. `rx`/`ry` may be lists, one per point, for tapering.

```python
finish(name, *builds, material=..., color=..., uv=True)
check(ob)    # the gate: loose verts / edges / zero-area faces must be 0
report(ob)   # verts, faces, tris, bbox, height
```
`finish()` merges one or more `Build`s into a single object, applies smooth flags per face,
makes the material, recalculates normals, adds placeholder UVs and prints the build report.
It replaces any existing object of the same name, so a build script is safe to re-run.

## Workflow

1. **Measure the reference before modelling.** Run `scripts/measure_silhouette.py` on the
   turnaround: it prints silhouette width at every 3% of height. Write the table down.
   Eyeballing proportions is the single biggest source of rounds lost — a waist 2 cm off
   does not read as "slightly wrong", it reads as a different character.
2. **Block with lofts.** One `Build`, parts in order: torso → legs → feet → arms → hands →
   mirror → head → hair → accessories. Read the printed PARTS log after every build; it
   tells you which part is eating polys.
3. **Render clay, not shaded.** `preview.py`, grey background, no textures. Judge only
   silhouette and the shading break where surfaces meet.
4. **Compare against reference models**, not just the image. `compare.py` scales everything
   to one height and prints verts/tris side by side. It catches short arms and flat depth
   faster than looking.
5. **Gate.** `check()` clean, feet on Z=0, tri count in budget.
6. **Save a copy.** `bpy.ops.wm.save_as_mainfile(filepath=…, copy=True)` writes the file
   without hijacking the session's current filepath.

## Traps — each one of these cost at least one round trip

1. **Separate shells always cross.** Two lofts of similar radius produce a jagged seam
   wherever their surfaces intersect, and no amount of tweaking hides it. Let the *outer
   garment* own the joint: the trousers form the hips, the torso tapers to a small cap
   buried inside them, and the crossover hides under the belt (belt wider than the body).
   Same trick at arm→shoulder and trouser-hem→boot.
2. **A cap that pokes out reads as a torn edge.** A cap sharing a Z with another shell
   makes a visible jagged ring. Keep caps strictly inside the other shell, or don't cap.
3. **Fill the crotch.** Two overlapping leg tubes leave a deep valley at x=0. Bridge it
   with a narrow torso cone whose front is level with the trousers. Too thin and you get a
   black groove; too wide and you get a diaper.
4. **Hair: don't cut the face slot out of the shell.** For each row, columns inside the slot
   get a radial scale around 0.45 plus a small +Y push, ramping to full radius roughly 10°
   past the slot half-angle (26–34° by row). The quad leaving the head then leaves at the
   cheek instead of across the face. A 30° ramp puts hair over the whole face; shrink
   without the push leaves a big pale inner wall beside the cheek.
5. **Never alternate a fringe hem by column parity.** `j % 2` on an even column count puts
   a deep tooth notch dead centre. Use a smooth function of the column angle.
6. **Hair is a closed lofted volume, not cards** — e.g. 20 columns × 11 rows, flat-shaded,
   with per-vertex wobble for the chopped look. Sweep the lower rows backwards or the
   profile reads as a hood.
7. **Chains float.** Keep a necklace arc within a few millimetres of the chest surface or
   it reads as wire hanging in space in three-quarter views.
8. **Normalise every direction vector** before scaling by a length. An unnormalised one
   produced a 1 m thumb.
9. **`mirror_x` takes `(len(v), len(f))` from `mark()`**, and mirrored faces need reversed
   winding. Passing vertex indices corrupts the mesh silently.
10. **Never `join()` without deselecting all first.** A leftover default cube gets absorbed
    into the character. Filter selection by object name.
11. **Reference FBX imports** need `parent_clear(type="CLEAR_KEEP_TRANSFORM")` *before* the
    armature is deleted — rigs are commonly 0.01 scale with a 100-scale mesh parented to
    them. Then apply transforms and centre on the **bbox centre**, not the bbox min, or the
    models never line up.
12. **Elevated preview cameras**: the horizontal offset must scale by `cos(elev)`, or the
    shot frames empty background.
13. **Run the gate on geometry, not on the render.** A degenerate quad can look fine in a
    front view and wreck the wireframe. `check()` exists for that.

## Review pass

`preview.py` gives four full-body views plus two close-ups, all derived from the object's
bbox. Look for: jagged shell crossings, caps showing as flat ledges, the crotch, garment
junctions, whether the hair profile is hair or a hood, whether the face slot is clear.

Final gate:

```python
from psx_build import check
check(ob)   # loose verts, loose edges, zero-area faces → all 0
```
plus: bbox `z.min == 0`, height, tri count, smooth flags correct.

## Worked example — one real character

A 1.744 m gothic girl, T-pose, mesh only, built with this library: 1225 verts / 1079 faces
/ 2294 tris, 26 n-gons (caps), 4 triangles, everything else quads; feet at 0; one material,
one placeholder UV map.

Measured widths from its reference sheet (z → silhouette width in metres), which is what
the body tables were built from:

| z | width | | z | width |
|---|---|---|---|---|
| 1.66 | 0.245 | | 1.05 | 0.242 |
| 1.575 | 0.322 | | 0.96 | 0.295 |
| 1.49 | 0.349 | | 0.875 | 0.314 |
| 1.40 | 0.403 | | 0.61 | 0.330 |
| 1.225 | 0.265 | | 0.26 | 0.452 |
| 1.14 | 0.180 | | 0.0525 | 0.449 |

The numbers matter less than the method: one table, one pass of lofts, then numeric
corrections driven by renders. In that build, arm length was the one thing that needed the
reference *models* rather than the image — the image's arms droop ~20°, so its horizontal
span (1.457 m) understates the true arm length. Compare against a T-posed reference model
for anything measured at an angle.

## Out of scope here

Texturing, rigging and export. Placeholder UVs from `smart_project` are islands, not a
real atlas. When texturing starts: one 256² or 512² atlas, keep hair's inner surfaces on a
dark region so the shell edges read as depth, and paint the face — the mesh stays a mask.
