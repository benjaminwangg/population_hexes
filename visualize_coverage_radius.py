import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from shapely.geometry import Point
import pyarrow.parquet as pq
import pandas as pd

# ========== LOAD DATA ==========
@st.cache_data
def load_data():
    # Read only necessary columns from parquet
    columns = ['h3', 'population', 'density_per_mi2', 'city', 'county', 'state', 'centroid', 'geometry']
    gdf = gpd.read_parquet(r"parquet_files\us_hexes_with_geonames.parquet", columns=columns)
    gdf = gdf.set_crs("EPSG:4326")
    return gdf

gdf = load_data()

# ========== SIDEBAR FILTERS ==========
st.sidebar.title("🔍 Filter Parameters")

# Density range
min_density, max_density = st.sidebar.slider(
    "Population Density (people per sq. mile)",
    min_value=0,
    max_value=int(gdf["density_per_mi2"].max()),
    value=(0, 10000),
    step=100
)

# State filter
states = sorted(gdf["state"].dropna().unique())
state = st.sidebar.selectbox("State", options=["All"] + states)

# County filter
county = st.sidebar.text_input("County (optional)")

# City filter
city = st.sidebar.text_input("City (optional)")

# Radius Filter
st.sidebar.markdown("---")
st.sidebar.subheader("📍 Landmark Radius Filter")
use_radius_filter = st.sidebar.checkbox("Enable Radius Filter")

lat = st.sidebar.number_input("Latitude", value=40.7128, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=-74.0060, format="%.6f")
radius_km = st.sidebar.slider("Radius (km)", min_value=0.1, max_value=20.0, value=1.2, step=0.1)

# Search trigger
search = st.sidebar.button("Apply Filters")

# ========== FILTER LOGIC ==========
if search:
    filtered = gdf.copy()

    # Apply standard filters
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

    # Apply radius filter if enabled
    if use_radius_filter:
        # Create the landmark point and project to EPSG:3857
        landmark = Point(lon, lat)
        landmark_metric = gpd.GeoSeries([landmark], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]

        # Project centroids to metric CRS
        centroids_metric = gpd.GeoSeries(filtered["centroid"], crs="EPSG:4326").to_crs(epsg=3857)

        # Compute distance from each centroid to the landmark
        distances = centroids_metric.distance(landmark_metric)
        
        # Add distance column to filtered GeoDataFrame
        filtered["distance_km"] = distances / 1000  # Convert meters to kilometers

        # Calculate intersection area for partial hexes
        def calculate_intersection_area(row):
            hex_metric = gpd.GeoSeries([row.geometry], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
            circle = landmark_metric.buffer(radius_km * 1000)  # Create circle in meters
            intersection = hex_metric.intersection(circle)
            if intersection.is_empty:
                return 0
            return intersection.area / hex_metric.area  # Ratio of intersection area to total hex area

        # Calculate intersection ratios
        filtered["intersection_ratio"] = filtered.apply(calculate_intersection_area, axis=1)
        
        # Adjust population based on intersection ratio
        filtered["adjusted_population"] = filtered["population"] * filtered["intersection_ratio"]
        
        # Filter hexes that have any intersection with the circle
        filtered = filtered[filtered["intersection_ratio"] > 0]

        # Sort by distance for better visualization
        filtered = filtered.sort_values("distance_km")

    st.subheader(f"✅ {len(filtered)} matching hexes")
    if use_radius_filter:
        total_pop = filtered["adjusted_population"].sum()
    else:
        total_pop = filtered["population"].sum()
    st.markdown(f"**Total Population in these hexes:** {total_pop:,.0f}")

    # Show Folium map
    if not filtered.empty:
        # Prepare tooltip columns
        tooltip_cols = ["population", "density_per_mi2", "city", "county", "state"]
        if use_radius_filter:
            tooltip_cols.extend(["distance_km", "intersection_ratio", "adjusted_population"])
        
        m = filtered.explore(
            column="density_per_mi2",
            cmap="YlOrRd",
            tooltip=tooltip_cols,
            popup=True,
            tiles="CartoDB positron",
            style_kwds={"weight": 0.1, "fillOpacity": 0.6},
            name="Population Density"
        )

        # Add landmark radius circle if used
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
        st.dataframe(filtered[["h3", "population", "adjusted_population", "density_per_mi2", "city", "county", "state", "distance_km", "intersection_ratio"]])
    else:
        st.dataframe(filtered[["h3", "population", "density_per_mi2", "city", "county", "state"]])
else:
    st.info("Use the filters in the sidebar and click 'Apply Filters' to get results.")
