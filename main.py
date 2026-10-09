import math
from typing import Optional
from fastapi import FastAPI, Query, Form, File, UploadFile, HTTPException, Request

from search_engine import SearchEngine

app = FastAPI(title="Proximity Search API")
engine = SearchEngine()


def validate_params(lat: float, long: float, cat: str, rad: float):
    if math.isnan(lat) or math.isinf(lat):
        raise HTTPException(status_code=400, detail="Latitude must be a valid finite number")
    if math.isnan(long) or math.isinf(long):
        raise HTTPException(status_code=400, detail="Longitude must be a valid finite number")
    if math.isnan(rad) or math.isinf(rad) or rad < 0:
        raise HTTPException(status_code=400, detail="Radius must be a valid non-negative finite number")
    if not cat or not isinstance(cat, str):
        raise HTTPException(status_code=400, detail="Category must be a non-empty string")


@app.get("/search/")
def search_get(
    lat: float = Query(..., description="Current latitude"),
    long: float = Query(..., description="Current longitude"),
    cat: str = Query(..., description="Category to search for"),
    rad: float = Query(..., description="Search radius (circular distance)"),
    link: Optional[str] = Query(None, description="Linkage file URL, path, or content")
):
    validate_params(lat, long, cat, rad)
    ids = engine.search(lat=lat, lon=long, category=cat, radius=rad, link=link)
    return {"results": ids}


@app.post("/search/")
async def search_post(
    request: Request,
    lat: Optional[float] = Form(None),
    long: Optional[float] = Form(None),
    cat: Optional[str] = Form(None),
    rad: Optional[float] = Form(None),
    link: Optional[str] = Form(None),
    link_file: Optional[UploadFile] = File(None)
):
    # Check if params passed via query parameters or form fields
    q_params = request.query_params
    if lat is None and "lat" in q_params:
        lat = float(q_params["lat"])
    if long is None and "long" in q_params:
        long = float(q_params["long"])
    if cat is None and "cat" in q_params:
        cat = q_params["cat"]
    if rad is None and "rad" in q_params:
        rad = float(q_params["rad"])
    if link is None and "link" in q_params:
        link = q_params["link"]

    # Check JSON body if parameters are still missing
    if (lat is None or long is None or cat is None or rad is None) and request.headers.get("content-type") == "application/json":
        try:
            body = await request.json()
            lat = lat if lat is not None else float(body.get("lat"))
            long = long if long is not None else float(body.get("long"))
            cat = cat if cat is not None else str(body.get("cat"))
            rad = rad if rad is not None else float(body.get("rad"))
            link = link if link is not None else body.get("link")
        except Exception:
            pass

    if lat is None or long is None or cat is None or rad is None:
        raise HTTPException(status_code=400, detail="Missing required parameters (lat, long, cat, rad)")

    validate_params(lat, long, cat, rad)

    # Process uploaded file if provided
    link_content = link
    if link_file is not None:
        try:
            link_content = await link_file.read()
        except Exception:
            pass

    ids = engine.search(lat=lat, lon=long, category=cat, radius=rad, link=link_content)
    return {"results": ids}