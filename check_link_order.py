
import os
from data_loader import LocationStore
from graph_builder import build_graph_from_lines
from search_engine import SearchEngine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
link_path = os.path.join(BASE_DIR, "link.txt")

store = LocationStore()

with open(link_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for order in ("lat_lon", "lon_lat"):
    graph = build_graph_from_lines(
        lines, store, coord_order=order
    )
    engine = SearchEngine()
    result = engine.search(
        0.5, 0.5, "bank", 0.3, link=graph
    )
    print(f"\nCoordinate order: {order}")
    print("Results:", result)
