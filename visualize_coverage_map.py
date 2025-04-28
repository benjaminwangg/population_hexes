import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import folium_static

# ========== LOAD DATA ==========
@st.cache_data
def load_data():
    gdf = gpd.read_parquet(r"location_hexes\yonkers.parquet")
    gdf = gdf.set_crs("EPSG:4326")
    gdf["density_per_mi2"] = gdf["population"] / 0.2857156
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

# Signal strength filter
min_signal, max_signal = st.sidebar.slider(
    "Average Min Signal Strength (dBm)",
    min_value=-120,
    max_value=-50,
    value=(-100, -80),
    step=1
)


# State filter
states = sorted(gdf["state"].dropna().unique())
state = st.sidebar.selectbox("State", options=["All"] + states)

# County filter
county = st.sidebar.text_input("County (optional)")

# City filter
city = st.sidebar.text_input("City (optional)")

# Search trigger
search = st.sidebar.button("Apply Filters")

# ========== FILTER LOGIC ==========
filtered = gdf.copy()

if search:
    filtered = filtered[
        (filtered["density_per_mi2"] >= min_density) &
        (filtered["density_per_mi2"] <= max_density) 
        &
        (filtered["avg_minsignal"] >= min_signal) &
        (filtered["avg_minsignal"] <= max_signal)
    ]

    if state != "All":
        filtered = filtered[filtered["state"] == state]

    if county:
        filtered = filtered[filtered["county"].str.contains(county, case=False, na=False)]

    if city:
        filtered = filtered[filtered["city"].str.contains(city, case=False, na=False)]

    st.subheader(f"✅ {len(filtered)} matching hexes")
    total_pop = filtered["population"].sum()
    st.markdown(f"**Total Population in these hexes:** {total_pop:,}")

    # Show Folium map
    if not filtered.empty:
        m = filtered.explore(
            column="density_per_mi2",
            cmap="YlOrRd",
            tooltip=["population", "density_per_mi2", "city", "county", "state"],
            popup=True,
            tiles="CartoDB positron",
            style_kwds={"weight": 0.1, "fillOpacity": 0.6},
            name="Population Density"
        )
        folium.LayerControl().add_to(m)
        folium_static(m, height=600)

    # Show table
    st.dataframe(filtered[["h3", "population", "density_per_mi2", "city", "county", "state"]])

else:
    st.info("Use the filters in the sidebar and click 'Apply Filters' to get results.")
