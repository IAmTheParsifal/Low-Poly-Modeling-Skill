"""PSX low-poly builder: superellipse cross-sections lofted into shells, stitched into
one surface.

Deliberately dumb. No modifiers, no bmesh surgery, no sculpting — every shape is a
table of numbers, so a model is tuned by editing numbers and nothing else. That is what
makes PS1-era shapes converge fast: the whole character is one script you can re-run.

    from psx_build import Build, ring, ring_dir, bridge, finish

    b = Build()
    b.loft([ring(0, 0, z, rx, ry, 12) for z, rx, ry in TORSO], part="torso")
    b.loft(ARM, part="arm")                       # open at both ends
    b.add_faces(bridge(b.v, socket, arm_ring, face_next_to_the_socket), part="shoulder")

Conventions this library assumes (they are the reference models' conventions):
+Z up, character faces -Y, feet on Z=0, metres, one object, one material.

Two ways to join parts, and the second is the one that looks professional:

* butted shells — a limb tube pushed into a torso, capped, hidden under a garment. Fast,
  but the surfaces cross and the seam shows in close-up, and it deforms badly on a rig.
* welded surface — cut a socket in the parent, `bridge()` the limb's first ring into it,
  or share a ring outright (`extrude()` for digits, a split rim for legs). The result is
  one closed shell: `check()` reports 0 boundary edges and the joint is invisible.
"""
import bpy
import bmesh
import math
from mathutils import Vector as V

TAU = math.tau


def ring(cx, cy, cz, rx, ry, n=12, e=2.0, axis="Z", phase=0.0, yoff=None):
    """One closed cross-section.

    e is the superellipse exponent: 2 is a circle, higher is boxier. Useful values:
    2.1 limbs and head, 2.2 legs, 2.3 torso and belt, 2.6 palm.
    axis="X" lays the ring in the YZ plane, for limbs that run along X.
    yoff={vertex_index: dy} pushes individual vertices — that is how a bust bulge,
    a lumbar curve or a seat is made without extra rings.
    """
    pts = []
    for i in range(n):
        a = phase + TAU * i / n
        c, s = math.cos(a), math.sin(a)
        px = math.copysign(abs(c) ** (2.0 / e), c) * rx
        py = math.copysign(abs(s) ** (2.0 / e), s) * ry
        if yoff:
            py += yoff.get(i, 0.0)
        if axis == "Z":
            pts.append(V((cx + px, cy + py, cz)))
        else:
            pts.append(V((cx, cy + px, cz + py)))
    return pts


def ring_dir(c, d, rx, ry, n=4, e=2.0, up=V((0, 0, 1))):
    """Cross-section perpendicular to direction d — chains, fingers, swept tubes.

    d does not need normalising. n=4 is the PS1 look for fingers and chains; 6-8 for
    limbs you want to read as round.
    """
    d = d.normalized()
    u = up.cross(d)
    if u.length < 1e-5:
        u = V((1, 0, 0)).cross(d)
    u.normalize()
    v = d.cross(u).normalized()
    out = []
    for i in range(n):
        a = TAU * i / n + TAU / (2 * n)
        cc, ss = math.cos(a), math.sin(a)
        px = math.copysign(abs(cc) ** (2.0 / e), cc) * rx
        py = math.copysign(abs(ss) ** (2.0 / e), ss) * ry
        out.append(c + u * px + v * py)
    return out


