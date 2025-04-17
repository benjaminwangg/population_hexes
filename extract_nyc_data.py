import pandas as pd
import geopandas as gpd
import h3

# Step 1: Load coverage data (hex9s with signal)
coverage_gdf = gpd.read_parquet(r"parquet_files/ID_US_hexes.parquet")

# Step 2: Add parent hex8 ID
coverage_gdf["h3"] = coverage_gdf["h3_res9_id"].apply(lambda h: h3.h3_to_parent(h, 8))

# Step 3: Group by hex8 and average the signal
hex8_signal = (
    coverage_gdf
    .groupby("h3")["minsignal"]
    .mean()
    .reset_index()
    .rename(columns={"minsignal": "avg_minsignal"})
)

# Step 4: Load population hex8 data
pop_df = gpd.read_parquet(r"parquet_files/us_hexes_with_geonames.parquet")

# Merge on H3 index
merged = pop_df.merge(hex8_signal, on="h3", how="inner")

# Step 5: Sort by worst signal first
worst_hexes = merged.sort_values(by="avg_minsignal").copy()

# Step 6: Print results (worst signal hexes only — no limit unless you add one)
print("📉 Hexes with the worst average signal (dBm):\n")
# Step 7: Print the 10 hexes with the worst average min signal
worst_10 = worst_hexes.nsmallest(10, "avg_minsignal")

print("\n🚨 Worst 10 Signal Hexes:")
print(
    worst_10[["h3", "avg_minsignal", "city", "county", "state"]]
    .to_string(index=False)
)
