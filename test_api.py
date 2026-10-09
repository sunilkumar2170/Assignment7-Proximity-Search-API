import argparse, json, random, urllib.parse, urllib.request
import numpy as np, pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

BASE = "http://10.1.75.53:5213/search/"
WEIGHT = "euclid"   # or "hop"


def call_api(lat, lon, cat, rad, link):
    q = urllib.parse.urlencode({"lat": lat, "long": lon, "cat": cat, "rad": rad, "link": link})
    with urllib.request.urlopen(f"{BASE}?{q}", timeout=10) as r:
        return json.loads(r.read())["results"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--link", required=True)
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()

    df = pd.read_csv(a.csv).iloc[:, :4]
    df.columns = ["id", "lat", "lon", "cat"]
    ids = df["id"].to_numpy()
    idx = {v: i for i, v in enumerate(ids)}
    xy = df[["lat", "lon"]].to_numpy()

    coord_to_node = {}
    for i in range(len(df)):
        coord_to_node[(round(df["lat"].iloc[i], 6), round(df["lon"].iloc[i], 6))] = i

    rows, cols, w = [], [], []
    for line in open(a.link):
        p = line.split()
        if len(p) == 2:
            u, v = idx[int(p[0])], idx[int(p[1])]
            d = 1.0 if WEIGHT == "hop" else float(np.linalg.norm(xy[u] - xy[v]))
            rows += [u, v]; cols += [v, u]; w += [d, d]
        elif len(p) == 4:
            vals = [float(x) for x in p]
            lat_a, lon_a, lat_b, lon_b = vals[0], vals[1], vals[2], vals[3]
            u = coord_to_node.get((round(lat_a, 6), round(lon_a, 6)))
            v = coord_to_node.get((round(lat_b, 6), round(lon_b, 6)))
            if u is not None and v is not None:
                d = 1.0 if WEIGHT == "hop" else float(np.sqrt((lat_a - lat_b)**2 + (lon_a - lon_b)**2))
                rows += [u, v]; cols += [v, u]; w += [d, d]
    G = csr_matrix((w, (rows, cols)), shape=(len(df), len(df)))

    cats = df["cat"].unique().tolist()
    passed = failed = 0
    for t in range(a.n):
        lat, lon = round(random.random(), 3), round(random.random(), 3)
        cat, rad = random.choice(cats), random.choice([0.15, 0.2, 0.3])
        d_euc = np.linalg.norm(xy - np.array([lat, lon]), axis=1)
        valid = np.where((df["cat"].to_numpy() == cat) & (d_euc <= rad))[0]
        if len(valid) < 10:
            continue
        src = int(np.argmin(d_euc))
        dist = dijkstra(G, directed=False, indices=src)
        order = sorted(valid, key=lambda i: (dist[i], d_euc[i], ids[i]))
        expected = [int(ids[i]) for i in order[:10]]

        got = call_api(lat, lon, cat, rad, a.link)
        ok = (len(got) == 10 and len(set(got)) == 10
              and all(g in set(int(ids[i]) for i in valid) for g in got))
        match = sum(g == e for g, e in zip(got, expected))
        status = "OK " if ok and got == expected else "DIFF"
        print(f"{status} lat={lat} long={lon} cat={cat} rad={rad} "
              f"valid={ok} positional_match={match}/10")
        if status == "OK ":
            passed += 1
        else:
            failed += 1
            print("   got     :", got)
            print("   expected:", expected)
    print(f"\nExact match: {passed}, Differences: {failed}")


if __name__ == "__main__":
    main()