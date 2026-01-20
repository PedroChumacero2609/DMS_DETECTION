import os
import importlib
import numpy as np
import open3d as o3d
import torch
import json
import pandas as pd

class ClassifierInterface:
    def __init__(self, config):
        """
        Interface to classify MT poles using a trained model.
        """
        self.config = config

        # Folder containing detected poles (PLY files)
        self.input_dir = config["models_dir"]
        # Path for the output CSV file
        self.output_csv = os.path.join(config["output_dir"], "poles_MT_info_classified.csv")
        # Path to the trained model
        self.model_path = config["model_trained_path"]

        # Import default geometric feature extraction method
        geom_module = importlib.import_module("classifier.geometry_methods.default_geom")
        self.extract_geometry = geom_module.extract_geometry

        # Load trained model onto GPU if available, otherwise CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.load_model()

    def load_model(self):
        """
        Load the pre-trained PointNet model for classification.
        """
        from pointnet.model import PointNetCls
        model = PointNetCls(k=2)  # k=2 classes: Monoposte / Biposte
        model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        model.to(self.device)
        model.eval()  # Set model to evaluation mode
        return model

    def classify_pole(self, points):
        """
        Classify a single pole point cloud.
        Args:
            points: np.array of shape (N,3)
        Returns:
            0 = Monoposte, 1 = Biposte
        """
        with torch.no_grad():
            pts = torch.from_numpy(points).float().unsqueeze(0).transpose(2, 1)
            output = self.model(pts)
            # If model returns a tuple (common in PointNet), take first element
            if isinstance(output, tuple):
                output = output[0]
            pred_choice = output.data.max(1)[1]
            return pred_choice.item()

    def run_classification(self):
        """
        Run classification on all PLY files in the input folder
        and export results as a CSV.
        """
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"❌ Folder not found: {self.input_dir}")

        # List all .ply files in the folder
        ply_files = [f for f in os.listdir(self.input_dir) if f.endswith(".ply")]
        if not ply_files:
            print("⚠️ No .ply files found for classification.")
            return

        poles_info = []

        # Process each pole file
        for idx, fname in enumerate(sorted(ply_files)):
            path = os.path.join(self.input_dir, fname)
            pcd = o3d.io.read_point_cloud(path)
            points = np.asarray(pcd.points)
            if len(points) == 0:
                continue  # Skip empty point clouds

            # Extract geometric features from the pole
            geom = self.extract_geometry(points)

            # Classify pole type
            pole_type = self.classify_pole(points)
            type_str = "Monoposte" if pole_type == 0 else "Biposte"

            # Store information for CSV
            poles_info.append({
                "Pole_ID": idx + 1,
                "Center_X": geom["center"][0],
                "Center_Y": geom["center"][1],
                "Base_Z": geom["base_z"],
                "Height_m": geom["height"],
                "Type": type_str
            })

        # Create output folder if it does not exist
        os.makedirs(os.path.dirname(self.output_csv), exist_ok=True)
        # Save classification results as CSV
        pd.DataFrame(poles_info).to_csv(self.output_csv, index=False)
        print(f"✅ Classification complete.")
        print(f"📂 CSV saved at: {self.output_csv}")