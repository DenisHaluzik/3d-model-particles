"""
╔══════════════════════════════════════════════════════╗
║          DETAILNÍ ŽRALOK PRO BLENDER                 ║
║  Realistická anatomie · 6 kloubů · Wave animace      ║
╠══════════════════════════════════════════════════════╣
║  SPUŠTĚNÍ:                                            ║
║  1. Blender → záložka "Scripting"                    ║
║  2. New → vlož celý kód → Run Script (Alt+P)         ║
╚══════════════════════════════════════════════════════╝

Anatomie žraloka:
  ┌─ Tělo: cross-section rings (22 segmentů) ─────────┐
  │  Torpédovitý tvar, splasklé břicho, hřbetní hřbet  │
  └────────────────────────────────────────────────────┘
  Ploutve:  hřbetní, 2× hřbetní malá, ocasní (heteroc.)
            2× prsní, 2× břišní, řitní
  Oči:      2× přesně v hlavě
  Žaberní štěrbiny: 5 na každé straně
  
  Armatura – 6 kloubů:
    Head → Body_Front → Body_Back → Tail_Root → Tail_Mid → Tail_Tip
  
  Animace: vlnivý pohyb ocasu, frame 1–60, smyčka
"""

import bpy
import bmesh
import math
from mathutils import Vector

# ═══════════════════════════════════════════════════════════════════
#  ČISTÁ SCÉNA
# ═══════════════════════════════════════════════════════════════════
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for d in [bpy.data.meshes, bpy.data.armatures,
          bpy.data.materials, bpy.data.actions]:
    for item in list(d):
        d.remove(item)

# ═══════════════════════════════════════════════════════════════════
#  MATERIÁLY
# ═══════════════════════════════════════════════════════════════════
def make_mat(name, color, roughness=0.55, metallic=0.0, specular=0.2):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    b = n.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Specular IOR Level"].default_value = specular
    return mat

mat_top    = make_mat("Shark_Top",    (0.25, 0.30, 0.37), 0.60)  # Modro-šedá záda
mat_belly  = make_mat("Shark_Belly",  (0.82, 0.82, 0.78), 0.65)  # Bílé břicho
mat_fin    = make_mat("Shark_Fin",    (0.27, 0.32, 0.39), 0.62)  # Tmavší ploutve
mat_eye    = make_mat("Shark_Eye",    (0.01, 0.01, 0.01), 0.05, 0.0, 0.8)  # Lesklé oko
mat_pupil  = make_mat("Shark_Pupil",  (0.00, 0.00, 0.00), 0.02, 0.0, 1.0)
mat_gill   = make_mat("Shark_Gill",   (0.18, 0.20, 0.24), 0.80)

# ═══════════════════════════════════════════════════════════════════
#  TĚLO – cross-section rings
# ═══════════════════════════════════════════════════════════════════
# Profil: (Y pozice, rx=šířka, rz=výška, z_center=výška osy těla)
# Žralok leží podél osy Y, čumák u Y=0, ocas u Y=4
# Celková délka: ~4 jednotky Blenderu

SEGS = 22   # vrcholů v každém kruhu (musí být sudé)

PROFILE = [
    # y      rx      rz      z_ctr      # co to je
    (0.000, 0.001, 0.001,  0.000),  # apex čumáku
    (0.070, 0.032, 0.026,  0.000),  # špička čumáku
    (0.180, 0.085, 0.068,  0.000),  # čumák
    (0.340, 0.162, 0.132,  0.006),  # přechod čumák→hlava
    (0.530, 0.242, 0.195,  0.016),  # oblast očí
    (0.760, 0.310, 0.245,  0.013),  # za očima
    (1.000, 0.362, 0.272,  0.007),  # přední žaberní oblast
    (1.240, 0.395, 0.285,  0.000),  # žaberní štěrbiny
    (1.450, 0.408, 0.292, -0.005),  # základna prsní ploutve (NEJŠIRŠÍ)
    (1.660, 0.392, 0.276, -0.012),  # za prsní ploutví
    (1.900, 0.340, 0.248, -0.022),  # střed těla
    (2.140, 0.272, 0.204, -0.032),  # střed těla zadní
    (2.380, 0.198, 0.158, -0.041),  # přechod na stonek
    (2.620, 0.135, 0.110, -0.050),  # začátek caudálního stonku
    (2.860, 0.085, 0.082, -0.057),  # caudální stonek
    (3.100, 0.052, 0.060, -0.062),  # úzký stonek
    (3.340, 0.030, 0.040, -0.067),  # před ocasem
    (3.580, 0.016, 0.022, -0.072),  # spojení s ocasní ploutví
]

