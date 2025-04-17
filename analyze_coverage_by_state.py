import geopandas as gpd
import os
import glob
import time
import h3

def analyze_state_coverage(hex_file, pop_df):
    try:
        # Load the state hex file
        coverage_gdf = gpd.read_parquet(hex_file)
        
        # Get state code from filename
        state = os.path.basename(hex_file).split('_')[0]
        
        # Add parent hex8 ID
        coverage_gdf["h3"] = coverage_gdf["h3_res9_id"].apply(lambda h: h3.h3_to_parent(h, 8))
        
        # Group by hex8 and average the signal
        hex8_signal = (
            coverage_gdf
            .groupby("h3")["minsignal"]
            .mean()
            .reset_index()
            .rename(columns={"minsignal": "minsignal"})
        )
        
        # Merge with population data
        merged = pop_df.merge(hex8_signal, on="h3", how="inner")
        
        # Calculate population in different signal ranges
        great_coverage = merged[merged['minsignal'] >= -90]['population'].sum()
        good_coverage = merged[(merged['minsignal'] > -100) & (merged['minsignal'] < -90)]['population'].sum()
        poor_coverage = merged[merged['minsignal'] <= -100]['population'].sum()
        total_population = merged['population'].sum()
        
        # Print results
        print(f"\n📊 {state} Coverage Analysis:")
        print(f"Total Population: {total_population:,.0f}")
        print(f"Great Coverage (≥ -90 dBm): {great_coverage:,.0f} ({great_coverage/total_population*100:.1f}%)")
        print(f"Good Coverage (-100 < x < -90 dBm): {good_coverage:,.0f} ({good_coverage/total_population*100:.1f}%)")
        print(f"Poor Coverage (≤ -100 dBm): {poor_coverage:,.0f} ({poor_coverage/total_population*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error processing {hex_file}: {e}")

def main():
    # Load population data once
    print("Loading population data...")
    pop_df = gpd.read_parquet("parquet_files/us_hexes_with_geonames.parquet")
    
    # Find all state hex files
    hex_files = glob.glob("parquet_files/*_US_hexes.parquet")
    
    # Process each state file
    for hex_file in hex_files:
        start_time = time.time()
        analyze_state_coverage(hex_file, pop_df)
        print(f"⏱️ Processing time: {time.time() - start_time:.2f} seconds")
        print("-" * 50)

if __name__ == "__main__":
    main() 