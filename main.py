import os
import json
import argparse
import sys
import runpy

# =====================================================
# Argument parser for the full pipeline
# =====================================================
parser = argparse.ArgumentParser(description="Run full dms-Detection pipeline")
parser.add_argument("--mode", choices=["automatic", "manual"], default="automatic",
                    help="Fusion mode: automatic or manual")
parser.add_argument("--radius", type=float, help="Tube radius in meters")
parser.add_argument("-i", "--input", type=str, help="Input PLY file (labeled)")
parser.add_argument("-o", "--output", type=str, help="Output folder")
args = parser.parse_args()

# =====================================================
# Load config and update according to user inputs
# =====================================================
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

if args.input:
    config["input_ply"] = args.input
if args.output:
    config["output_dir"] = args.output
    config["models_dir"] = os.path.join(config["output_dir"], "poles_MT")
    config["collisions_dir"] = os.path.join(config["output_dir"], "collisions")
if args.radius:
    config["tube"]["default_radius"] = args.radius

# Create folders if they don't exist
os.makedirs(config["output_dir"], exist_ok=True)
os.makedirs(config["models_dir"], exist_ok=True)
os.makedirs(config["collisions_dir"], exist_ok=True)

# Save updated config
with open(CONFIG_FILE, "w") as f:
    json.dump(config, f, indent=4)
print("✅ Config updated for this run.\n")

# =====================================================
# 1️⃣ Base Extractor
# =====================================================
print("="*50)
print("1️⃣ Running Base Extractor")
print("="*50)
from extractor.base_extractor import main as extractor_main
sys.argv = ["base_extractor.py"]  # Clear argv to avoid conflicts
extractor_main()
print("\n")

# =====================================================
# 2️⃣ Classifier
# =====================================================
print("="*50)
print("2️⃣ Running Classifier")
print("="*50)
from classifier.base_classifier import main as classifier_main
sys.argv = ["base_classifier.py"]
classifier_main()
print("\n")

# =====================================================
# 3️⃣ Fusion
# =====================================================
print("="*50)
print(f"3️⃣ Running Fusion ({args.mode})")
print("="*50)
sys.argv = ["base_fusion.py", "--mode", args.mode]
from fusion.base_fusion import main as fusion_main
fusion_main()
print("\n")

# =====================================================
# 4️⃣ Rebuild Poles MT
# =====================================================
print("="*50)
print("4️⃣ Running Rebuild Poles MT")
print("="*50)
from rebuild.rebuild_poles_MT import load_and_color_pointcloud, reconstruct_poles, compute_average_pole_height
import open3d as o3d

# Load point cloud and reconstruct poles
pcd = load_and_color_pointcloud()
uniform_height = compute_average_pole_height(config["csv_poles_MT"])
poles = reconstruct_poles(uniform_height)

# Open visualization window and keep it open until user closes it
vis = o3d.visualization.VisualizerWithKeyCallback()
vis.create_window("MT Pole Reconstruction | S=save, Q=close", width=1200, height=800)
vis.add_geometry(pcd)
for g in poles:
    vis.add_geometry(g)

# Function to save image
def save_view(vis):
    output_img = os.path.join(config["output_dir"], "poles_reconstructed.png")
    vis.capture_screen_image(output_img)
    print(f"📸 View saved: {output_img}")
    return False

# Function to close window
def close_vis(vis):
    vis.close()
    return False

# Register key callbacks
vis.register_key_callback(ord("S"), save_view)
vis.register_key_callback(ord("Q"), close_vis)

vis.run()
vis.destroy_window()
print("✅ Rebuild completed\n")

# =====================================================
# 5️⃣ Tube + Split
# =====================================================
print("="*50)
print("5️⃣ Running Tube + Split")
print("="*50)

# Run tube.py using runpy so __main__ block works
sys.argv = ["tube.py"]
runpy.run_path("dms/tube.py", run_name="__main__")

# Run split.py using runpy
sys.argv = ["split.py"]
runpy.run_path("dms/split.py", run_name="__main__")

print("\n🎉 DMS-Detection pipeline completed successfully!")