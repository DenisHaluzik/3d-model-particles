"""
ŽRALOK V BLENDERU - Skript s armaturou a 6 klouby
===================================================
Jak použít:
  1. Otevři Blender
  2. Přejdi do "Scripting" workspace (záložka nahoře)
  3. Klikni na "New" pro nový skript
  4. Zkopíruj celý tento kód a vlož ho do editoru
  5. Stiskni "Run Script" (šipka ▶ nebo Alt+P)
  6. Žralok se objeví ve scéně se 6 klouby a wave animací!

Klouby (bones):
  1. Root       - kořen těla
  2. Body_Mid   - střed těla
  3. Body_Back  - zadní část těla
  4. Tail_Base  - základ ocasu
  5. Tail_Mid   - střed ocasu
  6. Tail_Tip   - špička ocasu

Animace: vlnivý pohyb ocasu (frame 1-60, smyčka)
"""

import bpy
import math
from mathutils import Vector

# ── Vymazání scény ──────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# ── Pomocné funkce ──────────────────────────────────────────────────────────

def add_keyframe_rotation(bone, frame, rx=0, ry=0, rz=0):
    """Přidá keyframe rotace pro pose bone."""
    bone.rotation_mode = 'XYZ'
    bone.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
    bone.keyframe_insert(data_path="rotation_euler", frame=frame)


# ── 1. ARMATURA (kostra se 6 klouby) ───────────────────────────────────────

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm_obj = bpy.context.object
arm_obj.name = "Shark_Armature"
arm = arm_obj.data
arm.name = "Shark_Bones"

# Smazání výchozího bone
for b in arm.edit_bones:
    arm.edit_bones.remove(b)

# Definice kostí: (název, hlava, ocas, rodič)
BONES = [
    ("Root",       (0,  0,    0),    (0,  0.6,  0),    None),
    ("Body_Mid",   (0,  0.6,  0),    (0,  1.4,  0),    "Root"),
    ("Body_Back",  (0,  1.4,  0),    (0,  2.2,  0),    "Body_Mid"),
    ("Tail_Base",  (0,  2.2,  0),    (0,  2.9,  0),    "Body_Back"),
    ("Tail_Mid",   (0,  2.9,  0),    (0,  3.5,  0),    "Tail_Base"),
    ("Tail_Tip",   (0,  3.5,  0),    (0,  4.0,  0),    "Tail_Mid"),
]

created = {}
for name, head, tail, parent_name in BONES:
    b = arm.edit_bones.new(name)
    b.head = Vector(head)
    b.tail = Vector(tail)
    if parent_name:
        b.parent = created[parent_name]
        b.use_connect = True
    created[name] = b

bpy.ops.object.mode_set(mode='OBJECT')
arm_obj.show_in_front = True


# ── 2. TĚLO ŽRALOKA ─────────────────────────────────────────────────────────

def make_shark_body():
    """Vytvoří tvar žraloka pomocí UV sphere + modifikátorů."""

    # Hlavní tělo - protáhlá koule
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32, ring_count=24,
        radius=1.0, location=(0, 0, 0)
    )
    body = bpy.context.object
    body.name = "Shark_Body"

    # Natáhneme tělo do tvaru žraloka
    body.scale = (0.35, 2.0, 0.28)
    body.location = (0, 0.8, 0)

    # Shade smooth
    bpy.ops.object.shade_smooth()

    # Subsurf modifier
    mod = body.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = 2
    mod.render_levels = 3

    return body


def make_fin(name, location, rotation, scale):
    """Vytvoří ploutev."""
    verts = [
        (0,    0,    0),
        (0,    0.8,  0),
        (0,    0.4,  0.7),
        (0,   -0.1,  0.5),
    ]
    faces = [(0, 1, 2), (0, 2, 3)]
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    return obj


# Tělo
body = make_shark_body()