def get_profile_at(y):
    """Interpolace profilu těla pro danou Y pozici."""
    for i in range(len(PROFILE) - 1):
        y0, rx0, rz0, zc0 = PROFILE[i]
        y1, rx1, rz1, zc1 = PROFILE[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return (rx0 + t*(rx1-rx0), rz0 + t*(rz1-rz0), zc0 + t*(zc1-zc0))
    return PROFILE[-1][1], PROFILE[-1][2], PROFILE[-1][3]

bm = bmesh.new()
rings = []   # (ring_verts, y_position)

for y, rx, rz, zc in PROFILE:
    ring = []
    for i in range(SEGS):
        a = 2 * math.pi * i / SEGS
        cx = math.cos(a)
        cz = math.sin(a)
        
        # Tvarování průřezu – realističtější tvar žraloka
        if cz < 0:
            # Břicho – splasklé (D-tvar)
            cz = -(abs(cz) ** 0.82)
        else:
            # Záda – mírně zakulacená
            cz = cz ** 0.90
        
        # Boky – mírně zploštělé
        cx = math.copysign(abs(cx) ** 0.96, cx)
        
        v = bm.verts.new((rx * cx, y, rz * cz + zc))
        ring.append(v)
    rings.append((ring, y))

# Propojení kruhů do ploch
for ri in range(len(rings) - 1):
    r1, _ = rings[ri]
    r2, _ = rings[ri + 1]
    for i in range(SEGS):
        j = (i + 1) % SEGS
        try:
            bm.faces.new([r1[i], r2[i], r2[j], r1[j]])
        except:
            pass

# Uzavření čumáku
apex_v = bm.verts.new((0, 0, 0))
r_front = rings[0][0]
for i in range(SEGS):
    j = (i + 1) % SEGS
    try:
        bm.faces.new([r_front[j], apex_v, r_front[i]])
    except:
        pass

# Uzavření ocasu
r_last = rings[-1][0]
cx = sum(v.co.x for v in r_last) / SEGS
cy = sum(v.co.y for v in r_last) / SEGS
cz_v = sum(v.co.z for v in r_last) / SEGS
tail_cap = bm.verts.new((cx, cy, cz_v))
for i in range(SEGS):
    j = (i + 1) % SEGS
    try:
        bm.faces.new([r_last[i], tail_cap, r_last[j]])
    except:
        pass

# Uložení vertex pozic pro váhy (před uvolněním bmesh)
vert_positions = [(v.co.y, v.co.z) for v in bm.verts]

mesh_body = bpy.data.meshes.new("Shark_Body_Mesh")
bm.to_mesh(mesh_body)
bm.free()

body = bpy.data.objects.new("Shark_Body", mesh_body)
bpy.context.collection.objects.link(body)
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.shade_smooth()
body.select_set(False)

# Subdiv pro hladší povrch
sub_body = body.modifiers.new("Subsurf", 'SUBSURF')
sub_body.levels = 2
sub_body.render_levels = 3

# Materiály těla (hřbet a břicho)
body.data.materials.append(mat_top)
body.data.materials.append(mat_belly)


# ═══════════════════════════════════════════════════════════════════
#  POMOCNÁ FUNKCE – vytvoření ploutve ze 2D obrysu
# ═══════════════════════════════════════════════════════════════════
def make_fin(name, outline_yz, thickness=0.020, mat=None, subdiv=2):
    """
    Vytvoří ploutev z uzavřeného polygonu v rovině YZ.
    outline_yz: seznam bodů [(y,z), ...]
    """
    bm2 = bmesh.new()
    verts = [bm2.verts.new((0.0, y, z)) for y, z in outline_yz]
    try:
        bm2.faces.new(verts)
    except Exception as e:
        print(f"Fin face error {name}: {e}")
    mesh2 = bpy.data.meshes.new(name + "_mesh")
    bm2.to_mesh(mesh2)
    bm2.free()
    
    obj = bpy.data.objects.new(name, mesh2)
    bpy.context.collection.objects.link(obj)
    
    # Solidify – tloušťka ploutve
    sol = obj.modifiers.new("Solidify", 'SOLIDIFY')
    sol.thickness = thickness
    sol.offset = 0.0
    sol.use_even_offset = True
    
    # Subdiv
    if subdiv > 0:
        s = obj.modifiers.new("Subd", 'SUBSURF')
        s.levels = subdiv
    
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()
    obj.select_set(False)
    
    if mat:
        obj.data.materials.append(mat)
    
    return obj


# ═══════════════════════════════════════════════════════════════════
#  HŘBETNÍ PLOUTEV (velká, trojúhelníková, mírně zahnutá dozadu)
# ═══════════════════════════════════════════════════════════════════
# Základna na hřbetu těla (z ≈ +0.287), špička výše
dorsal1_outline = [
    (1.42,  0.283),  # přední základna
    (1.50,  0.360),
    (1.57,  0.450),
    (1.63,  0.548),
    (1.68,  0.635),
    (1.72,  0.706),
    (1.76,  0.754),
    (1.80,  0.776),  # ŠPIČKA
    (1.85,  0.762),
    (1.91,  0.722),
    (1.98,  0.658),
    (2.05,  0.575),
    (2.11,  0.482),
    (2.16,  0.390),
    (2.20,  0.318),
    (2.23,  0.283),  # zadní základna
    # základna se uzavírá po povrchu těla – přidáme střední bod
    (1.82,  0.280),
]
dorsal1 = make_fin("Dorsal_Fin_1", dorsal1_outline, thickness=0.024, mat=mat_fin)


# ═══════════════════════════════════════════════════════════════════
#  DRUHÁ HŘBETNÍ PLOUTEV (malá)
# ═══════════════════════════════════════════════════════════════════
dorsal2_outline = [
    (2.55,  0.108),
    (2.59,  0.148),
    (2.64,  0.192),
    (2.70,  0.228),
    (2.76,  0.245),  # vrchol
    (2.83,  0.232),
    (2.89,  0.200),
    (2.94,  0.158),
    (2.97,  0.112),
    (2.98,  0.108),
]
dorsal2 = make_fin("Dorsal_Fin_2", dorsal2_outline, thickness=0.016, mat=mat_fin, subdiv=1)


# ═══════════════════════════════════════════════════════════════════
#  OCASNÍ PLOUTEV – heterocercální (horní lalok větší)
# ═══════════════════════════════════════════════════════════════════
# Tvar ocasní ploutve v rovině YZ
# Tělo končí u y=3.58, z=-0.072
caudal_outline = [
    (3.55, -0.070),  # bod napojení na tělo (stonek)
    # ─── HORNÍ LALOK (větší) ────────────────────────────
    (3.63,  0.010),
    (3.72,  0.108),
    (3.82,  0.222),
    (3.93,  0.338),
    (4.04,  0.440),
    (4.14,  0.512),
    (4.22,  0.548),
    (4.28,  0.558),  # vrchol horního laloku
    (4.32,  0.540),
    (4.34,  0.505),
    (4.32,  0.450),
    (4.26,  0.375),
    (4.17,  0.290),
    (4.06,  0.205),
    (3.95,  0.122),
    (3.84,  0.042),
    # ─── ZÁŘEZ (notch) ──────────────────────────────────
    (3.76, -0.040),
    (3.80, -0.092),
    # ─── DOLNÍ LALOK (menší) ────────────────────────────
    (3.88, -0.158),
    (3.98, -0.248),
    (4.08, -0.322),
    (4.16, -0.368),
    (4.22, -0.388),  # vrchol dolního laloku
    (4.25, -0.372),
    (4.24, -0.335),
    (4.18, -0.285),
    (4.10, -0.235),
    (4.00, -0.185),
    (3.90, -0.142),
    (3.80, -0.108),
    (3.70, -0.085),
    (3.60, -0.073),
]
caudal = make_fin("Caudal_Fin", caudal_outline, thickness=0.018, mat=mat_fin)


# ═══════════════════════════════════════════════════════════════════
#  PRSNÍ PLOUTVE – velké, lomené dozadu (jako u žraloka bílého)
# ═══════════════════════════════════════════════════════════════════
def make_pectoral(side):
    """Vytvoří prsní ploutev. side = 'L' nebo 'R'."""
    sign = 1 if side == 'L' else -1
    
    # Obrys v rovině XY (lokální souřadnice ploutve)
    # Kladné X = ven od těla
    raw_pts = [
        # (local_x, local_y) – před rotací do 3D
        (0.00,  0.00),   # přední hrana u těla
        (0.18,  0.02),
        (0.42,  0.02),
        (0.68,  0.00),
        (0.90, -0.04),   # vedoucí hrana
        (1.08, -0.10),
        (1.18, -0.18),
        (1.22, -0.28),
        (1.20, -0.40),   # špička ploutve
        (1.12, -0.50),
        (0.98, -0.56),
        (0.80, -0.58),   # zadní konec ploutve
        (0.62, -0.55),
        (0.45, -0.48),
        (0.30, -0.40),
        (0.16, -0.32),
        (0.06, -0.22),
        (0.00, -0.12),
    ]
    
    bm3 = bmesh.new()
    verts3 = []
    for lx, ly in raw_pts:
        # Mapování do 3D:
        # local_x -> X (s přihlédnutím ke straně)
        # local_y -> Y (podél těla, posunutý o y_offset)
        # Z: mírně dolů od základny
        x = sign * lx
        y = 1.22 + ly * 0.0 + lx * (-0.15)   # mírné zpětné šipování
        z = -lx * 0.16 - 0.005               # klesá ven od těla
        # Přepočítáme: základna je u těla, ploutev se rozkládá stranou a dozadu
        verts3.append(bm3.verts.new((x, y + ly, z)))
    
    try:
        bm3.faces.new(verts3)
    except Exception as e:
        print(f"Pectoral face error: {e}")
    
    mesh3 = bpy.data.meshes.new(f"Pectoral_{side}_mesh")
    bm3.to_mesh(mesh3)
    bm3.free()
    
    obj3 = bpy.data.objects.new(f"Pectoral_{side}", mesh3)
    bpy.context.collection.objects.link(obj3)
    
    # Solidify
    sol3 = obj3.modifiers.new("Solidify", 'SOLIDIFY')
    sol3.thickness = 0.020
    sol3.offset = 0
    
    s3 = obj3.modifiers.new("Subd", 'SUBSURF')
    s3.levels = 2
    
    # Posunutí k tělu
    obj3.location = (sign * 0.395, 0.0, 0.0)
    obj3.rotation_euler = (
        math.radians(sign * -5),   # mírný náklon ven
        math.radians(-18),          # náklon dolů
        0
    )
    
    bpy.context.view_layer.objects.active = obj3
    obj3.select_set(True)
    bpy.ops.object.shade_smooth()
    obj3.select_set(False)
    
    obj3.data.materials.append(mat_fin)
    return obj3

pec_l = make_pectoral('L')
pec_r = make_pectoral('R')


# ═══════════════════════════════════════════════════════════════════
#  PÁNEVNÍ PLOUTVE (malé, spodní strana)
# ═══════════════════════════════════════════════════════════════════
def make_pelvic(side):
    sign = 1 if side == 'L' else -1
    raw_pts = [
        (0.00,  0.00),
        (0.10,  0.02),
        (0.25,  0.02),
        (0.40,  0.00),
        (0.48, -0.08),
        (0.50, -0.20),
        (0.46, -0.32),
        (0.36, -0.38),
        (0.22, -0.36),
        (0.10, -0.28),
        (0.02, -0.16),
    ]
    bm4 = bmesh.new()
    verts4 = [bm4.verts.new((sign * x, y, 0)) for x, y in raw_pts]
    try:
        bm4.faces.new(verts4)
    except: pass
    mesh4 = bpy.data.meshes.new(f"Pelvic_{side}_mesh")
    bm4.to_mesh(mesh4); bm4.free()
    obj4 = bpy.data.objects.new(f"Pelvic_{side}", mesh4)
    bpy.context.collection.objects.link(obj4)
    sol4 = obj4.modifiers.new("Solidify", 'SOLIDIFY')
    sol4.thickness = 0.014; sol4.offset = 0
    obj4.modifiers.new("Subd", 'SUBSURF').levels = 1
    obj4.location = (sign * 0.16, 2.02, -0.200)
    obj4.rotation_euler = (0, math.radians(-10), math.radians(sign * -18))
    bpy.context.view_layer.objects.active = obj4
    obj4.select_set(True); bpy.ops.object.shade_smooth(); obj4.select_set(False)
    obj4.data.materials.append(mat_fin)
    return obj4

pelv_l = make_pelvic('L')
pelv_r = make_pelvic('R')


# ═══════════════════════════════════════════════════════════════════
#  ŘITNÍ PLOUTEV (malá, pod tělem)
# ═══════════════════════════════════════════════════════════════════
anal_outline = [
    (2.70, -0.152),
    (2.74, -0.192),
    (2.80, -0.232),
    (2.87, -0.260),
    (2.94, -0.272),  # vrchol
    (3.01, -0.258),
    (3.07, -0.228),
    (3.11, -0.192),
    (3.13, -0.158),
    (3.12, -0.152),
]
anal_fin = make_fin("Anal_Fin", anal_outline, thickness=0.014, mat=mat_fin, subdiv=1)


# ═══════════════════════════════════════════════════════════════════
#  OČI – detailní (bělmo + zornice)
# ═══════════════════════════════════════════════════════════════════
for side_name, sx in [('L', -1), ('R', 1)]:
    # Oko (bělmo)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=16,
        radius=0.042, location=(sx * 0.242, 0.52, 0.205)
    )
    eye = bpy.context.object
    eye.name = f"Eye_{side_name}"
    eye.data.materials.append(mat_eye)
    bpy.ops.object.shade_smooth()
    
    # Zornice (malá, přilepená na oku)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=12,
        radius=0.028, location=(sx * 0.278, 0.52, 0.205)
    )
    pupil = bpy.context.object
    pupil.name = f"Pupil_{side_name}"
    pupil.data.materials.append(mat_pupil)
    bpy.ops.object.shade_smooth()