class Build:
    """Accumulates verts/faces plus a per-face smooth flag and a part log."""

    def __init__(self):
        self.v, self.f, self.smooth, self.parts = [], [], [], []

    def add(self, verts, faces, flat=False, part="?"):
        o = len(self.v)
        self.v += [tuple(x) for x in verts]
        self.f += [tuple(i + o for i in fc) for fc in faces]
        self.smooth += [not flat] * len(faces)
        self.parts.append((part, len(verts), len(faces)))
        return o

    def loft(self, rings, cap_start=False, cap_end=False, flat=False, part="?"):
        """Skin a list of equally-sized cross-sections. Caps are single n-gons."""
        n = len(rings[0])
        verts = [p for r in rings for p in r]
        faces = []
        for k in range(len(rings) - 1):
            for i in range(n):
                j = (i + 1) % n
                faces.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
        if cap_start:
            faces.append(tuple(range(n - 1, -1, -1)))
        if cap_end:
            b = (len(rings) - 1) * n
            faces.append(tuple(range(b, b + n)))
        return self.add(verts, faces, flat, part)

    def tube(self, path, rx, ry, n=4, e=2.0, caps=True, part="tube"):
        """Skin a path of points, orienting each ring along the local tangent.

        Use this instead of calling ring_dir yourself: pairing a ring orientation with
        the wrong sweep direction silently collapses the tube into a flat strip.
        rx/ry may be a number or one value per path point (tapered fingers, chains).
        """
        if len(path) < 2:
            raise ValueError("tube needs at least 2 points")
        rxs = list(rx) if isinstance(rx, (list, tuple)) else [rx] * len(path)
        rys = list(ry) if isinstance(ry, (list, tuple)) else [ry] * len(path)
        rings = []
        for i, p in enumerate(path):
            d = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
            if d.length < 1e-9:
                raise ValueError("tube has a duplicate point at index %d" % i)
            rings.append(ring_dir(p, d, rxs[i], rys[i], n, e))
        return self.loft(rings, cap_start=caps, cap_end=caps, part=part)

    def box(self, cx, cy, cz, sx, sy, sz, flat=True, part="box"):
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        vs = [(cx + x, cy + y, cz + z) for x in (-hx, hx) for y in (-hy, hy) for z in (-hz, hz)]
        fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        return self.add(vs, fs, flat, part)

    def mark(self):
        """Bookmark for mirror_x. Returns (vertex count, face count) — not indices."""
        return (len(self.v), len(self.f))

    def add_faces(self, faces, flat=False, part="seam"):
        """Faces that stitch vertices that already exist: bridges, crotch panels, caps
        over an existing ring. Adds no geometry."""
        self.f += [tuple(fc) for fc in faces]
        self.smooth += [not flat] * len(faces)
        self.parts.append((part, 0, len(faces)))

    def extrude(self, base, steps, flat=False, part="digit"):
        """Grow a tube out of four *existing* vertex indices, sharing that base ring.

        `steps` is [(direction, length, scale), ...]. Each new ring is the base quad
        rotated onto the current direction, so a tube can neither twist nor drift off
        its base. This is how fingers and thumbs are welded to a palm.

        Pass indices, never positions: `b.tube(corners, ...)` with corner *coordinates*
        duplicates the base ring, so the digit looks attached in a render and is a
        separate shell. That bug survived a whole review pass.
        """
        quad = [V(self.v[i]) for i in base]
        c0 = sum(quad, V()) / 4
        n0 = (quad[1] - quad[0]).cross(quad[3] - quad[0]).normalized()
        rings, c = [quad], c0
        for d, L, s in steps:
            d = V(d).normalized()
            c = c + d * L
            q = n0.rotation_difference(d)
            rings.append([c + q @ ((p - c0) * s) for p in quad])
        n = len(rings[0])
        off = len(self.v)
        for r in rings[1:]:
            self.v.extend(tuple(p) for p in r)
        loops = [list(base)] + [[off + k * n + i for i in range(n)]
                                for k in range(len(rings) - 1)]
        faces = []
        for k in range(len(loops) - 1):
            a, c2 = loops[k], loops[k + 1]
            for i in range(n):
                j = (i + 1) % n
                faces.append((a[i], a[j], c2[j], c2[i]))
        faces.append(tuple(loops[-1]))          # blunt tip, not a spike
        self.f += faces
        self.smooth += [not flat] * len(faces)
        self.parts.append((part, len(self.v) - off, len(faces)))
        return off

    def mirror_x(self, mark, part="mirror"):
        """Duplicate everything added since `mark`, mirrored in X, winding reversed.

        Returns the vertex offset of the copy, so a seam can be stitched to it: the
        mirrored limb's vertex k lives at `offset + (original_index - mark[0])`.
        """
        v0, f0 = mark
        vsub = self.v[v0:]
        fsub = self.f[f0:]
        sflags = self.smooth[f0:]
        base = len(self.v)
        self.v += [(-x, y, z) for (x, y, z) in vsub]
        self.f += [tuple(base + (i - v0) for i in reversed(fc)) for fc in fsub]
        self.smooth += sflags
        self.parts.append((part, len(vsub), len(fsub)))
        return base


def bridge(verts, a, b, ref):
    """Stitch two open loops together with a band of triangles.

    This is what turns a body from a bag of tubes into one surface: cut a socket in the
    torso, then stitch the limb's first ring into it. Loops may differ in vertex count
    and starting point — each is re-ordered by angle round its own centre, `b` is rotated
    to line up with `a`, then both are walked in step, emitting a triangle whenever one
    side runs out of verts.

    `ref` is a neighbouring face that shares an edge of the seam; the band is wound to
    agree with it (two faces must walk a shared edge in opposite directions). Do not
    decide the winding from a normal vote: for a band that wraps a limb the normals sum
    to roughly zero and the vote is noise.
    """
    def ring_of(loop):
        pts = [V(verts[i]) for i in loop]
        c = sum(pts, V()) / len(pts)
        n = V((0.0, 0.0, 0.0))
        for k in range(len(pts)):
            n = n + (pts[k] - c).cross(pts[(k + 1) % len(pts)] - c)
        n = n.normalized() if n.length > 1e-9 else V((0.0, 0.0, 1.0))
        u = pts[0] - c
        u = (u - n * u.dot(n)).normalized()
        w = n.cross(u)
        ang = [math.atan2((p - c).dot(w), (p - c).dot(u)) % TAU for p in pts]
        order = sorted(range(len(pts)), key=lambda k: ang[k])
        return [loop[k] for k in order], [ang[k] for k in order]

    a2, aa = ring_of(a)
    b2, ba = ring_of(b)
    k0 = min(range(len(b2)), key=lambda k: abs((ba[k] - aa[0] + math.pi) % TAU - math.pi))
    b2 = b2[k0:] + b2[:k0]
    n, m = len(a2), len(b2)
    faces, i, j = [], 0, 0
    while i < n or j < m:
        if j >= m or (i < n and i * m <= j * n):
            faces.append((a2[i % n], a2[(i + 1) % n], b2[j % m]))
            i += 1
        else:
            faces.append((a2[i % n], b2[(j + 1) % m], b2[j % m]))
            j += 1
    redges = set((ref[i], ref[(i + 1) % len(ref)]) for i in range(len(ref)))
    for f in faces:
        for i in range(len(f)):
            if (f[i], f[(i + 1) % len(f)]) in redges:
                return [tuple(reversed(x)) for x in faces]
    return faces


