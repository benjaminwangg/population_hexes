import geopandas as gpd
import json
from pathlib import Path

def load_hex_data():
    """Load the hex data from parquet file"""
    columns = ['h3', 'population', 'geometry', 'centroid', 'lat', 'lon', 'density_per_mi2']
    gdf = gpd.read_parquet(r"parquet_files\ng_hexes_with_coordinates.parquet", columns=columns)
    return gdf

def load_geojson_boundary(geojson_path):
    """Load boundary from GeoJSON file"""
    try:
        # Load the GeoJSON file
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Convert to GeoDataFrame
        boundary = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        print(f"✅ Successfully loaded GeoJSON with {len(boundary)} features")
        print(f"GeoJSON columns: {list(boundary.columns)}")
        print(f"GeoJSON CRS: {boundary.crs}")
        
        # If there are multiple features, combine them into one boundary
        if len(boundary) > 1:
            print(f"Multiple features found. Combining {len(boundary)} features into single boundary...")
            # Dissolve all features into one
            boundary = boundary.dissolve()
            print("Features combined successfully")
        
        return boundary
        
    except Exception as e:
        print(f"❌ Error loading GeoJSON file: {e}")
        return None

def create_geojson_from_coordinates(coordinates, name="custom_boundary"):
    """Create a simple GeoJSON from coordinate list (alternative to file loading)"""
    try:
        # Create a simple polygon from coordinates
        from shapely.geometry import Polygon
        
        # Ensure coordinates form a closed polygon
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        polygon = Polygon(coordinates)
        gdf = gpd.GeoDataFrame([{'geometry': polygon, 'name': name}], crs='EPSG:4326')
        
        print(f"✅ Created GeoJSON boundary from {len(coordinates)-1} coordinate pairs")
        return gdf
        
    except Exception as e:
        print(f"❌ Error creating GeoJSON from coordinates: {e}")
        return None

def create_output_folder():
    """Create output folder if it doesn't exist"""
    output_dir = Path("geojson_hexes")
    output_dir.mkdir(exist_ok=True)
    return output_dir

def find_hexes_in_boundary(hex_gdf, boundary_gdf):
    """Find hexes that intersect with the boundary"""
    
    # Handle CRS issues
    if boundary_gdf.crs is None:
        print("⚠️  GeoJSON has no CRS defined. Assuming WGS84 (EPSG:4326)...")
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

def save_hexes(hex_gdf, boundary_gdf, output_dir, boundary_name="geojson_boundary"):
    """Save all hexes within the boundary"""
    
    # Find hexes within boundary
    boundary_hexes = find_hexes_in_boundary(hex_gdf, boundary_gdf)
    
    if not boundary_hexes.empty:
        # Save to parquet (with all columns)
        output_file = output_dir / f"hexes_in_{boundary_name}.parquet"
        boundary_hexes.to_parquet(output_file)
        print(f"✅ Saved {len(boundary_hexes):,} hexes to {output_file}")
        
        # Create a clean version for GeoJSON export (only one geometry column)
        geojson_hexes = boundary_hexes.copy()
        
        # Drop the centroid column if it exists (keep only the main geometry)
        if 'centroid' in geojson_hexes.columns:
            geojson_hexes = geojson_hexes.drop(columns=['centroid'])
            print("  - Removed centroid column for GeoJSON export")
        
        # Also save as GeoJSON for visualization
        geojson_output = output_dir / f"hexes_in_{boundary_name}.geojson"
        geojson_hexes.to_file(geojson_output, driver='GeoJSON')
        print(f"✅ Saved hexes as GeoJSON: {geojson_output}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total hexes found: {len(boundary_hexes):,}")
        print(f"Total population: {boundary_hexes['population'].sum():,}")
        print(f"Average population per hex: {boundary_hexes['population'].mean():,.0f}")
        
        # Show coordinate ranges
        if 'lat' in boundary_hexes.columns and 'lon' in boundary_hexes.columns:
            print(f"Latitude range: {boundary_hexes['lat'].min():.6f} to {boundary_hexes['lat'].max():.6f}")
            print(f"Longitude range: {boundary_hexes['lon'].min():.6f} to {boundary_hexes['lon'].max():.6f}")
        
        return boundary_hexes
    else:
        print("❌ No hexes found within the boundary")
        return None

def main():
    """Main function to find hexes within GeoJSON boundary"""
    
    print("GeoJSON Hex Finder")
    print("=" * 50)
    
    # Configuration
    geojson_file = r"tl_2024_us_county\lagos.geojson"  # Update this path as needed
    
    # Alternative: Create boundary from coordinates
    use_coordinates = False  # Set to True to use coordinate method instead
    
    # Create output folder
    output_dir = create_output_folder()
    
    # Load data
    print("\nLoading hex data...")
    hex_gdf = load_hex_data()
    print(f"Loaded {len(hex_gdf):,} hexes")
    
    # Load boundary
    if use_coordinates:
        print("\nCreating boundary from coordinates...")
        # Example coordinates for Nigeria (approximate bounding box)
        nigeria_coords = [
            (3.0, 4.0),   # Southwest
            (15.0, 4.0),  # Southeast  
            (15.0, 14.0), # Northeast
            (3.0, 14.0),  # Northwest
            (3.0, 4.0)    # Close the polygon
        ]
        boundary_gdf = create_geojson_from_coordinates(nigeria_coords, "nigeria_bbox")
    else:
        print("\nLoading GeoJSON boundary...")
        boundary_gdf = load_geojson_boundary(geojson_file)
    
    if boundary_gdf is None:
        print("Failed to load boundary. Exiting.")
        return
    
    # Additional debugging info
    print(f"\nBoundary info:")
    print(f"  - Number of features: {len(boundary_gdf)}")
    print(f"  - CRS: {boundary_gdf.crs}")
    print(f"  - Bounds: {boundary_gdf.total_bounds}")
    print(f"  - Geometry types: {boundary_gdf.geometry.geom_type.unique()}")
    
    # Process and save hexes
    print("\nFinding hexes within boundary...")
    boundary_name = "geojson_boundary" if not use_coordinates else "nigeria_bbox"
    result_hexes = save_hexes(hex_gdf, boundary_gdf, output_dir, boundary_name)
    
    if result_hexes is not None:
        print(f"\n🎉 Successfully processed GeoJSON boundary!")
        print(f"📁 Results saved to: {output_dir}/")
        print(f"📊 Found {len(result_hexes):,} hexes within the boundary")
        
        # Show output files
        print(f"\nOutput files:")
        for file_path in output_dir.glob("*"):
            if file_path.is_file():
                print(f"  📄 {file_path.name}")
    else:
        print("\n❌ No hexes found within the boundary")

if __name__ == "__main__":
    main()
