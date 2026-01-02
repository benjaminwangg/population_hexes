import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from pathlib import Path

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

def load_hex_data():
    """Load the hex data from parquet file"""
    columns = ['h3', 'population', 'geometry', 'centroid', 'lat', 'lon', 'density_per_mi2']
    gdf = gpd.read_parquet(r"parquet_files\ng_hexes_with_coordinates.parquet", columns=columns)
    return gdf

def find_hexes_and_population_for_coordinate(center_lat, center_lon, radius_km, hex_gdf, resolution=8):
    """Find hexes within radius and calculate population statistics for a single coordinate"""
    
    # Get hexes within radius
    hexagons, center_hex, k = get_hexes_in_radius(center_lat, center_lon, radius_km, resolution)
    
    # Filter to only hexagons in our radius that exist in our data
    radius_hexes = hex_gdf[hex_gdf['h3'].isin(hexagons)].copy()
    
    if radius_hexes.empty:
        return {
            'center_lat': center_lat,
            'center_lon': center_lon,
            'center_hex': str(center_hex),
            'radius_km': radius_km,
            'rings': k,
            'hexes_found': 0,
            'total_population': 0,
            'avg_population': 0,
            'total_area_km2': 0,
            'avg_distance_km': 0,
            'max_distance_km': 0
        }
    
    # Calculate distance from center for each hex
    radius_hexes['distance_from_center_km'] = radius_hexes.apply(
        lambda row: h3.great_circle_distance(
            (center_lat, center_lon), 
            (row['lat'], row['lon']), 
            unit='km'
        ), 
        axis=1
    )
    
    # Add area
    radius_hexes['area_km2'] = radius_hexes['h3'].apply(lambda h: h3.cell_area(h, unit='km^2'))
    
    # Calculate statistics
    total_pop = radius_hexes['population'].sum()
    avg_pop = radius_hexes['population'].mean()
    total_area = radius_hexes['area_km2'].sum()
    avg_distance = radius_hexes['distance_from_center_km'].mean()
    max_distance = radius_hexes['distance_from_center_km'].max()
    
    return {
        'center_lat': center_lat,
        'center_lon': center_lon,
        'center_hex': str(center_hex),
        'radius_km': radius_km,
        'rings': k,
        'hexes_found': len(radius_hexes),
        'total_population': total_pop,
        'avg_population': avg_pop,
        'total_area_km2': total_area,
        'avg_distance_km': avg_distance,
        'max_distance_km': max_distance
    }

def process_coordinate_list(coordinates, radius_km, resolution=8):
    """Process a list of coordinates and find hexes within radius for each"""
    
    print(f"Loading hex data...")
    hex_gdf = load_hex_data()
    print(f"Loaded {len(hex_gdf)} hexes")
    
    results = []
    
    print(f"\nProcessing {len(coordinates)} coordinates with {radius_km}km radius...")
    for i, (lat, lon, name) in enumerate(coordinates):
        print(f"Processing {i+1}/{len(coordinates)}: {name} ({lat:.4f}, {lon:.4f})")
        
        result = find_hexes_and_population_for_coordinate(lat, lon, radius_km, hex_gdf, resolution)
        result['location_name'] = name
        results.append(result)
    
    return results, hex_gdf

def save_results(results, hex_gdf, radius_km, output_dir):
    """Save results to files"""
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Save summary results
    summary_df = pd.DataFrame(results)
    summary_file = output_dir / f"population_summary_{radius_km}km_radius.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"\nSaved summary to: {summary_file}")
    
    # Save detailed hex data for each location
    for result in results:
        if result['hexes_found'] > 0:
            # Get hexes for this location
            center_hex = h3.str_to_int(result['center_hex'])
            hexagons, _, _ = get_hexes_in_radius(
                result['center_lat'], 
                result['center_lon'], 
                result['radius_km']
            )
            
            # Filter hex data
            location_hexes = hex_gdf[hex_gdf['h3'].isin(hexagons)].copy()
            
            # Add distance and area
            location_hexes['distance_from_center_km'] = location_hexes.apply(
                lambda row: h3.great_circle_distance(
                    (result['center_lat'], result['center_lon']), 
                    (row['lat'], row['lon']), 
                    unit='km'
                ), 
                axis=1
            )
            location_hexes['area_km2'] = location_hexes['h3'].apply(
                lambda h: h3.cell_area(h, unit='km^2')
            )
            
            # Save to parquet
            safe_name = result['location_name'].replace(' ', '_').replace(',', '').replace('.', '')
            hex_file = output_dir / f"hexes_{safe_name}_{radius_km}km_radius.parquet"
            location_hexes.to_parquet(hex_file)
            print(f"Saved hex data for {result['location_name']}: {hex_file}")
    
    return summary_file

def main():
    """Main function with example coordinates"""
    
    # Example coordinates: (latitude, longitude, location_name)
    # You can modify this list with your actual coordinates
    coordinates = [
        (6.619526, 3.361939, "nigeria, 1")
        # Add more coordinates as needed
    ]
    
    # Parameters
    radius_km = 2   # 5 km radius
    resolution = 8  # H3 resolution
    output_dir = "radius_analysis_results"
    
    print(f"Starting population aggregation analysis...")
    print(f"Radius: {radius_km} km")
    print(f"H3 Resolution: {resolution}")
    print(f"Number of locations: {len(coordinates)}")
    
    # Process coordinates
    results, hex_gdf = process_coordinate_list(coordinates, radius_km, resolution)
    
    # Save results
    summary_file = save_results(results, hex_gdf, radius_km, output_dir)
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    summary_df = pd.DataFrame(results)
    print(summary_df[['location_name', 'hexes_found', 'total_population', 'total_area_km2']].to_string(index=False))
    
    print(f"\nTotal population across all locations: {summary_df['total_population'].sum():,}")
    print(f"Average hexes per location: {summary_df['hexes_found'].mean():.1f}")
    print(f"Results saved to: {output_dir}/")

if __name__ == "__main__":
    main()
