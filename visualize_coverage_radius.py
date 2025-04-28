import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import pandas as pd
import h3
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point

# ========== LOAD DATA ==========
@st.cache_data
def load_data():
    columns = ['h3', 'population', 'density_per_mi2', 'city', 'county', 'state', 'geometry']
    gdf = gpd.read_parquet(r"parquet_files/us_hexes_with_geonames.parquet", columns=columns)
    gdf = gdf.set_crs("EPSG:4326")
    return gdf

gdf = load_data()

# ========== SIDEBAR FILTERS ==========
st.sidebar.title("🔍 Filter Parameters")

min_density, max_density = st.sidebar.slider(
    "Population Density (people per sq. mile)",
    min_value=0,
    max_value=int(gdf["density_per_mi2"].max()),
    value=(0, 10000),
    step=100
)

states = sorted(gdf["state"].dropna().unique())
state = st.sidebar.selectbox("State", options=["All"] + states)
county = st.sidebar.text_input("County (optional)")
city = st.sidebar.text_input("City (optional)")

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Landmark Radius Filter")
use_radius_filter = st.sidebar.checkbox("Enable Radius Filter")

lat = st.sidebar.number_input("Latitude", value=40.7128, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=-74.0060, format="%.6f")
radius_km = st.sidebar.slider("Radius (km)", min_value=0.1, max_value=20.0, value=1.2, step=0.1)

search = st.sidebar.button("Apply Filters")

# ========== FILTER LOGIC ==========
if search:
    filtered = gdf.copy()

    # Standard filters
    filtered = filtered[
        (filtered["density_per_mi2"] >= min_density) &
        (filtered["density_per_mi2"] <= max_density)
    ]

    if state != "All":
        filtered = filtered[filtered["state"] == state]

    if county:
        filtered = filtered[filtered["county"].str.contains(county, case=False, na=False)]

    if city:
        filtered = filtered[filtered["city"].str.contains(city, case=False, na=False)]

    if use_radius_filter:
        # Step 1: Get center H3 hex at res 8
        center_hex = h3.latlng_to_cell(lat, lon, 8)

        # Step 2: Approximate number of rings
        k = int(np.ceil(radius_km / 0.9204))

        # Step 3: Get all hexes within k rings
        nearby_hexes = set(h3.grid_disk(center_hex, k))

        # Step 4: Compute grid distance for each hex
        hexes_with_distance = {hex_id: h3.grid_distance(center_hex, hex_id) for hex_id in nearby_hexes}

        # Step 5: Filter hexes based on H3 ID match
        filtered = filtered[filtered["h3"].isin(nearby_hexes)].copy()

        # Step 6: Attach distance to center
        filtered["grid_distance"] = filtered["h3"].map(hexes_with_distance)

        # Step 7: (Optional) Remove hexes that fall *just outside* the radius
        # For extra precision: check lat/lon great-circle distance (later if needed)

    st.subheader(f"✅ {len(filtered)} matching hexes")

    if use_radius_filter:
        total_pop = filtered["population"].sum()
    else:
        total_pop = filtered["population"].sum()

    st.markdown(f"**Total Population in these hexes:** {total_pop:,.0f}")

    # Show Folium map
    if not filtered.empty:
        tooltip_cols = ["population", "density_per_mi2", "city", "county", "state"]
        if use_radius_filter:
            tooltip_cols.append("grid_distance")

        m = filtered.explore(
            column="density_per_mi2",
            cmap="YlOrRd",
            tooltip=tooltip_cols,
            popup=True,
            tiles="CartoDB positron",
            style_kwds={"weight": 0.1, "fillOpacity": 0.6},
            name="Population Density"
        )

        if use_radius_filter:
            folium.Circle(
                location=[lat, lon],
                radius=radius_km * 1000,
                color="blue",
                fill=True,
                fill_opacity=0.2,
                popup="Landmark Radius"
            ).add_to(m)

        folium.LayerControl().add_to(m)
        folium_static(m, height=600)

    # Show table
    if use_radius_filter:
        st.dataframe(filtered[["h3", "population", "density_per_mi2", "city", "county", "state", "grid_distance"]])
    else:
        st.dataframe(filtered[["h3", "population", "density_per_mi2", "city", "county", "state"]])

else:
    st.info("Use the filters in the sidebar and click 'Apply Filters' to get results.")

