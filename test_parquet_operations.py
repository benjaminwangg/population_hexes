import geopandas as gpd
import time

# Start timer
start = time.time()
id = '882a107289fffff'
# Path to your file
parquet_path = r"all_pa_hexes_with_signal.parquet"

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
    # total_pop = gdf["population"].sum()

    # print(f"📊 Total population in high-density areas with weak signal (≤ -90 dBm): {total_pop}")
    
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