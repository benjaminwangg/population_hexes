import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import pandas as pd
import h3
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point


def hex_to_polygon(hex_id):
    """Convert H3 hexagon to Shapely Polygon"""
    hex_boundary = h3.cell_to_boundary(hex_id)
    return Polygon(hex_boundary)

def get_hexes_in_radius(center_lat, center_lon, radius_km, resolution=8):
    """Get all hexes within a given radius using apothem height"""
    # Get center hexagon
    center_hex = h3.latlng_to_cell(center_lat, center_lon, resolution)
    
    # Calculate number of rings needed using apothem height
    # At resolution 8, apothem height is 0.9204 km
    k = int(np.ceil(radius_km / 0.9204))
    
    # Get all hexagons within k rings
    hexagons = h3.grid_disk(center_hex, k)
    
    return hexagons, center_hex, k

def create_hex_dataframe(hexagons, center_hex, center_lat, center_lon):
    """Create a GeoDataFrame with hexagon properties"""
    # Convert hexagons to polygons
    polygons = [hex_to_polygon(hex_id) for hex_id in hexagons]
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=polygons)
    
    # Add H3 ID
    gdf['h3'] = hexagons
    
    # Add resolution
    gdf['resolution'] = h3.get_resolution(hexagons[0])
    
    # Calculate distance from center for each hex
    center_lat, center_lon = h3.cell_to_latlng(center_hex)
    distances = []
    for hex_id in hexagons:
        hex_lat, hex_lon = h3.cell_to_latlng(hex_id)
        distance = h3.great_circle_distance((center_lat, center_lon), (hex_lat, hex_lon), unit='km')
        distances.append(distance)
    
    gdf['distance_from_center_km'] = distances
    
    # Add area
    gdf['area_km2'] = [h3.cell_area(hex_id, unit='km^2') for hex_id in hexagons]
    
    return gdf

def visualize_hexes(gdf, center_lat, center_lon, k):
    """Visualize hexagons with center point"""
    # Plot
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(ax=ax, alpha=0.5, edgecolor='black')
    
    # Add center point
    center_point = Point(center_lon, center_lat)
    gpd.GeoDataFrame(geometry=[center_point]).plot(ax=ax, color='red', markersize=100)
    
    # Add title with statistics
    title = f"Hexes within {k} rings of center\n"
    title += f"Number of Hexagons: {len(gdf)}"
    plt.title(title)
    
    plt.show()

def main():
    # Example: Times Square, NYC
    center_lat, center_lon = 40.7580, -73.9855
    radius_km = 6  # 6 km radius
    
    # Get hexes within radius
    hexagons, center_hex, k = get_hexes_in_radius(center_lat, center_lon, radius_km)
    
    # Create GeoDataFrame with properties
    gdf = create_hex_dataframe(hexagons, center_hex, center_lat, center_lon)
    
    # Visualize results
    visualize_hexes(gdf, center_lat, center_lon, k)
    
    # Save to parquet
    output_file = "hexes_6km_radius.parquet"
    gdf.to_parquet(output_file)
    print(f"Saved {len(gdf)} hexagons to {output_file}")
    
    # Print statistics
    print(f"Center hex: {center_hex}")
    print(f"Number of rings (k): {k}")
    print(f"Number of hexagons: {len(gdf)}")
    print(f"Total area covered: {gdf['area_km2'].sum():.2f} km²")
    print(f"Average distance from center: {gdf['distance_from_center_km'].mean():.2f} km")
    print(f"Maximum distance from center: {gdf['distance_from_center_km'].max():.2f} km")

if __name__ == "__main__":
    main()