def _material(name, color, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def check(ob, boundary=0, verbose=True):
    """The gate every build has to pass. Returns True when clean.

    `boundary` is the number of single-sided edges you are willing to ship: 0 for a
    closed body, higher only for deliberate single-sided decals (glasses lenses, cards).
    Counting boundary edges is also *the* test of whether two parts are really welded —
    a digit that was meant to share a ring but copied it shows up here, not in a render.
    """
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    loose_v = sum(1 for v in bm.verts if not v.link_faces)
    loose_e = sum(1 for e in bm.edges if not e.link_faces)
    degen = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
    edge1 = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    ngon = sum(1 for f in bm.faces if len(f.verts) > 4)
    dup = len(bm.verts) - len({tuple(round(c, 5) for c in v.co) for v in bm.verts})
    bm.free()
    ok = not (loose_v or loose_e or degen or nonman or ngon or dup) and edge1 <= boundary
    if verbose:
        print("CHECK loose_v=%d loose_e=%d zero_area=%d nonmanifold=%d ngon=%d "
              "coincident=%d boundary=%d (allowed %d) -> %s"
              % (loose_v, loose_e, degen, nonman, ngon, dup, edge1, boundary,
                 "ok" if ok else "FIX THIS"))
    return ok


def report(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    bb = [ob.matrix_world @ V(c) for c in ob.bound_box]
    print("RESULT verts=%d faces=%d tris=%d quads=%d tris=%d ngons=%d" % (
        len(me.vertices), len(me.polygons), tris,
        sum(1 for p in me.polygons if len(p.vertices) == 4),
        sum(1 for p in me.polygons if len(p.vertices) == 3),
        sum(1 for p in me.polygons if len(p.vertices) > 4)))
    print("HEIGHT %.3f m   BBOX x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % (
        max(p.z for p in bb) - min(p.z for p in bb),
        min(p.x for p in bb), max(p.x for p in bb),
        min(p.y for p in bb), max(p.y for p in bb),
        min(p.z for p in bb), max(p.z for p in bb)))
    if abs(min(p.z for p in bb)) > 1e-4:
        print("WARNING object does not sit on Z=0")


def finish(name, *builds, material="PSX", color=(0.34, 0.32, 0.34, 1), roughness=0.75,
           uv_angle=1.15, uv_margin=0.005, uv=True, verbose=True):
    """Merge one or more Builds into a single object, shade, UV, verify.

    Replaces any existing object of the same name, so a build script is safe to re-run.
    Returns the object.
    """
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for ob in [o for o in bpy.data.objects if o.name.startswith(name)]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)

    verts, faces, smooth = [], [], []
    for b in builds:
        o = len(verts)
        verts += b.v
        faces += [tuple(i + o for i in fc) for fc in b.f]
        smooth += b.smooth
        if verbose:
            for part, nv, nf in b.parts:
                print("   %-14s v=%-4d f=%d" % (part, nv, nf))

    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(_material(material, color, roughness))
    # validate() can drop faces, which would shift the smooth flags onto the wrong ones
    if len(me.polygons) == len(smooth):
        for p, s in zip(me.polygons, smooth):
            p.use_smooth = s
    else:
        for p in me.polygons:
            p.use_smooth = True

    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob

    bm = bmesh.new()
    bm.from_mesh(me)
    # tidy before normals: weld anything that landed on top of itself, and break the
    # single-n-gon caps into triangles so the asset is only ever quads and tris.
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big:
        bmesh.ops.triangulate(bm, faces=big)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

    if uv:  # placeholder atlas: islands, not a real layout
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=uv_angle, island_margin=uv_margin)
        bpy.ops.object.mode_set(mode="OBJECT")

    if verbose:
        report(ob)
    check(ob)
    return ob