# Hřbetní ploutev
dorsal = make_fin("Dorsal_Fin",
    location=(0, 1.2, 0.28),
    rotation=(0, 0, 0),
    scale=(0.5, 0.6, 0.8))

# Levá prsní ploutev
pec_l = make_fin("Pectoral_Fin_L",
    location=(-0.35, 0.9, 0),
    rotation=(math.radians(90), math.radians(-30), math.radians(-40)),
    scale=(0.45, 0.55, 0.3))

# Pravá prsní ploutev
pec_r = make_fin("Pectoral_Fin_R",
    location=(0.35, 0.9, 0),
    rotation=(math.radians(-90), math.radians(30), math.radians(40)),
    scale=(0.45, 0.55, 0.3))

# Ocasní ploutev (svislá)
tail_v = make_fin("Tail_Fin_V",
    location=(0, 3.85, 0),
    rotation=(math.radians(0), math.radians(0), math.radians(-20)),
    scale=(0.15, 0.5, 0.6))

# Ocasní ploutev (vodorovná)
tail_h = make_fin("Tail_Fin_H",
    location=(0, 3.85, 0),
    rotation=(math.radians(90), math.radians(0), math.radians(-20)),
    scale=(0.15, 0.3, 0.4))

# Hlava / čumák - kužel
bpy.ops.mesh.primitive_cone_add(
    vertices=20, radius1=0.3, radius2=0.0,
    depth=0.7, location=(0, -0.55, 0)
)
snout = bpy.context.object
snout.name = "Shark_Snout"
snout.rotation_euler = (math.radians(90), 0, 0)
snout.scale = (0.85, 1.0, 0.65)
bpy.ops.object.shade_smooth()

# Oči
for side, x in [("L", -0.3), ("R", 0.3)]:
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.045, location=(x, 0.05, 0.18)
    )
    eye = bpy.context.object
    eye.name = f"Eye_{side}"
    mat = bpy.data.materials.new(f"Eye_Mat_{side}")
    mat.diffuse_color = (0.02, 0.02, 0.02, 1.0)
    eye.data.materials.append(mat)


# ── 3. MATERIÁL ──────────────────────────────────────────────────────────────

shark_mat = bpy.data.materials.new("Shark_Material")
shark_mat.use_nodes = True
nodes = shark_mat.node_tree.nodes
bsdf = nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.35, 0.40, 0.45, 1.0)  # Modro-šedá
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Specular IOR Level"].default_value = 0.3

for obj in [body, dorsal, pec_l, pec_r, tail_v, tail_h, snout]:
    if obj.data.materials:
        obj.data.materials[0] = shark_mat
    else:
        obj.data.materials.append(shark_mat)


# ── 4. PŘIPOJENÍ MESHŮ K ARMATURĚ ───────────────────────────────────────────

def parent_to_armature(mesh_obj, arm_obj):
    """Přidá armature modifier na mesh."""
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True


all_meshes = [body, dorsal, pec_l, pec_r, tail_v, tail_h, snout]
for m in all_meshes:
    parent_to_armature(m, arm_obj)

# Přiřazení vertex groups pro tělo
def assign_weights(obj, group_name, min_y, max_y, falloff=0.3):
    """Jednoduchá váhová mapa podle Y pozice."""
    vg = obj.vertex_groups.new(name=group_name)
    idxs = []
    weights = []
    for v in obj.data.vertices:
        world_y = (obj.matrix_world @ v.co).y
        if min_y - falloff < world_y < max_y + falloff:
            dist_min = abs(world_y - min_y)
            dist_max = abs(world_y - max_y)
            center = (min_y + max_y) / 2
            dist_c = abs(world_y - center) / max(abs(max_y - min_y) / 2, 0.001)
            w = max(0.0, 1.0 - dist_c)
            idxs.append(v.index)
            weights.append(w)
    for i, w in zip(idxs, weights):
        vg.add([i], w, 'REPLACE')

