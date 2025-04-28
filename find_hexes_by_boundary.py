import geopandas as gpd
import pandas as pd
from pathlib import Path
import os

def load_hex_data():
    """Load the hex data from parquet file"""
    columns = ['h3', 'population', 'geometry', 'centroid', 'lat', 'lon', 'density_per_mi2']
    gdf = gpd.read_parquet(r"parquet_files\us_hexes_with_geonames.parquet", columns=columns)
    return gdf

def load_boundary_data():
    """Load boundary data for all locations"""
    # Define state FIPS codes
    state_fips = {
        'New York': '36',
        'Nevada': '32',
        'California': '06',
        'Pennsylvania': '42',
        'Maryland': '24',
        'Connecticut': '09',
        'Texas': '48',
        'New Jersey': '34'
    }
    
    # Load the county shapefile
    counties = gpd.read_file(r"tl_2024_us_county\tl_2024_us_county.shp")
    
    # Print all Connecticut county names
    ct_counties = counties[counties['STATEFP'] == state_fips['Connecticut']]
    print("\nConnecticut Counties:")
    print(ct_counties['NAME'].unique().tolist())
    print("\n")
    
    # Load state-specific place shapefiles
    state_places = {
        'New York': gpd.read_file(r"tiger_shapefiles\ny_place\tl_2024_36_place.shp"),
        'Nevada': gpd.read_file(r"tiger_shapefiles\nv_place\tl_2024_32_place.shp"),
        'California': gpd.read_file(r"tiger_shapefiles\ca_place\tl_2024_06_place.shp"),
        'Pennsylvania': gpd.read_file(r"tiger_shapefiles\pa_place\tl_2024_42_place.shp"),
        'Maryland': gpd.read_file(r"tiger_shapefiles\ma_place\tl_2024_24_place.shp"),
        'Connecticut': gpd.read_file(r"tiger_shapefiles\ct_place\tl_2023_09_place.shp"),
        'Texas': gpd.read_file(r"tiger_shapefiles\tx_place\tl_2024_48_place.shp"),
        'New Jersey': gpd.read_file(r"tiger_shapefiles\nj_place\tl_2024_34_place.shp")
    }
    
    # Define all locations from create_location_parquets.py
    boundaries = {
        # NYC (combined boroughs)
        "new_york_city": counties[
            (counties['STATEFP'] == state_fips['New York']) & 
            (counties['NAME'].isin(['Kings', 'New York', 'Queens', 'Bronx', 'Richmond']))
        ],
        
        # Nevada
        "clark_county": counties[
            (counties['STATEFP'] == state_fips['Nevada']) & 
            (counties['NAME'] == 'Clark')
        ],
        
        # Westchester County
        "westchester_county": counties[
            (counties['STATEFP'] == state_fips['New York']) & 
            (counties['NAME'] == 'Westchester')
        ],
        
        # California (San Francisco)
        "san_francisco_county": counties[
            (counties['STATEFP'] == state_fips['California']) & 
            (counties['NAME'] == 'San Francisco')
        ],
        
        # Philadelphia
        "philadelphia_county": counties[
            (counties['STATEFP'] == state_fips['Pennsylvania']) & 
            (counties['NAME'] == 'Philadelphia')
        ],
        
        # Baltimore
        "baltimore_county": counties[
            (counties['STATEFP'] == state_fips['Maryland']) & 
            (counties['NAME'] == 'Baltimore')
        ],
        
        # Western County (CT)
        "fairfield_county": counties[
            (counties['STATEFP'] == state_fips['Connecticut']) & 
            (counties['NAME'] == 'Western Connecticut')
        ],
        
        # Texas Counties
        "dallas_county": counties[
            (counties['STATEFP'] == state_fips['Texas']) & 
            (counties['NAME'] == 'Dallas')
        ],
        "harris_county": counties[
            (counties['STATEFP'] == state_fips['Texas']) & 
            (counties['NAME'] == 'Harris')
        ],
        "denton_county": counties[
            (counties['STATEFP'] == state_fips['Texas']) & 
            (counties['NAME'] == 'Denton')
        ],
        
        # New Jersey Counties
        "hudson_county": counties[
            (counties['STATEFP'] == state_fips['New Jersey']) & 
            (counties['NAME'] == 'Hudson')
        ],
        "essex_county": counties[
            (counties['STATEFP'] == state_fips['New Jersey']) & 
            (counties['NAME'] == 'Essex')
        ],
        
        # Connecticut Cities
        "stamford": state_places['Connecticut'][state_places['Connecticut']['NAME'] == 'Stamford'],
        "greenwich": state_places['Connecticut'][state_places['Connecticut']['NAME'] == 'Greenwich'],
        "darien": state_places['Connecticut'][state_places['Connecticut']['NAME'] == 'Darien'],
        
        # California Cities
        "san_francisco": state_places['California'][state_places['California']['NAME'] == 'San Francisco'],
        
        # Pennsylvania Cities
        "philadelphia": state_places['Pennsylvania'][state_places['Pennsylvania']['NAME'] == 'Philadelphia'],
        
        # Maryland Cities
        "baltimore": state_places['Maryland'][state_places['Maryland']['NAME'] == 'Baltimore'],
        
        # New York Cities
        "yonkers": state_places['New York'][state_places['New York']['NAME'] == 'Yonkers'],
        "new_york": state_places['New York'][state_places['New York']['NAME'] == 'New York'],
        
        # New Jersey Cities
        "newark": state_places['New Jersey'][state_places['New Jersey']['NAME'] == 'Newark'],
        "jersey_city": state_places['New Jersey'][state_places['New Jersey']['NAME'] == 'Jersey City'],
        
        # Texas Cities
        "houston": state_places['Texas'][state_places['Texas']['NAME'] == 'Houston'],
        "dallas": state_places['Texas'][state_places['Texas']['NAME'] == 'Dallas']
    }
    
    return boundaries

def create_output_folder():
    """Create output folder if it doesn't exist"""
    output_dir = Path("location_hexes_by_boundary")
    output_dir.mkdir(exist_ok=True)
    return output_dir

def find_hexes_in_boundary(hex_gdf, boundary_gdf):
    """Find hexes that intersect with a boundary"""
    # Ensure both GeoDataFrames are in the same CRS
    hex_gdf = hex_gdf.to_crs(boundary_gdf.crs)
    
    # Find intersecting hexes
    intersecting_hexes = gpd.sjoin(hex_gdf, boundary_gdf, how='inner', predicate='intersects')
    
    # Remove duplicates based on h3 index
    intersecting_hexes = intersecting_hexes.drop_duplicates(subset=['h3'])
    
    return intersecting_hexes

def save_location_hexes(hex_gdf, boundaries, output_dir):
    """Save hexes for each location as separate parquet files"""
    for location_name, boundary_gdf in boundaries.items():
        if boundary_gdf.empty:
            print(f"No boundary data found for {location_name}")
            continue
            
        # Find hexes within boundary
        location_hexes = find_hexes_in_boundary(hex_gdf, boundary_gdf)
        
        if not location_hexes.empty:
            # Save to parquet
            output_file = output_dir / f"{location_name}.parquet"
            location_hexes.to_parquet(output_file)
            print(f"Saved {len(location_hexes)} hexes for {location_name} to {output_file}")
        else:
            print(f"No hexes found for {location_name}")

def main():
    # Create output folder
    output_dir = create_output_folder()
    
    # Load data
    hex_gdf = load_hex_data()
    boundaries = load_boundary_data()
    
    # Process and save location hexes
    save_location_hexes(hex_gdf, boundaries, output_dir)

if __name__ == "__main__":
    main() 