# ═══════════════════════════════════════════════════════════════════
#  ŽABERNÍ ŠTĚRBINY (5 na každé straně)
# ═══════════════════════════════════════════════════════════════════
for side, sx in [('L', -1), ('R', 1)]:
    for gi in range(5):
        y_pos = 0.95 + gi * 0.072
        # Přibližná pozice na povrchu těla
        rx, rz, zc = get_profile_at(y_pos)
        
        bpy.ops.mesh.primitive_plane_add(size=1.0)
        gill = bpy.context.object
        gill.name = f"Gill_{side}_{gi}"
        gill.location = (sx * rx * 0.92, y_pos, -0.012 + zc)
        gill.rotation_euler = (
            math.radians(8),
            math.radians(0),
            math.radians(sx * 80)
        )
        gill.scale = (0.016, 0.076, 0.001)
        gill.data.materials.append(mat_gill)


# ═══════════════════════════════════════════════════════════════════
#  ARMATURA – 6 KLOUBŮ
# ═══════════════════════════════════════════════════════════════════
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
arm_obj = bpy.context.object
arm_obj.name   = "Shark_Rig"
arm            = arm_obj.data
arm.name       = "Shark_Bones"

for b in arm.edit_bones:
    arm.edit_bones.remove(b)

# Definice kloubů podél páteře
BONES = [
    # (název,         hlava(x,y,z),         ocas(x,y,z),          rodič)
    ("Head",       (0, 0.30,  0.010),  (0, 0.95,  0.005),  None),
    ("Body_Front", (0, 0.95,  0.005),  (0, 1.72, -0.003),  "Head"),
    ("Body_Back",  (0, 1.72, -0.003),  (0, 2.55, -0.028),  "Body_Front"),
    ("Tail_Root",  (0, 2.55, -0.028),  (0, 3.12, -0.055),  "Body_Back"),
    ("Tail_Mid",   (0, 3.12, -0.055),  (0, 3.58, -0.068),  "Tail_Root"),
    ("Tail_Tip",   (0, 3.58, -0.068),  (0, 4.05, -0.072),  "Tail_Mid"),
]

