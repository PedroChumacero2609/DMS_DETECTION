"""
Unified interface for detecting MT poles
Connects input/output with internal clustering methods.
"""

from .clustering.dbscan import detect_with_dbscan

def detect_poles(points, labels, method="dbscan", target_label=7, **kwargs):
    """
    Args:
        points: np.array (Nx3)
        labels: np.array (N)
        method: str, "dbscan" or another
        target_label: MT pole label
        kwargs: additional parameters for each method
    Returns:
        list of clusters (each one an np.array Nx3)
    """
    if method == "dbscan":
        return detect_with_dbscan(points, labels, target_label=target_label, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")