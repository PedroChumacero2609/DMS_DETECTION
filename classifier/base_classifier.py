import os
import json
import argparse
import numpy as np
import pandas as pd
import open3d as o3d
from classifier.interface import ClassifierInterface

# =========================================================
# Configuration file
# =========================================================
CONFIG_FILE = "config.json"

def load_config(path=CONFIG_FILE):
    """
    Load configuration from a JSON file.
    
    Raises:
        FileNotFoundError: if the config file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Config file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)

# =========================================================
# Main execution
# =========================================================
def main():
    # Command line argument parser
    parser = argparse.ArgumentParser(description="Classify MT poles from detected .ply files")
    args = parser.parse_args()  # Currently, no extra arguments are used

    # Load configuration
    config = load_config()

    # Initialize the classification interface
    interface = ClassifierInterface(config)

    # Run the classification on the detected poles
    interface.run_classification()

# Entry point of the script
if __name__ == "__main__":
    main()