created = {}
for bname, bhead, btail, bpar in BONES:
    eb = arm.edit_bones.new(bname)
    eb.head = Vector(bhead)
    eb.tail = Vector(btail)
    if bpar:
        eb.parent = created[bpar]
        eb.use_connect = True
    created[bname] = eb

bpy.ops.object.mode_set(mode='OBJECT')
arm_obj.show_in_front = True
arm_obj.display_type  = 'STICK'


# ═══════════════════════════════════════════════════════════════════
#  PARENTING – připojení meshů k armaturě
# ═══════════════════════════════════════════════════════════════════
all_parts = [body, dorsal1, dorsal2, caudal,
             pec_l, pec_r, pelv_l, pelv_r, anal_fin]

for obj in all_parts:
    obj.parent = arm_obj
    mod_arm = obj.modifiers.new("Armature", 'ARMATURE')
    mod_arm.object = arm_obj
    # Přesun Armature modifikátoru nahoru (před Subsurf/Solidify)
    while obj.modifiers[0].name != "Armature":
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_move_up(modifier="Armature")


# ═══════════════════════════════════════════════════════════════════
#  VERTEX WEIGHTS – automatické váhy dle Y pozice
# ═══════════════════════════════════════════════════════════════════
def smooth_weight(y, y_min, y_max):
    """Smooth-step váha 0→1→0 pro daný Y rozsah."""
    if y <= y_min or y >= y_max:
        return 0.0
    t = (y - y_min) / (y_max - y_min)
    return math.sin(t * math.pi)  # hladká zvonovitá křivka

