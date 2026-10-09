import os
import re
import hashlib
import requests
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import dijkstra

from data_loader import LocationStore, COORD_ORDER
from graph_builder import build_default_graph, build_graph_from_lines


def convert_google_drive_url(url):
    if "drive.google.com" in url:
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        match = re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


class SearchEngine:
    def __init__(self, csv_path=None):
        self.store = LocationStore(csv_path)
        self.tree = cKDTree(np.column_stack((self.store.lats, self.store.lons)))
        self.default_graph = build_default_graph(self.store, coord_order=COORD_ORDER)
        self.graph_cache = {}

    def get_graph(self, link_input=None):
        if link_input is None:
            return self.default_graph

        # If already a cached sparse matrix graph, return it directly
        if hasattr(link_input, "tocsr"):
            return link_input

        # Handle string or bytes input
        cache_key = None
        if isinstance(link_input, str):
            cache_key = hashlib.md5(link_input.encode("utf-8")).hexdigest()
            if cache_key in self.graph_cache:
                return self.graph_cache[cache_key]
        elif isinstance(link_input, bytes):
            cache_key = hashlib.md5(link_input).hexdigest()
            if cache_key in self.graph_cache:
                return self.graph_cache[cache_key]

        try:
            lines = None
            if isinstance(link_input, str):
                s = link_input.strip()
                if s.startswith("http://") or s.startswith("https://"):
                    url = convert_google_drive_url(s)
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        lines = resp.text.splitlines()
                elif os.path.exists(s):
                    with open(s, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                else:
                    lines = s.splitlines()
            elif isinstance(link_input, bytes):
                lines = link_input.decode("utf-8", errors="ignore").splitlines()

            if lines:
                graph = build_graph_from_lines(lines, self.store, coord_order=COORD_ORDER)
                if cache_key:
                    self.graph_cache[cache_key] = graph
                return graph
        except Exception:
            pass

        return self.default_graph

    def search(self, lat, lon, category, radius, link=None, top_k=10):
        graph = self.get_graph(link)

        start_node = self.tree.query([lat, lon])[1]
        distances = dijkstra(graph, indices=start_node)

        candidate_idx = self.store.category_map.get(category)
        if candidate_idx is None or len(candidate_idx) == 0:
            return []

        dx = self.store.lats[candidate_idx] - lat
        dy = self.store.lons[candidate_idx] - lon
        circular_dist = np.sqrt(dx ** 2 + dy ** 2)

        mask = circular_dist <= (radius + 1e-9)
        within_radius = candidate_idx[mask]
        within_euc = circular_dist[mask]
        if len(within_radius) == 0:
            return []

        finite_mask = np.isfinite(distances[within_radius])
        reachable = within_radius[finite_mask]
        if len(reachable) == 0:
            return []

        reachable_euc = within_euc[finite_mask]
        node_ids = self.store.ids[reachable]
        graph_dist = distances[reachable]

        sort_indices = np.lexsort((node_ids, reachable_euc, graph_dist))
        ranked = reachable[sort_indices]
        top = ranked[:top_k]

        return [int(rid) for rid in self.store.ids[top]]


if __name__ == "__main__":
    engine = SearchEngine()
    result = engine.search(lat=0.5, lon=0.5, category="bank", radius=0.3)
    print("Result:", result)