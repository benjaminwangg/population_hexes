import geopandas as gpd
import reverse_geocode
import time
hex_area_mi2 = 0.2857156


# Load original data
gdf = gpd.read_file("kontur_population_MX_20231101.gpkg")

# Project to EPSG:3857 (units = meters)
# Save original polygons before projection
original_polygons = gdf["geometry"]

# Project for centroid math
gdf = gdf.to_crs("EPSG:3857")
gdf["centroid"] = gdf.geometry.centroid
# coords like da x,y like minecraft 

# Reproject centroids to WGS84
centroids_wgs84 = gdf.set_geometry("centroid").to_crs("EPSG:4326")
#4326 is like degrees and shit
gdf["lat"] = centroids_wgs84.geometry.y
gdf["lon"] = centroids_wgs84.geometry.x

# ✅ Restore original polygon geometry (in WGS84)
gdf = gdf.set_geometry(original_polygons)
gdf = gdf.to_crs("EPSG:4326")
# degrees like lat and long

# Optional: assign a proper centroid geometry column too
gdf["centroid"] = gpd.points_from_xy(gdf["lon"], gdf["lat"])

print(gdf.head())
# Compute population density
gdf["density_per_mi2"] = gdf["population"] / hex_area_mi2

# Reverse geocode in batches
batch_size = 10000
num_rows = len(gdf)
num_batches = (num_rows + batch_size - 1) // batch_size

cities, counties, states, countries = [], [], [], []

start = time.time()
print(f"Starting reverse geocoding for {num_rows} rows in {num_batches} batches...")

for i in range(num_batches):
    batch = gdf.iloc[i * batch_size : (i + 1) * batch_size]
    latlon_points = list(zip(batch["lat"], batch["lon"]))

    try:
        results = reverse_geocode.search(latlon_points)
    except Exception as e:
        print(f"❌ Error in batch {i}: {e}")
        results = [{"city": None, "county": None, "state": None, "country": None}] * len(batch)

    cities.extend([r.get("city") for r in results])
    counties.extend([r.get("county") for r in results])
    states.extend([r.get("state") for r in results])
    countries.extend([r.get("country") for r in results])

    print(f"✅ Batch {i+1}/{num_batches} complete")

# Assign reverse geocode results
gdf["city"] = cities
gdf["county"] = counties
gdf["state"] = states
gdf["country"] = countries

# Save output
gdf.to_parquet("mx_hexes_with_geonames2.parquet")
print("✅ Saved enriched GeoDataFrame to 'mx_hexes_with_geonames2.parquet'")

end = time.time()
print(f"⏱️ Total processing time: {round(end - start, 2)} seconds")