# Rozsahy pro každou kost (překrývají se pro hladký přechod)
BONE_RANGES = {
    "Head":       (0.00, 1.10),
    "Body_Front": (0.80, 1.92),
    "Body_Back":  (1.70, 2.75),
    "Tail_Root":  (2.50, 3.25),
    "Tail_Mid":   (3.05, 3.68),
    "Tail_Tip":   (3.48, 4.20),
}

# Váhy pro tělo
for bname, (y0, y1) in BONE_RANGES.items():
    vg = body.vertex_groups.new(name=bname)
    indices_weights = []
    for v in body.data.vertices:
        w = smooth_weight(v.co.y, y0, y1)
        if w > 0.001:
            indices_weights.append((v.index, w))
    for idx, w in indices_weights:
        vg.add([idx], w, 'REPLACE')

# Jednoduché váhy pro ploutve (vždy ke konkrétní kosti)
FIN_BONE = {
    dorsal1:   "Body_Front",
    dorsal2:   "Body_Back",
    caudal:    "Tail_Tip",
    pec_l:     "Body_Front",
    pec_r:     "Body_Front",
    pelv_l:    "Body_Back",
    pelv_r:    "Body_Back",
    anal_fin:  "Tail_Root",
}

for obj, bname in FIN_BONE.items():
    # Primární kost
    vg = obj.vertex_groups.new(name=bname)
    vg.add([v.index for v in obj.data.vertices], 1.0, 'REPLACE')

