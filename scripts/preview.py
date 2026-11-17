"""Clay preview renders for a PSX build.

Run after the build script, in the same Blender session. Flat grey studio, no textures,
so only silhouette and shading are judged — the way a PS1 asset is actually judged.

Shots are generated from the object's bounding box, so this works for any character or
prop. Override SHOTS if you want specific framings.

    import bpy
    for f in ("scripts/psx_build.py", "scripts/preview.py"): ...
    preview.run()
"""
import bpy
import math
import os
from mathutils import Vector as V

OBJECT = "Character"
OUT = os.path.join(os.path.dirname(bpy.data.filepath) or os.path.expanduser("~"), "psx_preview")

# None = derive from the bounding box. Otherwise: (name, look-at, ortho width, azimuth,
# elevation, resolution). Azimuth 0 looks at the front (-Y), 90 at the left side.
SHOTS = None


def setup(sc):
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.245, 0.247, 0.247, 1)
    bg.inputs[1].default_value = 0.9
    for name, loc, energy, size in (("K", (2.5, -3.5, 3.2), 420, 4),
                                    ("F", (-3.5, -2.2, 1.2), 180, 5),
                                    ("R", (0.6, 3.2, 2.4), 220, 4)):
        light = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
        light.energy = energy
        light.size = size
        ob = bpy.data.objects.get(name)
        if not ob:
            ob = bpy.data.objects.new(name, light)
            sc.collection.objects.link(ob)
        elif ob.name not in sc.objects:
            # the light datablock can outlive its scene link (a leaked temp scene did
            # this once) and every render then comes out black — relink it
            sc.collection.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (V((0, 0, 1.1)) - V(loc)).to_track_quat("-Z", "Y").to_euler()


def shot(sc, name, center, ortho, azim, elev=0.0, res=(560, 860)):
    cam = bpy.data.objects.get("PrevCam")
    if not cam:
        cam = bpy.data.objects.new("PrevCam", bpy.data.cameras.new("PrevCam"))
    if cam.name not in sc.objects:
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ortho
    a, e = math.radians(azim), math.radians(elev)
    d = 8.0
    # the horizontal part has to shrink with elevation or the frame drifts off target
    cam.location = V(center) + V((math.sin(a) * d * math.cos(e),
                                 -math.cos(a) * d * math.cos(e),
                                 math.sin(e) * d))
    cam.rotation_euler = (math.radians(90) - e, 0, a)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("shot", name)


def auto_shots(h, w):
    res = (560, 860)
    # ortho_scale follows the LONGER resolution side (here: height), so fit both dims
    ortho = 1.10 * max(h, w * res[1] / res[0])
    shots = [("body_" + nm, (0, 0, h * 0.5), ortho, az, 0, res)
             for nm, az in (("front", 0), ("side", 90), ("back", 180), ("q34", 35))]
    shots.append(("closeup_upper", (0, 0, h * 0.86), h * 0.34, 35, 0, (520, 600)))
    shots.append(("closeup_lower", (0, 0, h * 0.16), h * 0.34, 35, 0, (520, 600)))
    return shots


def run():
    sc = bpy.context.scene
    os.makedirs(OUT, exist_ok=True)
    setup(sc)
    ob = bpy.data.objects[OBJECT]
    bb = [ob.matrix_world @ V(c) for c in ob.bound_box]
    h = max(p.z for p in bb) - min(p.z for p in bb)
    w = max(p.x for p in bb) - min(p.x for p in bb)

    clay = bpy.data.materials.get("Clay") or bpy.data.materials.new("Clay")
    clay.use_nodes = True
    bsdf = next(n for n in clay.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.53, 0.54, 1)
    bsdf.inputs["Roughness"].default_value = 0.68
    sc.view_layers[0].material_override = clay

    for s in (SHOTS if SHOTS is not None else auto_shots(h, w)):
        shot(sc, *s)

    sc.view_layers[0].material_override = None
    print("preview ->", OUT)
