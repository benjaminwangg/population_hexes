import geopandas as gpd
import reverse_geocode
import time
hex_area_mi2 = 0.2857156


# Load original data
gdf = gpd.read_file("gpkgs\kontur_population_LT_20231101.gpkg")

# Project to EPSG:3857 (units = meters)
# Save original polygons before projection

print(gdf.head())
# Compute population density
gdf["density_per_mi2"] = gdf["population"] / hex_area_mi2


# Save output
gdf.to_parquet("lt_hexes.parquet")
print("✅ Saved enriched GeoDataFrame to 'mx_hexes_with_geonames.parquet'")

end = time.time()
