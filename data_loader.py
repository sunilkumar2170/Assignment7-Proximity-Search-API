import os
import pandas as pd
import numpy as np

# Column ordering constant for link parsing: "lat_lon" or "lon_lat"
COORD_ORDER = "lon_lat"

class LocationStore:
    def __init__(self, csv_path=None):
        if csv_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(base_dir, "data", "locations.csv")
            if not os.path.exists(csv_path):
                csv_path = os.path.join(base_dir, "locations.csv")

        df = pd.read_csv(csv_path)
        self.ids = df["ID"].to_numpy()
        self.lats = df["Latitude"].to_numpy(dtype=np.float64)
        self.lons = df["Longitude"].to_numpy(dtype=np.float64)
        self.categories = df["Category"].to_numpy()

        # Build coordinate lookup dictionary
        self.coord_to_node = {
            (round(lat, 6), round(lon, 6)): i
            for i, (lat, lon) in enumerate(zip(self.lats, self.lons))
        }

        # Precompute category mapping
        self.category_map = {
            cat: np.where(self.categories == cat)[0]
            for cat in np.unique(self.categories)
        }

    def __len__(self):
        return len(self.ids)


if __name__ == "__main__":
    store = LocationStore()
    print(len(store), "locations loaded")
