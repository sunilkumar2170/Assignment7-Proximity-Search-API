import os
import numpy as np
from scipy.sparse import coo_matrix

COORD_ORDER = "lon_lat"


def build_graph_from_lines(lines, store, coord_order=COORD_ORDER):
    n = len(store)
    src, dst, weights = [], [], []

    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="ignore")
        parts = line.strip().split()
        if not parts:
            continue

        if len(parts) == 4:
            try:
                vals = [float(p) for p in parts]
            except ValueError:
                continue

            if coord_order == "lat_lon":
                lat_a, lon_a, lat_b, lon_b = vals[0], vals[1], vals[2], vals[3]
            else:
                lon_a, lat_a, lon_b, lat_b = vals[0], vals[1], vals[2], vals[3]

            i = store.coord_to_node.get((round(lat_a, 6), round(lon_a, 6)))
            j = store.coord_to_node.get((round(lat_b, 6), round(lon_b, 6)))

            if i is not None and j is not None:
                d = np.sqrt((lat_a - lat_b) ** 2 + (lon_a - lon_b) ** 2)
                src.append(i)
                dst.append(j)
                weights.append(d)

        elif len(parts) == 2:
            try:
                id_a, id_b = int(parts[0]), int(parts[1])
            except ValueError:
                continue

            i = id_a - 1 if 0 <= id_a - 1 < n else None
            j = id_b - 1 if 0 <= id_b - 1 < n else None

            if i is not None and j is not None:
                d = np.sqrt((store.lats[i] - store.lats[j]) ** 2 + (store.lons[i] - store.lons[j]) ** 2)
                src.append(i)
                dst.append(j)
                weights.append(d)

    full_src = src + dst
    full_dst = dst + src
    full_weights = weights + weights

    if not full_src:
        return coo_matrix((n, n)).tocsr()

    return coo_matrix((full_weights, (full_src, full_dst)), shape=(n, n)).tocsr()


def build_default_graph(store, coord_order=COORD_ORDER):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "link.txt"),
        os.path.join(base_dir, "data", "link.txt"),
    ]

    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return build_graph_from_lines(f, store, coord_order=coord_order)

    # Fallback to full grid if link.txt is missing
    n = len(store)
    index_of = {}
    for i in range(n):
        r = round(store.lats[i], 6)
        c = round(store.lons[i], 6)
        index_of[(r, c)] = i

    src, dst, weights = [], [], []
    unique_lats = sorted(set(np.round(store.lats, 6)))
    unique_lons = sorted(set(np.round(store.lons, 6)))
    lat_step = unique_lats[1] - unique_lats[0] if len(unique_lats) > 1 else 0.010101
    lon_step = unique_lons[1] - unique_lons[0] if len(unique_lons) > 1 else 0.010101

    for i in range(n):
        r, c = round(store.lats[i], 6), round(store.lons[i], 6)
        for dr, dc in [(lat_step, 0), (0, lon_step)]:
            j = index_of.get((round(r + dr, 6), round(c + dc, 6)))
            if j is not None:
                d = np.sqrt(dr ** 2 + dc ** 2)
                src.append(i)
                dst.append(j)
                weights.append(d)

    full_src = src + dst
    full_dst = dst + src
    full_weights = weights + weights
    return coo_matrix((full_weights, (full_src, full_dst)), shape=(n, n)).tocsr()