"""
=========================================================
Base extractor:
Executes MT pole detection from a PLY file.
Now input file is read from config.json instead of CLI.
=========================================================
"""

import os
import json
import numpy as np
from plyfile import PlyData

from extractor.interface import detect_poles

# =========================================================
# CONFIG
# =========================================================
CONFIG_FILE = "config.json"

def load_config(path=CONFIG_FILE):
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Config file not found: {path}")
    with open(path, "r") as f:
        config = json.load(f)
    # Validate required keys
    required_keys = ["models_dir", "output_dir", "label_MT", "input_ply"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"❌ Config missing required key: {key}")
    return config


# =========================================================
# SAVE CLUSTERS
# =========================================================
def save_clusters(clusters, output_dir):
    import open3d as o3d
    os.makedirs(output_dir, exist_ok=True)
    for i, cluster_pts in enumerate(clusters):
        if len(cluster_pts) == 0:
            continue
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(cluster_pts)
        ply_path = os.path.join(output_dir, f"pole_{i+1:02d}.ply")
        o3d.io.write_point_cloud(ply_path, pcd)


# =========================================================
# MAIN EXECUTION
# =========================================================
def main():
    config = load_config()
    input_ply = config["input_ply"]

    # Read PLY file
    plydata = PlyData.read(input_ply)
    vertex = plydata["vertex"].data
    field_names = vertex.dtype.names

    # Detect label field
    label_field = None
    for candidate in ["scalar_Label", "label", "Label", "classification", "class"]:
        if candidate in field_names:
            label_field = candidate
            break
    if label_field is None:
        raise ValueError("❌ No label field found in PLY.")

    points = np.vstack([vertex["x"], vertex["y"], vertex["z"]]).T
    labels = np.array(vertex[label_field])

    # ============================
    # Call the interface
    # ============================
    clusters = detect_poles(
        points,
        labels,
        method="dbscan",
        target_label=config["label_MT"]
    )

    save_clusters(clusters, config["models_dir"])
    print(f"✅ Total clusters detected: {len(clusters)}")
    print(f"📂 Saved in: {config['models_dir']}")


# =========================================================
# EXECUTE
# =========================================================
if __name__ == "__main__":
    main()