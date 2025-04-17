# Hex Population Density Visualizer

An interactive web application for visualizing population density using H3 hexagons across the United States.

## Features

- Interactive map visualization using Folium
- Population density filtering
- State, county, and city filtering
- Radius-based filtering with partial hex support
- Real-time population calculations

## Setup

1. Clone the repository:
```bash
git clone [your-repo-url]
cd [your-repo-name]
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the data:
   - The application requires a parquet file containing US hex data
   - Place the parquet file in the `parquet_files` directory
   - Contact the repository maintainer for access to the data file

## Running the Application

```bash
streamlit run streamlit_map_radius.py
```

## Data Requirements

The application requires a parquet file with the following columns:
- h3: Hex identifier
- population: Population count
- density_per_mi2: Population density per square mile
- city: City name
- county: County name
- state: State name
- centroid: Centroid coordinates
- geometry: Hex geometry

## Notes

- Large data files are not included in the repository
- Contact the repository maintainer for access to the data files
- The application is optimized for performance with large datasets 