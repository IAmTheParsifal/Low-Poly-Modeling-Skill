"""Compare the current build against reference models: a stats table, plus a side-by-side
front render with every model scaled to the same height.

Reference models are imported, scaled, laid out and deleted again — nothing is left in
the scene. Missing files are skipped, so the REFS list can outlive the files.

Put your reference models next to this script and list them:

    REFS = [("basemesh", r"refs/lowpoly_basemesh_male.fbx")]
"""
import bpy
import math
import os
from mathutils import Vector as V

OBJECT = "Character"
REFS = []
OUT = os.path.join(os.path.dirname(bpy.data.filepath) or os.path.expanduser("~"), "psx_compare")


def mesh_stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    return len(me.vertices), len(me.polygons), tris


def bounds(ob):
    lo = V((1e9, 1e9, 1e9))
    hi = V((-1e9, -1e9, -1e9))
    for c in ob.bound_box:
        w = ob.matrix_world @ V(c)
        lo = V((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
        hi = V((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def import_ref(path, height):
    """Import an FBX, drop its rig, bake transforms, scale to `height`, centre on X/Y."""
    before = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.data.objects if o.name not in before and o.type == "MESH"]
    if not meshes:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    # keep the world transform when detaching: rigs are commonly 0.01 scale with a
    # 100-scale mesh parented to them, and clearing without KEEP_TRANSFORM loses that
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in [o for o in bpy.data.objects if o.name not in before and o.type == "ARMATURE"]:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo, hi = bounds(ob)
    s = height / max(hi.z - lo.z, 1e-6)
    ob.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    lo, hi = bounds(ob)
    # centre on the bbox centre, not the min, or the models never line up
    ob.location = V((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    bpy.ops.object.transform_apply(location=True)
    return ob


def lay_out(obs, gap=0.12):
    """Spread objects left to right on X, centred on the origin. Returns total width."""
    x = 0.0
    for ob in obs:
        lo, hi = bounds(ob)
        ob.location.x += x - lo.x
        x += (hi.x - lo.x) + gap
    total = x - gap
    for ob in obs:
        ob.location.x -= total / 2
    bpy.context.view_layer.update()
    return total


def run():
    sc = bpy.context.scene
    os.makedirs(OUT, exist_ok=True)
    ob = bpy.data.objects[OBJECT]
    lo, hi = bounds(ob)
    height = hi.z - lo.z
    home = V(ob.location)

    rows = [(OBJECT, "this build") + mesh_stats(ob) + (height,)]
    imported = []
    for label, path in REFS:
        if not os.path.exists(path):
            print("skip missing reference:", label, path)
            continue
        ref = import_ref(path, height)
        if ref is None:
            print("skip reference with no mesh:", label)
            continue
        imported.append(ref)
        rows.append((label, "reference") + mesh_stats(ref) + (height,))

    print("%-16s %-10s %6s %6s %6s %7s" % ("MODEL", "ROLE", "verts", "faces", "tris", "height"))
    for name, role, v, f, t, h in rows:
        print("%-16s %-10s %6d %6d %6d %7.3f" % (name, role, v, f, t, h))

    if not imported:
        print("no references imported — nothing to render")
        return

    allobs = [ob] + imported
    total = lay_out(allobs)

    clay = bpy.data.materials.get("Clay") or bpy.data.materials.new("Clay")
    clay.use_nodes = True
    bsdf = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.53, 0.54, 1)
    bsdf.inputs["Roughness"].default_value = 0.68
    sc.view_layers[0].material_override = clay

    if not any(o.type == "LIGHT" for o in bpy.data.objects):
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
        sc.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(55), 0, math.radians(35))
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.245, 0.247, 0.247, 1)
    bg.inputs[1].default_value = 1.0
    sc.render.engine = "BLENDER_EEVEE"
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.look = "None"

    cam = bpy.data.objects.get("PrevCam")
    if not cam:
        cam = bpy.data.objects.new("PrevCam", bpy.data.cameras.new("PrevCam"))
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = total * 1.10
    cam.location = V((0, -8, height * 0.5))
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1000, 760
    sc.render.filepath = os.path.join(OUT, "compare_front.png")
    bpy.ops.render.render(write_still=True)
    print("shot compare_front ->", OUT)

    # put the scene back the way it was
    ob.location = home
    sc.view_layers[0].material_override = None
    for ref in imported:
        me = ref.data
        bpy.data.objects.remove(ref, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    bpy.context.view_layer.update()


run()
