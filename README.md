# Low-Poly-Modeling-Skill

A skill for AI coding agents that model **PS1/PSX-style low-poly assets in Blender**.

Not a modeling tutorial. It is the working method that converges fast: block with lofts,
judge in clay, correct numbers instead of vertices, and verify with the same gate every
time. It also carries the list of failure modes that cost the most round trips, so the
next attempt doesn't rediscover them.

Built from a study of three real PS1-era reference models and one finished character.

## What's here

| file | what it is |
|---|---|
| `SKILL.md` | the skill: conventions, API, workflow, traps, review gate |
| `scripts/psx_build.py` | the library — superellipse rings, lofts, swept tubes, mirroring, finish, geometry gate |
| `scripts/preview.py` | ortho clay renders; shots derived from the object's bounding box |
| `scripts/compare.py` | stats table + side-by-side render against reference models |
| `scripts/measure_silhouette.py` | width-at-height scan of a reference image |
| `examples/minimal_character.py` | ~60 line end-to-end blockout |
| `tests/test_measure_stub.py` | runs the measuring tool against a synthetic image, no Blender needed |

## Install

Copy or link this folder into your agent's skills directory so that `SKILL.md` sits at its
root:

```
~/.config/opencode/skills/ps1-modeling/     # OpenCode
~/.claude/skills/ps1-modeling/              # Claude Code
```

On Windows a junction is enough and keeps one copy:

```powershell
cmd /c mklink /J "%USERPROFILE%\.config\opencode\skills\ps1-modeling" "F:\path\to\Low-Poly-Modeling-Skill"
```

## Use

The scripts run inside Blender (they need `bpy`). From the repo root:

```python
import sys; sys.path.insert(0, "scripts")

exec(open("examples/minimal_character.py").read())   # build
exec(open("scripts/preview.py").read())              # render clay views
exec(open("scripts/compare.py").read())              # after setting REFS
```

Each harness has its config at the top: `OBJECT`, `OUT`, and for `compare.py` a `REFS` list
of reference models to scale and line up against the build.

## The conventions it enforces

+Z up · character faces −Y · feet on Z=0 · metres · one object · one material · one
256²–512² atlas · smooth-shaded body with faceted hair · no normal maps, PBR or shape keys ·
no loose or degenerate geometry · 600–1600 tris for a bare body, more once hair and
accessories are added.

## License

MIT — see `LICENSE`.
