import geopandas as gpd
import time

# Start timer
start = time.time()
id = '882a107289fffff'
# Path to your file
parquet_path = r"parquet_files\ng_hexes.parquet"

try:
    # Load the Parquet file
    gdf = gpd.read_parquet(parquet_path)

    # Stop timer
    end = time.time()

    # Print results
    print(f"✅ Loaded {len(gdf)} hexes in {round(end - start, 2)} seconds")
    print("📦 Columns:", gdf.columns.tolist())
    print("🧭 CRS:", gdf.crs)
    print("🔍 First few rows:\n", gdf.head())
    
    # Calculate and print total population
    if 'population' in gdf.columns:
        total_pop = gdf["population"].sum()
        print(f"👥 Total population: {total_pop:,}")
    else:
        print("❌ 'population' column not found in the data")
    
    # Find and print rows with lowest minsignal
    if 'avg_minsignal' in gdf.columns:
        min_signal = gdf['avg_minsignal'].min()
        lowest_signal_rows = gdf[gdf['avg_minsignal'] == min_signal]
        print(f"\n📡 Rows with lowest minsignal ({min_signal}):")
        print(lowest_signal_rows)
    else:
        print("\n❌ 'minsignal' column not found in the data")
except Exception as e:
    print("❌ Failed to load the Parquet file:", e)

print(gdf.head())