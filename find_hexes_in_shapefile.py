import geopandas as gpd
from pathlib import Path

def load_hex_data():
    """Load the hex data from parquet file"""
    columns = ['h3', 'population', 'geometry', 'centroid', 'lat', 'lon', 'density_per_mi2']
    gdf = gpd.read_parquet(r"parquet_files\ng_hexes_with_coordinates.parquet", columns=columns)
    return gdf

def load_shapefile_boundary():
    """Load the shapefile boundary"""
    try:
        # Load the shapefile
        boundary = gpd.read_file(r"nyu_2451_36990/ng.shp")
        print(f"Loaded shapefile with {len(boundary)} features")
        print(f"Shapefile columns: {list(boundary.columns)}")
        print(f"Shapefile CRS: {boundary.crs}")
        
        # If there are multiple features, we can either:
        # 1. Use the first feature, or
        # 2. Combine all features into one boundary
        
        if len(boundary) > 1:
            print(f"Multiple features found. Combining {len(boundary)} features into single boundary...")
            # Dissolve all features into one
            boundary = boundary.dissolve()
            print("Features combined successfully")
        
        return boundary
        
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        return None

def create_output_folder():
    """Create output folder if it doesn't exist"""
    output_dir = Path("shapefile_hexes")
    output_dir.mkdir(exist_ok=True)
    return output_dir

def find_hexes_in_boundary(hex_gdf, boundary_gdf):
    """Find hexes that intersect with a boundary"""
    
    # Handle CRS issues
    if boundary_gdf.crs is None:
        print("⚠️  Shapefile has no CRS defined. Assuming WGS84 (EPSG:4326)...")
        # Set the boundary to WGS84
        boundary_gdf = boundary_gdf.set_crs('EPSG:4326')
    
    print(f"Boundary CRS: {boundary_gdf.crs}")
    print(f"Hex data CRS: {hex_gdf.crs}")
    
    # Ensure both GeoDataFrames are in the same CRS
    if hex_gdf.crs != boundary_gdf.crs:
        print(f"Converting hex data from {hex_gdf.crs} to {boundary_gdf.crs}...")
        hex_gdf = hex_gdf.to_crs(boundary_gdf.crs)
    
    # Find intersecting hexes
    print("Finding intersecting hexes...")
    intersecting_hexes = gpd.sjoin(hex_gdf, boundary_gdf, how='inner', predicate='intersects')
    
    # Remove duplicates based on h3 index
    intersecting_hexes = intersecting_hexes.drop_duplicates(subset=['h3'])
    
    print(f"Found {len(intersecting_hexes)} intersecting hexes")
    return intersecting_hexes

def save_hexes(hex_gdf, boundary_gdf, output_dir):
    """Save all hexes within the boundary"""
    
    # Find hexes within boundary
    boundary_hexes = find_hexes_in_boundary(hex_gdf, boundary_gdf)
    
    if not boundary_hexes.empty:
        # Save to parquet
        output_file = output_dir / "all_hexes_in_boundary.parquet"
        boundary_hexes.to_parquet(output_file)
        print(f"Saved {len(boundary_hexes)} hexes to {output_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total hexes found: {len(boundary_hexes):,}")
        print(f"Total population: {boundary_hexes['population'].sum():,}")
        print(f"Average population per hex: {boundary_hexes['population'].mean():,.0f}")
        
        return boundary_hexes
    else:
        print("No hexes found within the boundary")
        return None

def main():
    """Main function to find all hexes within shapefile boundary"""
    
    print("Shapefile Hex Finder")
    print("=" * 50)
    
    # Create output folder
    output_dir = create_output_folder()
    
    # Load data
    print("\nLoading hex data...")
    hex_gdf = load_hex_data()
    print(f"Loaded {len(hex_gdf):,} hexes")
    
    print("\nLoading shapefile boundary...")
    boundary_gdf = load_shapefile_boundary()
    
    if boundary_gdf is None:
        print("Failed to load shapefile. Exiting.")
        return
    
    # Additional debugging info
    print(f"Shapefile info:")
    print(f"  - Number of features: {len(boundary_gdf)}")
    print(f"  - CRS: {boundary_gdf.crs}")
    print(f"  - Bounds: {boundary_gdf.total_bounds}")
    print(f"  - Geometry types: {boundary_gdf.geometry.geom_type.unique()}")
    
    # Process and save hexes
    print("\nFinding hexes within boundary...")
    result_hexes = save_hexes(hex_gdf, boundary_gdf, output_dir)
    
    if result_hexes is not None:
        print(f"\n✅ Successfully processed shapefile!")
        print(f"📁 Results saved to: {output_dir}/")
        print(f"📊 Found {len(result_hexes):,} hexes within the boundary")
    else:
        print("\n❌ No hexes found within the boundary")

if __name__ == "__main__":
    main()
