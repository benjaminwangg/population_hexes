import pandas as pd
import geopandas as gpd
import h3

# Step 1: Load coverage data (hex9s with signal)
coverage_gdf = gpd.read_parquet(r"parquet_files/PA_US_hexes.parquet")

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

# Step 4: Load population data (must already be by hex8)
pop_df = gpd.read_parquet(r"parquet_files/us_hexes_with_geonames.parquet")  # or gpd.read_file(...) if it's spatial

# Ensure correct H3 ID column names
# Should contain: ["h3_res8_id", "population", "density"]

# Step 5: Merge population and signal info
merged = pop_df.merge(hex8_signal, on="h3", how="inner")

# Step 6: Save all merged hexes to parquet file
# Step 6: Filter for high-density + bad signal
# target_areas = merged[
#     (merged["avg_minsignal"] <= -100)
# ]
merged.to_parquet("all_pa_hexes_with_signal.parquet")

print(f"📊 Total population in all areas: {merged['population'].sum()}")
