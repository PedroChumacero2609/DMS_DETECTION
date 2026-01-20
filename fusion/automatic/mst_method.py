import numpy as np
import networkx as nx
from scipy.spatial import distance_matrix
from fusion.utils.visualization import plot_connections


def run_mst_method(df, k_neighbors=2):
    coords = df[["Center_X", "Center_Y"]].values
    dist_matrix = distance_matrix(coords, coords)

    edges = []
    for i in range(len(df)):
        nearest = np.argsort(dist_matrix[i])[1:k_neighbors + 1]
        for j in nearest:
            edges.append((i, j, dist_matrix[i, j]))

    G = nx.Graph()
    for i, j, d in edges:
        G.add_edge(i, j, weight=d)

    mst = nx.minimum_spanning_tree(G)

    connections = []
    for i, j, data in mst.edges(data=True):
        connections.append({
            "from_id": int(df.iloc[i]["Pole_ID"]),
            "to_id": int(df.iloc[j]["Pole_ID"]),
            "from_xy": tuple(coords[i]),
            "to_xy": tuple(coords[j]),
            "distance": float(data["weight"])
        })

    fig = plot_connections(df, connections, "Automatic Fusion (MST)")
    return connections, fig