import open3d as o3d
import numpy as np
import pandas as pd
import json
import os
from plyfile import PlyData

# =========================
# ⚙️ LOAD CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

PLY_PATH = os.path.join(BASE_DIR, config["input_ply"])
CSV_PATH = os.path.join(BASE_DIR, config["csv_poles_MT"])
OUTPUT_IMAGE = os.path.join(BASE_DIR, config["visualization"]["reconstruction"])

# =========================
# 🎨 COLOR MAP
# =========================

COLOR_MAP = {
    1: [0.6, 0.6, 0.55],    # Ground, gris verdoso claro
    2: [0.7, 0.65, 0.6],    # Sidewalk, beige suave
    3: [0.5, 0.5, 0.6],     # Road, gris azulado suave
    4: [0.65, 0.65, 0.65],  # Buildings, gris neutro
    5: [0.5, 0.65, 0.5],    # Vegetation, verde apagado
    6: [0.55, 0.27, 0.07],  # LV Poles, marrón (igual que antes)
    8: [0.8, 0.75, 0.4],    # LV Wires, amarillo suave
    10: [0.7, 0.4, 0.4],    # Cars, rojo apagado
    11: [0.5, 0.7, 0.7],    # Signs, azul verdoso suave
    12: [0.6, 0.5, 0.6],    # Monuments, violeta apagado
    13: [0.4, 0.4, 0.7],    # Traffic signs, azul suave
}

# Remove only MT poles from point cloud
REMOVE_CLASSES = [0, config["label_MT"], 9]

# Avarage height
def compute_average_pole_height(csv_path):
    df = pd.read_csv(csv_path)
    heights = df["Height_m"].dropna()
    avg_height = heights.mean()
    print(f"📏 Using average pole height: {avg_height:.2f} m")
    return avg_height

# =========================
# 📏 GEOMETRY PARAMETERS
# =========================
pole_radius = 0.25

num_crossarms = 3
crossarm_length = 2.0
crossarm_radius = 0.06
crossarm_spacing = 1.0
bipole_spacing = 1.5
transformer_height = 2.0

# =========================
# 🔷 POLE CREATION
# =========================
def create_pole_with_crossarms(x, y, z_base, height):
    geometries = []

    pole = o3d.geometry.TriangleMesh.create_cylinder(
        radius=pole_radius, height=height
    )
    pole.compute_vertex_normals()
    pole.paint_uniform_color([0.55, 0.27, 0.07])

    pole.translate([x, y, z_base + height / 2])
    geometries.append(pole)

    z_start = z_base + height - crossarm_radius

    for i in range(num_crossarms):
        crossarm = o3d.geometry.TriangleMesh.create_cylinder(
            radius=crossarm_radius, height=crossarm_length
        )
        crossarm.compute_vertex_normals()
        crossarm.paint_uniform_color([0.55, 0.27, 0.07])

        R = crossarm.get_rotation_matrix_from_xyz((0, np.pi / 2, 0))
        crossarm.rotate(R, center=(0, 0, 0))

        crossarm.translate([
            x + pole_radius + crossarm_length / 2,
            y,
            z_start - i * crossarm_spacing
        ])

        geometries.append(crossarm)

    return geometries


def create_bipole_with_transformer(x, y, z_base, height):
    geometries = []

    geometries += create_pole_with_crossarms(
        x, y - bipole_spacing / 2, z_base, height
    )
    geometries += create_pole_with_crossarms(
        x, y + bipole_spacing / 2, z_base, height
    )

    transformer = o3d.geometry.TriangleMesh.create_box(
        width=2 * pole_radius,
        height=bipole_spacing + 2 * pole_radius,
        depth=transformer_height
    )
    transformer.compute_vertex_normals()
    transformer.paint_uniform_color([0.4, 0.4, 0.4])

    transformer.translate([
        x - pole_radius,
        y - (bipole_spacing / 2 + pole_radius),
        z_base + height / 2
    ])

    geometries.append(transformer)
    return geometries

# =========================
# 📥 LOAD POINT CLOUD
# =========================
def load_and_color_pointcloud():
    plydata = PlyData.read(PLY_PATH)
    v = plydata["vertex"].data

    points = np.vstack([v["x"], v["y"], v["z"]]).T
    labels = v["class"]

    mask = ~np.isin(labels, REMOVE_CLASSES)
    points = points[mask]
    labels = labels[mask]

    colors = np.zeros((len(labels), 3))
    for cls, rgb in COLOR_MAP.items():
        colors[labels == cls] = rgb

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)

    return pcd

def run_rebuild():
    pcd = load_and_color_pointcloud()
    uniform_height = compute_average_pole_height(CSV_PATH)
    poles = reconstruct_poles(uniform_height)

    vis = o3d.visualization.Visualizer()
    vis.create_window(
        "MT Pole Reconstruction",
        1200,
        800
    )

    vis.add_geometry(pcd)
    for g in poles:
        vis.add_geometry(g)

    vis.poll_events()
    vis.update_renderer()

    # Guardar imagen automáticamente y cerrar
    save_current_view(vis)
    vis.destroy_window()
    print("✅ Rebuild completed (image saved automatically)")

# =========================
# 🏗️ RECONSTRUCT POLES
# =========================
def reconstruct_poles(uniform_height):
    df = pd.read_csv(CSV_PATH)
    geometries = []

    for _, row in df.iterrows():
        x = row["Center_X"]
        y = row["Center_Y"]
        z = row["Base_Z"]
        t = row["Type"].lower()

        if t == "monoposte":
            geometries += create_pole_with_crossarms(
                x, y, z, uniform_height
            )
        elif t == "biposte":
            geometries += create_bipole_with_transformer(
                x, y, z, uniform_height
            )

    print(f"✅ Reconstructed {len(df)} poles with uniform height")
    return geometries

# =========================
# 📸 SAVE VIEW
# =========================
def save_current_view(vis):
    vis.capture_screen_image(OUTPUT_IMAGE)
    print(f"📸 View saved: {OUTPUT_IMAGE}")
    return False


# =========================
# 🚀 MAIN
# =========================
if __name__ == "__main__":
    pcd = load_and_color_pointcloud()
    uniform_height = compute_average_pole_height(CSV_PATH)
    poles = reconstruct_poles(uniform_height)

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window(
        "MT Pole Reconstruction  |  Press 'S' to save view",
        1200,
        800
    )

    vis.add_geometry(pcd)
    for g in poles:
        vis.add_geometry(g)

    vis.register_key_callback(ord("S"), save_current_view)

    vis.run()
    vis.destroy_window()