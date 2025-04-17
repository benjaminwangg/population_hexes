import geopandas as gpd
import reverse_geocode
import time

# Load GeoDataFrame
gdf = gpd.read_file(r"DISH_gpkgs\ID.gpkg")
hex_area_mi2 = 0.2857156
print(gdf.head())
gdf.to_parquet("ID_US_hexes.parquet")
