"""
Default DBSCAN method for MT pole clustering
Completely internal: black box.
"""

import numpy as np
import open3d as o3d

# Default DBSCAN parameters
EPS_CLUSTER = 2.0
MIN_POINTS_CLUSTER = 20

def detect_with_dbscan(points, labels, target_label=7):
    """
    Detects pole clusters using DBSCAN.
    """
    # Filter points with the desired label
    mask = labels == target_label
    poles_points = points[mask]

    if len(poles_points) == 0:
        return []

    # Create point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(poles_points)

    # Apply DBSCAN
    cluster_labels = np.array(
        pcd.cluster_dbscan(eps=EPS_CLUSTER, min_points=MIN_POINTS_CLUSTER, print_progress=False)
    )

    clusters = []
    num_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    for cid in range(num_clusters):
        mask_cluster = cluster_labels == cid
        clusters.append(poles_points[mask_cluster])

    return clusters