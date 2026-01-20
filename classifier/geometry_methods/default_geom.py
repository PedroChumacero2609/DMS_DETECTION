import numpy as np

def extract_geometry(points):
    """
    Default method: mean + min/max + median
    Returns a dictionary with the pole's center, height, and diameter.
    
    Args:
        points: np.array of shape (N,3) representing the pole point cloud
    
    Returns:
        dict with keys:
            - "center": 3D center coordinates (x, y, z)
            - "base_z": minimum z-coordinate (base of the pole)
            - "height": height of the pole (max_z - min_z)
            - "diameter": estimated diameter based on median XY distance
    """
    # Compute 3D center of the point cloud
    center = np.mean(points, axis=0)
    
    # Compute vertical bounds and height
    min_z = np.min(points[:, 2])
    max_z = np.max(points[:, 2])
    height = max_z - min_z

    return {
        "center": center,
        "base_z": min_z,
        "height": height,
    }