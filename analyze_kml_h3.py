import pandas as pd
from shapely.geometry import shape
import geopandas as gpd

# Step 1: Read the KML file using GeoPandas
kml_file = '75pct_coverage.kml'
gdf_kml = gpd.read_file(kml_file)

# Check the structure of the KML data
print(gdf_kml.columns)
print(gdf_kml.head())

# Step 2: Load the Hex8 data from Parquet
hex_data = gpd.read_parquet('parquets/mx_hexes_with_geonames.parquet')

# Ensure the 'geometry' column in hex_data is in Shapely format
hex_data['geometry'] = hex_data['geometry'].apply(shape)

# Step 3: Initialize an empty GeoDataFrame to hold the intersecting hexagons
intersecting_hexagons_gdf = gpd.GeoDataFrame(columns=hex_data.columns, crs=hex_data.crs)

# Step 4: Iterate through each KML polygon and find intersecting or contained hexagons
for _, kml_polygon in gdf_kml.iterrows():
    polygon = kml_polygon['geometry']
    
    # Filter hexagons that either intersect or are within the KML polygon
    intersecting_or_contained = hex_data[
        hex_data['geometry'].apply(lambda x: x.intersects(polygon) or x.within(polygon))
    ]
    
    # Filter out columns with all NA or empty values before concatenating
    intersecting_or_contained = intersecting_or_contained.dropna(axis=1, how='all')  # Drop columns with all NA values
    
    # Use pd.concat to combine the GeoDataFrames
    intersecting_hexagons_gdf = pd.concat([intersecting_hexagons_gdf, intersecting_or_contained], ignore_index=True)

# Step 5: Output the results
print(f"Found {len(intersecting_hexagons_gdf)} hexagons that intersect or are contained within the KML polygons.")

# Step 6: Save the intersecting hexagons to a new Parquet file
intersecting_hexagons_gdf.to_parquet('intersecting_or_contained_hexagons_75.parquet')

# Optionally, check the saved file
intersecting_hexagons_gdf.head()
