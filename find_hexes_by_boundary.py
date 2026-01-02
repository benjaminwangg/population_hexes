import geopandas as gpd
from pathlib import Path

def load_hex_data():
    """Load the hex data from parquet file"""
    columns = ['h3', 'population', 'geometry', 'centroid', 'lat', 'lon', 'density_per_mi2']
    gdf = gpd.read_parquet(r"parquet_files\us_hexes_with_geonames.parquet", columns=columns)
    return gdf

def load_county_boundaries():
    """Load county boundaries for the specified counties"""
    # Define state FIPS codes
    nj_fips = '34'  # New Jersey
    de_fips = '10'  # Delaware
    pa_fips = '42'  # Pennsylvania
    
    # Load the county shapefile
    counties = gpd.read_file(r"tl_2024_us_county\tl_2024_us_county.shp")
    
    # Define the target counties with their state FIPS codes
    target_counties = [
        ('MONMOUTH', nj_fips),
        ('CAPE MAY', nj_fips),
        ('ATLANTIC', nj_fips),
        ('CAMDEN', nj_fips),
        ('NEW CASTLE', de_fips),
        ('BURLINGTON', nj_fips),
        ('MONTGOMERY', pa_fips)
    ]
    
    # Filter for the target counties
    county_boundaries = {}
    for county_name, state_fips in target_counties:
        county_boundary = counties[(counties['STATEFP'] == state_fips) & 
                                  (counties['NAME'].str.upper() == county_name.upper())]
        if not county_boundary.empty:
            county_boundaries[county_name] = county_boundary
            print(f"Found boundary for {county_name} County")
        else:
            print(f"Warning: No boundary found for {county_name} County")
    
    return county_boundaries

def create_output_folder():
    """Create output folder if it doesn't exist"""
    output_dir = Path("location_hexes_by_boundary1")
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

def save_county_hexes(hex_gdf, county_boundaries, output_dir):
    """Save hexes for each county as a parquet file"""
    total_hexes = 0
    
    for county_name, county_boundary in county_boundaries.items():
        if county_boundary.empty:
            print(f"No boundary data found for {county_name} County")
            continue
            
        # Find hexes within boundary
        county_hexes = find_hexes_in_boundary(hex_gdf, county_boundary)
        
        if not county_hexes.empty:
            # Save to parquet
            output_file = output_dir / f"{county_name.lower().replace(' ', '_')}_county.parquet"
            county_hexes.to_parquet(output_file)
            print(f"Saved {len(county_hexes)} hexes for {county_name} County to {output_file}")
            total_hexes += len(county_hexes)
        else:
            print(f"No hexes found for {county_name} County")
    
    print(f"\nTotal hexes found across all counties: {total_hexes}")

def main():
    # Create output folder
    output_dir = create_output_folder()

    # Load data
    print("Loading hex data...")
    hex_gdf = load_hex_data()
    print(f"Loaded {len(hex_gdf)} hexes")
    
    print("\nLoading county boundaries...")
    county_boundaries = load_county_boundaries()

    # Process and save hexes for each county
    print("\nProcessing counties...")
    save_county_hexes(hex_gdf, county_boundaries, output_dir)

if __name__ == "__main__":
    main()