# Ocasní ploutev dostane váhy rozdělené mezi 2 kosti
caudal_bones = [("Tail_Mid", 0.45), ("Tail_Tip", 0.55)]
for bname, w in caudal_bones:
    vg = caudal.vertex_groups.get(bname)
    if not vg:
        vg = caudal.vertex_groups.new(name=bname)
    for v in caudal.data.vertices:
        vg.add([v.index], w, 'REPLACE')


# ═══════════════════════════════════════════════════════════════════
#  ANIMACE – vlnivý pohyb ocasu (realistický)
# ═══════════════════════════════════════════════════════════════════
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end   = 60
bpy.context.scene.render.fps  = 24

bpy.context.view_layer.objects.active = arm_obj
arm_obj.select_set(True)
bpy.ops.object.mode_set(mode='POSE')

pose = arm_obj.pose

# Parametry vlnění: (kost, amplituda_stupně, fázový_posun_framy)
# Větší amplituda a zpoždění směrem k ocasu = realistická vlna
WAVE_BONES = [
    ("Body_Back",  4,   0),   # tělo se mírně hýbe
    ("Tail_Root",  9,   6),   # kořen ocasu
    ("Tail_Mid",   16,  12),  # střed ocasu
    ("Tail_Tip",   24,  18),  # špička – největší výchylka
]

