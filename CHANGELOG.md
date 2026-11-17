# Changelog

Dated, because this is a working skill rather than a library with versions. Format
borrowed from [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); dates are the day
the change landed on `main`.

Everything under "the character" describes the 1.72 m gothic girl the skill was written
on, which is also the skill's test case: a lesson only goes in `SKILL.md` after it survived
a build and a render pass on her.

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
