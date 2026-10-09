import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search_engine import SearchEngine
from data_loader import COORD_ORDER

engine = SearchEngine()
link_path = os.path.join(os.path.dirname(__file__), "..", "link.txt")


def check(lat, lon, category, radius, link=None):
    result = engine.search(lat, lon, category, radius, link=link)

    categories_ok = all(engine.store.categories[engine.store.ids == rid][0] == category for rid in result)

    within_radius_ok = True
    for rid in result:
        idx = int(engine.store.ids.tolist().index(rid))
        d = ((engine.store.lats[idx] - lat) ** 2 + (engine.store.lons[idx] - lon) ** 2) ** 0.5
        if d > radius + 1e-9:
            within_radius_ok = False

    no_duplicates = len(result) == len(set(result))

    status = "PASS" if (categories_ok and within_radius_ok and no_duplicates) else "FAIL"
    print(f"{status} | lat={lat} lon={lon} cat={category} rad={radius} -> {len(result)} results: {result}")
    return result


print(f"--- SANITY CHECK (lat=0.5, lon=0.5, cat=bank, rad=0.3 with link.txt | COORD_ORDER={COORD_ORDER}) ---")
res = check(0.5, 0.5, "bank", 0.3, link=link_path)

if COORD_ORDER == "lon_lat":
    expected_sanity = [4850, 4948, 4947, 4648, 5349, 4753, 4451, 5348, 5347, 4654]
else:
    expected_sanity = [4850, 4948, 4947, 4648, 5348, 4451, 4753, 5347, 4654, 5349]

if res == expected_sanity:
    print(f"SUCCESS: Result matches expected {COORD_ORDER} sanity check exactly!")
else:
    print(f"MISMATCH: Expected {expected_sanity}, got {res}")

print("\n--- Additional Query Tests ---")
check(0.0, 0.0, "hospital", 0.3, link=link_path)
check(1.0, 1.0, "cafe", 0.3, link=link_path)
check(0.233, 0.777, "store", 0.25, link=link_path)
