# main.py
# find cursor
from fastapi import FastAPI
from pydantic import BaseModel
from shapely.geometry import Point
import geopandas as gpd
import uvicorn

# ==== INIT FASTAPI ====
app = FastAPI(title="📡 Population + Signal API", description="Query H3 hex-level data by radius")

# ==== LOAD DATA ONCE ====
print("📦 Loading data...")
gdf = gpd.read_parquet("parquet_files/us_hexes_with_geonames.parquet").to_crs(epsg=3857)
gdf["centroid"] = gdf.geometry.centroid
gdf["area"] = gdf.geometry.area
print(f"✅ Loaded {len(gdf)} hexes")

# ==== REQUEST MODEL ====
class RadiusQuery(BaseModel):
    lat: float
    lon: float
    radius_km: float

# ==== ENDPOINT ====
@app.post("/query_radius")
def query_population_within_radius(query: RadiusQuery):
    point = Point(query.lon, query.lat)
    point_m = gpd.GeoSeries([point], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
    buffer = point_m.buffer(query.radius_km * 1000)

    intersecting = gdf[gdf.intersects(buffer)].copy()

    if intersecting.empty:
        return {"total_population": 0, "matched_hexes": 0}

    intersecting["intersect_area"] = intersecting.geometry.intersection(buffer).area
    intersecting["intersect_pct"] = intersecting["intersect_area"] / intersecting["area"]

    intersecting["weighted_pop"] = intersecting["population"] * intersecting["intersect_pct"]

    total_population = int(intersecting["weighted_pop"].sum())

    return {
        "total_population": total_population,
        "matched_hexes": len(intersecting),
        "radius_km": query.radius_km
    }

# ==== RUN LOCALLY ====
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