# Body weights (přibližné Y rozsahy po aplikaci scale)
assign_weights(body, "Root",      -2.0, 0.6 * 2.0)
assign_weights(body, "Body_Mid",   0.6 * 2.0 - 0.3, 1.4 * 2.0 + 0.3)
assign_weights(body, "Body_Back",  1.4 * 2.0 - 0.3, 2.2 * 2.0 + 0.3)
assign_weights(body, "Tail_Base",  2.2 * 2.0 - 0.3, 2.9 * 2.0 + 0.3)
assign_weights(body, "Tail_Mid",   2.9 * 2.0 - 0.3, 3.5 * 2.0 + 0.3)
assign_weights(body, "Tail_Tip",   3.5 * 2.0 - 0.3, 5.0)

# Ostatní meshes -> Root bone
for obj in [dorsal, pec_l, pec_r, snout]:
    vg = obj.vertex_groups.new(name="Root")
    verts = [v.index for v in obj.data.vertices]
    vg.add(verts, 1.0, 'REPLACE')

for obj in [tail_v, tail_h]:
    vg = obj.vertex_groups.new(name="Tail_Mid")
    verts = [v.index for v in obj.data.vertices]
    vg.add(verts, 1.0, 'REPLACE')


# ── 5. ANIMACE – vlnivý pohyb ocasu ─────────────────────────────────────────

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 60
bpy.context.scene.render.fps = 24

arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='POSE')

pose = arm_obj.pose

# Keyframe data: (bone_name, frame, rz_degrees)
# Vlnění – fázový posun pro každý kloub
wave_bones = ["Body_Back", "Tail_Base", "Tail_Mid", "Tail_Tip"]
amplitudes  = [5,           12,          18,          22]
phase_shift = [0,           8,           16,          24]  # frame offset

frames = [1, 15, 30, 45, 60]
angles = [0, 1, 0, -1, 0]  # normalizovaný sinus

for bone_name, amp, phase in zip(wave_bones, amplitudes, phase_shift):
    pb = pose.bones[bone_name]
    pb.rotation_mode = 'XYZ'
    for i, fr in enumerate(frames):
        # Posun fáze
        t = ((fr - 1 + phase) % 60) / 59
        angle_norm = math.sin(t * 2 * math.pi)
        rz = amp * angle_norm
        pb.rotation_euler = (0, 0, math.radians(rz))
        pb.keyframe_insert(data_path="rotation_euler", frame=fr)

# Nastavení smyčkování
for action in bpy.data.actions:
    for fcurve in action.fcurves:
        for mod in fcurve.modifiers:
            fcurve.modifiers.remove(mod)
        fcurve.modifiers.new('CYCLES')

bpy.ops.object.mode_set(mode='OBJECT')

# ── 6. KAMERA A SVĚTLO ───────────────────────────────────────────────────────

# Kamera
bpy.ops.object.camera_add(location=(3.5, -3.0, 1.5))
cam = bpy.context.object
cam.rotation_euler = (math.radians(75), 0, math.radians(45))
bpy.context.scene.camera = cam

# Světlo
bpy.ops.object.light_add(type='SUN', location=(2, -4, 5))
sun = bpy.context.object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(45), 0, math.radians(30))

# Přesunutí do pohledu
bpy.ops.view3d.view_all(center=True) if hasattr(bpy.ops.view3d, 'view_all') else None

print("=" * 55)
print("  ✅ ŽRALOK VYTVOŘEN!")
print("=" * 55)
print("  🦷 Mesh: Shark_Body + ploutve + čumák + oči")
print("  🦴 Armatura: 6 kostí (Root → Tail_Tip)")
print("  🎬 Animace: Frame 1-60, vlnivý pohyb ocasu")
print()
print("  Tipy:")
print("  • Stiskni MEZERNÍK pro spuštění animace")
print("  • Vyber armature → Tab → Pose Mode")
print("    pro ruční úpravy kloubů")
print("  • N panel → View → 'View All' pro zoom")
print("=" * 55)
