import geopandas as gpd
import pandas as pd

def load_hex_data():
    """Load the hex data from parquet file"""
    columns = ['h3', 'population', 'geometry', 'centroid', 'lat', 'lon', 'density_per_mi2', 'city', 'county', 'state', 'country']
    gdf = gpd.read_parquet(r"parquet_files\us_hexes_with_geonames.parquet", columns=columns)
    return gdf

def save_unique_locations():
    """Save all unique city and county names to CSV files"""
    gdf = load_hex_data()
    
    # Get unique cities with their states
    cities_df = gdf[['city', 'state']].dropna().drop_duplicates().sort_values(['state', 'city'])
    cities_df.to_csv('unique_cities.csv', index=False)
    print(f"Saved {len(cities_df)} unique cities to unique_cities.csv")
    
    # Get unique counties with their states
    counties_df = gdf[['county', 'state']].dropna().drop_duplicates().sort_values(['state', 'county'])
    counties_df.to_csv('unique_counties.csv', index=False)
    print(f"Saved {len(counties_df)} unique counties to unique_counties.csv")

if __name__ == "__main__":
    save_unique_locations() 