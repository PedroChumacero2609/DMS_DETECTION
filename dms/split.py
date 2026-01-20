import open3d as o3d
import numpy as np
import pandas as pd
import json
import os
from plyfile import PlyData, PlyElement

from rebuild.rebuild_poles_MT import (
    reconstruct_poles,
    compute_average_pole_height,
    crossarm_spacing,
    crossarm_radius
)

# =========================
# LOAD CONFIG
# =========================
with open("config.json") as f:
    cfg = json.load(f)

ply_path = cfg["input_ply"]
csv_path = cfg["csv_poles_MT"]
collision_dir = cfg.get("collisions_dir", "output/collisions")
collision_report_path = os.path.join(collision_dir, "collision_report.json")

tube_radius = cfg["tube"].get("default_radius", 4.0)
resol_cilindro = cfg["tube"].get("resolution", 18)

# Envelope
envolvente_radius = 60
envolvente_extension = 5

# Colors
COLOR_TUBE_COLLISION = [1, 0, 0]
COLOR_POLE = [1, 0, 1]

os.makedirs(collision_dir, exist_ok=True)

# =========================
# GEOMETRY UTILS
# =========================
def rotar_de_a_b(a, b):
    a = np.array(a) / np.linalg.norm(a)
    b = np.array(b) / np.linalg.norm(b)
    v = np.cross(a, b)
    c = np.dot(a, b)
    if np.linalg.norm(v) < 1e-6:
        return np.eye(3)
    s = np.linalg.norm(v)
    k = np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])
    return np.eye(3) + k + k @ k * ((1 - c) / (s ** 2))

def crear_cilindro_entre(p1, p2, radio):
    p1, p2 = np.array(p1), np.array(p2)
    vec = p2 - p1
    L = np.linalg.norm(vec)
    if L < 1e-6:
        return None

    cyl = o3d.geometry.TriangleMesh.create_cylinder(
        radius=radio,
        height=L,
        resolution=resol_cilindro
    )
    R = rotar_de_a_b([0, 0, 1], vec)
    cyl.rotate(R, center=(0, 0, 0))
    cyl.translate((p1 + p2) / 2)
    cyl.paint_uniform_color(COLOR_TUBE_COLLISION)
    cyl.compute_vertex_normals()
    return cyl

def puntos_en_cilindro(pts, p1, p2, radius):
    p1, p2 = np.array(p1), np.array(p2)
    v = p2 - p1
    L = np.linalg.norm(v)
    if L < 1e-6:
        return np.array([], dtype=int)

    u = v / L
    rel = pts - p1
    proj = np.dot(rel, u)
    mask_l = (proj >= 0) & (proj <= L)
    closest = p1 + np.outer(proj, u)
    dist = np.linalg.norm(pts - closest, axis=1)

    return np.where(mask_l & (dist <= radius))[0]

def mesh_to_points(mesh, n, class_id, color):
    pcd = mesh.sample_points_uniformly(n)
    pts = np.asarray(pcd.points)
    cols = np.tile(color, (len(pts), 1))
    lbls = np.full(len(pts), class_id, dtype=np.int32)
    return pts, cols, lbls

def guardar_ply(path, pts, cols, lbls):
    n = min(len(pts), len(cols), len(lbls))
    v = np.array([
        (*pts[i], cols[i][0], cols[i][1], cols[i][2], int(lbls[i]))
        for i in range(n)
    ], dtype=[
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
        ('red', 'f4'), ('green', 'f4'), ('blue', 'f4'),
        ('class', 'i4')
    ])
    PlyData([PlyElement.describe(v, 'vertex')]).write(path)

def load_pointcloud_raw(path):
    ply = PlyData.read(path)
    v = ply["vertex"].data
    pts = np.vstack([v["x"], v["y"], v["z"]]).T

    if all(c in v.dtype.names for c in ("red", "green", "blue")):
        cols = np.vstack([v["red"], v["green"], v["blue"]]).T
        if cols.max() > 1.0:
            cols = cols / 255.0
    else:
        cols = np.full((len(pts), 3), 0.6)

    lbls = v["class"] if "class" in v.dtype.names else np.zeros(len(pts), dtype=np.int32)
    return pts, cols, lbls

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    print("\n📥 Extracting collision PLYs (3 tubes per span)...")

    pts, cols, lbls = load_pointcloud_raw(ply_path)
    df = pd.read_csv(csv_path)

    with open(collision_report_path) as f:
        reporte = json.load(f)

    # --- uniform height ---
    uniform_height = compute_average_pole_height(csv_path)

    # --- rebuild poles ---
    pole_geoms = reconstruct_poles(uniform_height)

    pole_meshes = {}
    idx = 0
    for _, r in df.iterrows():
        pid = int(r["Pole_ID"])
        mesh = o3d.geometry.TriangleMesh()
        for _ in range(4):  # poste + 3 crucetas
            mesh += pole_geoms[idx]
            idx += 1
        mesh.compute_vertex_normals()
        pole_meshes[pid] = mesh

    cid = 1
    for col in reporte.get("collisions", []):

        fr, to = col["from_pole"], col["to_pole"]
        pf = df[df["Pole_ID"] == fr].iloc[0]
        pt = df[df["Pole_ID"] == to].iloc[0]

        # --- 3 crossarms ---
        z_offsets = [
            -crossarm_radius,
            -crossarm_radius - crossarm_spacing,
            -crossarm_radius - 2 * crossarm_spacing
        ]

        tubos = []
        for dz in z_offsets:
            p1 = [
                pf["Center_X"], pf["Center_Y"],
                pf["Base_Z"] + uniform_height + dz
            ]
            p2 = [
                pt["Center_X"], pt["Center_Y"],
                pt["Base_Z"] + uniform_height + dz
            ]
            tubos.append(crear_cilindro_entre(p1, p2, tube_radius))

        # --- environment envelope ---
        v = np.array(p2) - np.array(p1)
        u = v / np.linalg.norm(v)
        p1e = np.array(p1) - u * envolvente_extension
        p2e = np.array(p2) + u * envolvente_extension

        idx_env = puntos_en_cilindro(pts, p1e, p2e, envolvente_radius)
        ent_pts, ent_cols, ent_lbls = pts[idx_env], cols[idx_env], lbls[idx_env]

        pA, cA, lA = mesh_to_points(pole_meshes[fr], 8000, 7, COLOR_POLE)
        pB, cB, lB = mesh_to_points(pole_meshes[to], 8000, 7, COLOR_POLE)

        tpts, tcols, tlbls = [], [], []
        for t in tubos:
            p, c, l = mesh_to_points(t, 6000, 14, COLOR_TUBE_COLLISION)
            tpts.append(p)
            tcols.append(c)
            tlbls.append(l)

        Fpts = np.vstack([ent_pts, pA, pB] + tpts)
        Fcols = np.vstack([ent_cols, cA, cB] + tcols)
        Flbls = np.hstack([ent_lbls, lA, lB] + tlbls)

        out = os.path.join(collision_dir, f"collision_extract_{cid}.ply")
        guardar_ply(out, Fpts, Fcols, Flbls)
        print(f"[OK] {out}")
        cid += 1

    print("\n✅ Collision extraction completed.")