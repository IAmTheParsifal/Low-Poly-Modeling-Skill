# Changelog

Dated, because this is a working skill rather than a library with versions. Format
borrowed from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); dates are the day
the change landed on `main`.

Everything under "the character" describes the 1.72 m gothic girl the skill was written
on, which is also the skill's test case: a lesson only goes in `SKILL.md` after it survived
a build and a render pass on her.

## 2026-11-18 — Second character: male, and a shoulder that finally works

### Added

- **A second character built with the skill** (the real test of whether the lessons
  generalise): 1.81 m male, A-pose, leather jacket with a zip bead and cuffs over a tee,
  bootcut jeans, slim classic boots, short sloppy hair. **1202 v / 2372 tris**, gate clean.
- **The reference shoulder, copied properly.** The v2 basemesh dumps (`tools/v2_*.obj`)
  show an arm root as tall as the deltoid (~110 mm) welded into the torso's side. The
  socket is now a 2×2 quad cut whose eight rim verts *are* the arm's ring 0: no stitch
  band, no shelf, no shoulder pad. Two rounds of the previous approach (a 40 mm slot plus a
  swelling deltoid) could not get there.
- Trap 23: a 2×2 cut orphans the vert at the hole's centre — delete loose verts in the tidy
  before `remove_doubles`.
- Trap 24: garment edges are radius steps in one surface (tee hem, jacket hem, trouser
  cuff, zip bead), and a hard part like a sole can be a second loft that shares its
  boundary ring.
- **The decision to split body and clothing meshes** for the next character, with the
  budget and gate consequences written down.

### Changed

- `preview.py` takes `(name, mat, out, h, hand)`, so one harness renders any build; the
  hair is now marked by its material slot instead of flat shading + height.
- The socket doctrine in `SKILL.md`: "two quads wide by one band" was the old rule. A
  shoulder is now "as tall as the joint, and the hole's rim *is* the limb's first ring"; the
  old rule survives only where a socket cannot be sized to the joint.
- Boots: 72 mm ankle (was 90), 18 mm flat-shaded sole and welt, shaft top hidden up inside
  the trouser, pointed toe. Jeans flare from a 136 mm knee to a 190 mm hem.

### Fixed

- Short hair no longer draws a dark slab across the cheekbone: the face-slot columns fold
  straight back into the skull instead of sinking radially. The thick-mane trick does not
  survive 20 mm of hair.
- Two loose verts at the socket centres — caught by the gate, invisible in every render.

## 2026-11-18 — Geometry correction

### Added

- **12-column skull.** Columns at ±22.5° give the eye pair vertices of their own, plus a
  brow ring ahead of the eye ring, a 2 mm socket recess and cheekbone/hollow offsets. The
  skull's lowest ring is 12 verts like the neck rim, so the neck bridge is a straight 1:1
  band instead of an 8-into-12 fan.
- Trap: **a socket cut must match the table it indexes** — a one-band error is invisible
  in the numbers you are tuning.
- Trap: **faces need columns where eyes go**, and keep the offsets small; plus the fact
  that all five reference FBX files are 100% smooth-flagged yet render faceted because they
  carry baked split normals.
- Trap: **mark hair by its flat shading, not by "the last N faces"** after a join+tidy.
- Trap: **Workbench shadow acne looks like z-fighting** (the belt's dotted line).
- This changelog.

### Changed

- Exercised size is now **1167 v / 2308 tris** (was 1127 / 2228); README renders
  regenerated, captions updated, and the head caption now names the skull work.
- README's future plans drop geometry correction (done) and keep animating, texturing and
  UV correction.
- Project skill: the "Deliberately not done yet" section now says the sockets and brow are
  modelled and only the mouth/eyes remain painted; review-pass framing numbers corrected to
  the ones actually used (1.80 at 820 × 900).

### Fixed

- **Shoulder socket cut from the wrong band.** The comment said the slot came out of the
  armpit band (rings 8–9); the code cut `k == 9`, the shelf above it. The arm was stitched
  into the shoulder shelf, so the deltoid rose above the trapezius and the seam read as a
  valley with a flap. The arm's first ring now sits on the rim's bowed plane 3 mm proud and
  the deltoid's top lands on the shelf.
- **Preview hair pass.** "The last N faces are the hair" stopped being true once the join
  and the tidy pass reordered polygons, so the dark-hair pass was recolouring scattered
  faces. Now selects flat-shaded faces above the waist, excluding the nose.

## 2026-11-17 — A-pose and the seat

### Added

- **Pose after welding, don't model posed**: 35° arm drop with the angle ramped along x
  about the shoulder socket, plus a rigid 25° wrist break about the wrist ring, both before
  `mirror_x` so both sides come free.
- Reference study of the two `*_version_2` bases: 451/447 verts, 880 tris each, 47-bone
  UE4-style rigs, A-pose, hands shipped as separate cuff shells, three digit chains.
- `tools/dump_ref.py` as a reusable FBX study harness (structural JSON + clay renders).

### Changed

- Crotch points moved onto the cleft/buttock line (back `y 0.072, z 0.888`; front
  `y −0.060, z 0.880`).
- Preview harness: bbox-based framing, hand shots centred on the *posed* hand, lights and
  camera relinked if a datablock loses its scene link, no render on module import.

### Fixed

- **Seat fin.** The old rear crotch point closed the buttock with an edge-on quad that
  rendered as a sharp fin.
- **Leaked study scene.** A ref-study run died mid-way and left its temp scene active; the
  next build landed in it (no lights, no camera) and a whole render pass came out black.
  Temp scenes are now torn down in a `finally` at the call site.

## 2026-11-16 — Weld doctrine

### Added

- `bridge()` seam stitching (mismatched loop counts, angle-ordered merge walk, winding
  taken from a neighbouring face), welded digit extrusion, and the pelvis rim split
  six-and-six with two shared crotch verts.
- "One surface, not a bag of parts": limbs grow out of cut sockets, they are not pushed
  into the body and hidden under a garment.
- Numeric gate: 0 boundary, 0 non-manifold, 0 n-gons, 0 zero-area, 0 loose, 0 coincident.
- Development renders and a future-plans section in the README.

### Fixed

- Butted shells at the shoulders, wrists, hips, ankles and neck rebuilt as shared rings.

## 2026-11-15 — First release

### Added

- `SKILL.md`: conventions, builder API, workflow, traps, review gate.
- `scripts/psx_build.py` (superellipse rings, lofts, mirror, finish, checks),
  `scripts/preview.py`, `scripts/compare.py`, `scripts/measure_silhouette.py`.
- `examples/minimal_character.py`, `tests/smoke_weld.py`, `tests/test_measure_stub.py`.

## 2026-11-14 — Initial commit

- Repository scaffold.
