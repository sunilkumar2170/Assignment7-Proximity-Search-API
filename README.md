# Proximity Search API

A FastAPI service that finds the 10 closest locations to a given point, filtered by category and search radius, ranked by actual road-network traversal distance — built on a dataset of 10,000 locations laid out on a 100×100 grid.

---

## Table of contents

- [Overview](#overview)
- [How it works](#how-it-works)
- [API reference](#api-reference)
- [Road Linkage & Graph Caching](#road-linkage--graph-caching)
- [Project structure](#project-structure)
- [Running locally](#running-locally)
- [Testing](#testing)

---

## Overview

| Field | Description |
|---|---|
| **Input** | Current latitude (`lat`), longitude (`long`), category (`cat`), search radius (`rad`), and optional road linkage (`link`) |
| **Output** | IDs of the 10 closest matching locations |
| **Dataset** | 10,000 locations, 8 categories (1,250 each), arranged on a 100×100 lattice over `[0,1] × [0,1]` |
| **Road Linkage** | Real road connections loaded from `link.txt` (or uploaded/fetched via `link` param) |
| **Stack** | Python · FastAPI · Uvicorn · NumPy · SciPy (KD-tree + Dijkstra) · pandas · requests |

---

## How it works

```
locations.csv + link.txt
     │
     ▼
data_loader.py     loads locations.csv, maps (lat, lon) to grid node indices,
                    precomputes category lookup mapping
     │
     ▼
graph_builder.py    parses road linkage entries (4-coordinate lines or 2-ID lines),
                    builds SciPy CSR sparse matrix graph with real edge weights
     │
     ▼
search_engine.py    for a query point (lat, long, cat, rad, link):
                       1. retrieves/caches the sparse graph for the given link
                       2. snaps query point to nearest grid node using KD-tree
                       3. runs Dijkstra shortest-path algorithm over the link graph
                       4. filters candidates by category and circular Euclidean radius
                       5. ranks valid candidates by traversal distance, returns top 10
     │
     ▼
main.py             exposes GET /search/ and POST /search/ endpoints
```

Two different distance measures are used:
- **Radius check** → circular (Euclidean) distance from the query point ($d \le \text{rad} + 10^{-9}$).
- **Ranking** → graph distance (Dijkstra over the road linkage graph).

---

## API reference

### `GET /search/` or `POST /search/`

| Parameter | Type | In | Description |
|---|---|---|---|
| `lat` | float | Query / Form | Current latitude |
| `long` | float | Query / Form | Current longitude |
| `cat` | string | Query / Form | Category to search for |
| `rad` | float | Query / Form | Search radius (circular distance) |
| `link` | string / file | Query / Form / File | Linkage file path, URL (e.g. Google Drive view URL), or file upload |

**Example GET Query**

```http
GET /search/?lat=0.5&long=0.5&cat=bank&rad=0.3
```

**Response**

```json
{
  "results": [4850, 4948, 4947, 4648, 5348, 4451, 4753, 5347, 4654, 5349]
}
```

---

## Road Linkage & Graph Caching

- **Dynamic Link Input:** `link` can be passed as a local file path, a direct download URL, a Google Drive share URL (automatically converted to direct download link), or uploaded as a text file (`POST` multipart).
- **Fallback:** If `link` is omitted or cannot be fetched, the API automatically falls back to bundled `link.txt`.
- **Graph Caching:** Pre-built graph matrices are cached by content hash in memory so repeated queries using the same road network do not rebuild the graph.

---

## Project structure

```
nearest-locations-api/
├── data_loader.py      loads locations.csv, builds coordinate & category maps
├── graph_builder.py    parses road linkage entries & builds SciPy CSR graph
├── search_engine.py    handles graph caching, KD-tree snapping, Dijkstra ranking
├── main.py              FastAPI app, exposes GET/POST /search/
├── link.txt            road linkage dataset (14,800 lines)
├── data/
│   └── locations.csv   10,000 location records
├── tests/
│   └── test_search.py  automated test suite with sanity check verification
├── requirements.txt
└── README.md
```

---

## Running locally

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Interactive documentation: `http://localhost:8000/docs`

---

## Testing

```bash
python tests/test_search.py
```