TOTAL_F = 60   # délka smyčky v framech

for bname, amp, phase in WAVE_BONES:
    pb = pose.bones[bname]
    pb.rotation_mode = 'XYZ'
    
    # Keyframy pro jeden plný cyklus + 1 navíc pro smyčku
    for frame in range(1, TOTAL_F + 2):
        t = ((frame - 1 + phase) % TOTAL_F) / TOTAL_F
        angle_deg = amp * math.sin(2 * math.pi * t)
        pb.rotation_euler = (0, 0, math.radians(angle_deg))
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)

# Přidání CYCLES modifikátoru pro nekonečnou smyčku
for action in bpy.data.actions:
    for fc in action.fcurves:
        fc.modifiers.new('CYCLES')

bpy.ops.object.mode_set(mode='OBJECT')


# ═══════════════════════════════════════════════════════════════════
#  KAMERA A SVĚTLO
# ═══════════════════════════════════════════════════════════════════
# Kamera z boku – vidíme celého žraloka
bpy.ops.object.camera_add(location=(5.8, 2.0, 0.8))
cam = bpy.context.object
cam.name = "Camera"
cam.rotation_euler = (math.radians(82), 0, math.radians(70))
cam.data.lens = 50
bpy.context.scene.camera = cam

# Hlavní světlo (klíčové)
bpy.ops.object.light_add(type='SUN', location=(3, -4, 6))
sun = bpy.context.object
sun.name = "Sun_Key"
sun.data.energy = 4.0
sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(25))

# Doplňkové světlo (fill – zlehka)
bpy.ops.object.light_add(type='AREA', location=(-3, 4, 2))
fill = bpy.context.object
fill.name = "Light_Fill"
fill.data.energy = 200
fill.data.size = 5.0
fill.rotation_euler = (math.radians(100), 0, math.radians(-45))


# ═══════════════════════════════════════════════════════════════════
#  NASTAVENÍ ZOBRAZENÍ
# ═══════════════════════════════════════════════════════════════════
# Zoom na žraloka ve viewport
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'  # Material Preview
                break

# Nastavení framu na 1
bpy.context.scene.frame_set(1)

print()
print("╔══════════════════════════════════════════════════╗")
print("║  ✅  ŽRALOK HOTOV!                               ║")
print("╠══════════════════════════════════════════════════╣")
print("║  Tělo:    22-segment torpédo, hladký povrch      ║")
print("║  Ploutve: hřbetní (2×), prsní (2×), pánevní     ║")
print("║           (2×), řitní, ocasní (heterocerkální)   ║")
print("║  Oči:     2× bělmo + zornice                     ║")
print("║  Žábra:   5 štěrbin na každé straně              ║")
print("║  Klouby:  6 (Head→Body_Front→Body_Back→          ║")
print("║              Tail_Root→Tail_Mid→Tail_Tip)        ║")
print("║  Animace: vlna ocasu, frame 1-60, smyčka        ║")
print("╠══════════════════════════════════════════════════╣")
print("║  ▶ MEZERNÍK = přehrát animaci                    ║")
print("║  N → 'View All' = zoom na celého žraloka         ║")
print("║  Vyber Shark_Rig → Tab → Pose Mode               ║")
print("║     = ruční úprava kloubů                        ║")
print("╚══════════════════════════════════════════════════╝")
