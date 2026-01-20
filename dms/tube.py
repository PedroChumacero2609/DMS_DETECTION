import open3d as o3d
import numpy as np
import pandas as pd
import json
import os
import argparse
from collections import Counter
from plyfile import PlyData

from rebuild.rebuild_poles_MT import (
    load_and_color_pointcloud,
    reconstruct_poles,
    compute_average_pole_height,
    crossarm_spacing,
    crossarm_radius
)

# =========================
# ⚙️ LOAD CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

PLY_PATH = os.path.join(BASE_DIR, config["input_ply"])
CSV_PATH = os.path.join(BASE_DIR, config["csv_poles_MT"])
CONNECTIONS_PATH = os.path.join(BASE_DIR, "output/connections.json")
COLLISIONS_DIR = os.path.join(BASE_DIR, config["collisions_dir"])
os.makedirs(COLLISIONS_DIR, exist_ok=True)

# =========================
# 🟡 TUBE PARAMETERS
# =========================
tube_cfg = config["tube"]
DEFAULT_RADIUS = tube_cfg["default_radius"]
color_tubo = tube_cfg["color"]
resol_cilindro = tube_cfg["resolution"]
min_points_collision = tube_cfg["min_points_collision"]

# =========================
# CLI ARGUMENTS
# =========================
parser = argparse.ArgumentParser()
parser.add_argument("--radius", type=float)
args = parser.parse_args()
tube_radius = args.radius if args.radius else DEFAULT_RADIUS

# =========================
# CLASS NAMES
# =========================
class_names = {
    1: "Ground",
    2: "Sidewalk",
    3: "Road",
    4: "Building",
    5: "Vegetation",
    8: "LV Wires",
    10: "Car",
    11: "Sign",
    12: "Monument",
    13: "Traffic sign"
}

REMOVE_CLASSES = [0, 6, config["label_MT"], 9]

# =========================
# GEOMETRY UTILS
# =========================
def puntos_en_cilindro(points, p1, p2, radius):
    p1, p2 = np.array(p1), np.array(p2)
    axis = p2 - p1
    L = np.linalg.norm(axis)
    if L < 1e-6:
        return np.array([], dtype=int)
    axis_u = axis / L
    vecs = points - p1
    proj = np.dot(vecs, axis_u)
    mask = (proj >= 0) & (proj <= L)
    closest = p1 + np.outer(proj, axis_u)
    dist = np.linalg.norm(points - closest, axis=1)
    return np.where(mask & (dist <= radius))[0]

def rotar_de_a_b(a, b):
    a, b = np.array(a)/np.linalg.norm(a), np.array(b)/np.linalg.norm(b)
    v = np.cross(a, b)
    if np.linalg.norm(v) < 1e-6:
        return np.eye(3)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    k = np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return np.eye(3) + k + k@k*((1-c)/(s**2))

def crear_cilindro_entre(p1, p2, r):
    p1, p2 = np.array(p1), np.array(p2)
    L = np.linalg.norm(p2 - p1)
    if L < 1e-6:
        return None
    cyl = o3d.geometry.TriangleMesh.create_cylinder(r, L, resol_cilindro)
    cyl.rotate(rotar_de_a_b([0,0,1], p2-p1), center=(0,0,0))
    cyl.translate((p1+p2)/2)
    cyl.paint_uniform_color(color_tubo)
    cyl.compute_vertex_normals()
    return cyl

# =========================
# 📸 SAVE VIEW CALLBACK
# =========================
def save_view(vis):
    out_img = os.path.join(
        COLLISIONS_DIR,
        os.path.basename(config["visualization"]["collisions"])
    )
    vis.capture_screen_image(out_img)
    print(f"📸 View saved: {out_img}")
    return False

# =========================
# 🚀 MAIN
# =========================
if __name__ == "__main__":

    nube = load_and_color_pointcloud()

    ply = PlyData.read(PLY_PATH)["vertex"].data
    pts = np.vstack([ply["x"], ply["y"], ply["z"]]).T
    labels = np.array(ply["class"])
    mask = ~np.isin(labels, REMOVE_CLASSES)
    pts, labels = pts[mask], labels[mask]

    df = pd.read_csv(CSV_PATH)
    with open(CONNECTIONS_PATH) as f:
        conexiones = json.load(f)

    polos = {int(r["Pole_ID"]): r for _, r in df.iterrows()}
    uniform_height = compute_average_pole_height(CSV_PATH)

    geometries = [nube]
    geometries += reconstruct_poles(uniform_height)

    conexiones_dict = {}

    for c in conexiones:
        key = (c["from_id"], c["to_id"])
        conexiones_dict.setdefault(key, [])

        pf, pt = polos[c["from_id"]], polos[c["to_id"]]

        for i in range(3):
            zf = pf["Base_Z"] + uniform_height - crossarm_radius - i*crossarm_spacing
            zt = pt["Base_Z"] + uniform_height - crossarm_radius - i*crossarm_spacing
            p1 = [pf["Center_X"], pf["Center_Y"], zf]
            p2 = [pt["Center_X"], pt["Center_Y"], zt]
            cyl = crear_cilindro_entre(p1, p2, tube_radius)
            if cyl:
                geometries.append(cyl)
                conexiones_dict[key].append((p1, p2, cyl))

    reporte = {"tube_radius": tube_radius, "collisions": []}
    collision_id = 1

    for (from_id, to_id), segmentos in conexiones_dict.items():
        collision_map = {}
        hay_colision = False

        for p1, p2, mesh in segmentos:
            idx = puntos_en_cilindro(pts, p1, p2, tube_radius)
            if len(idx) < min_points_collision:
                continue

            hay_colision = True
            conteo = Counter(labels[idx])

            for cls, n in conteo.items():
                if n < min_points_collision:
                    continue
                collision_map.setdefault(cls, {
                    "object_class_id": int(cls),
                    "object_class_name": class_names.get(cls, f"Unknown_{cls}"),
                    "num_points": 0,
                    "sample_point": pts[idx[0]].tolist()
                })["num_points"] += int(n)

        if hay_colision:
            for _, _, mesh in segmentos:
                mesh.paint_uniform_color([1,0,0])

            reporte["collisions"].append({
                "id": collision_id,
                "from_pole": from_id,
                "to_pole": to_id,
                "collisions": list(collision_map.values())
            })
            collision_id += 1

    with open(os.path.join(COLLISIONS_DIR, "collision_report.json"), "w") as f:
        json.dump(reporte, f, indent=4)

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(
        "COLLISIONS VIEW | Press 'S' to save",
        width=1200,
        height=800
    )

    for g in geometries:
        vis.add_geometry(g)

    vis.register_key_callback(ord("S"), save_view)
    vis.run()
    vis.destroy_window()