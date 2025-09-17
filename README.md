# California State Highway Extractor

A Streamlit web application for extracting and visualizing California State Highway segments based on postmile values. This application allows users to interactively select highway segments by district, county, route, and direction, then extract specific portions based on postmile ranges.

## Features

- **Interactive Selection**: Choose highway segments by District, County, Route, and Direction
- **Postmile-based Extraction**: Extract specific highway segments using start and end postmile values
- **Interactive Mapping**: Display highway segments and postmile points on an interactive map using Plotly
- **Data Export**: Download extracted segments in GeoJSON format
- **Real-time Visualization**: Immediate visual feedback of selected segments on the map

## Project Structure

```
cashn-streamlit-app/
├── app.py                     # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── PostmileSegmentExtractor.py  # Core logic for highway segment extraction
│   └── MapPlotter.py                 # Map visualization functionality
├── data/                      # Highway data (line and point GeoJSON files)
│   ├── line/                   # Highway line segments by district/county
│   └── point/                  # Postmile points by district/county
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── pyproject.toml             # Project dependencies and configuration
└── README.md                  # This file
```

## Data Structure

Highway data is organized hierarchically:

- **Line Data**: `data/line/d{district}/{county}_route_{route}_{direction}.geojson`
- **Point Data**: `data/point/d{district}/{county}_pm_{route}_{direction}.geojson`
- **Output**: Extracted segments are saved to `data/splitted/`

## Development Setup

### Prerequisites

- Python 3.11
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)

### Installation

1. Install uv (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Install the pinned Python runtime and project dependencies:

   ```bash
   uv python install 3.11.8
   uv sync
   ```

   This creates a local virtual environment (`.venv/`) and installs all dependencies from `pyproject.toml`.
3. Launch the Streamlit application:

   ```bash
   uv run streamlit run app.py
   ```

### Running Commands

Use `uv run` to execute commands with the correct Python interpreter and dependencies:

```bash
uv run python --version
uv run streamlit run app.py --server.port 8501
```

## Core Components

### PostmileSegmentExtractor

Handles the extraction logic:

- Reads highway data for specified districts, counties, routes, and directions
- Cuts line segments based on start and end postmile values
- Processes both continuous and non-continuous segments
- Returns extracted line segments and postmile points

### MapPlotter

Provides visualization capabilities:

- Creates interactive maps using Plotly
- Supports visualization of both line and point data
- Automatically calculates appropriate zoom levels and center points
- Handles CRS conversion (to EPSG:4326 for web mapping)

## Dependencies

- **streamlit**: Web application framework
- **geopandas**: Geospatial data processing
- **shapely**: Geometric operations
- **plotly**: Interactive mapping
- **pandas**: Data manipulation
- **numpy**: Numerical computations
- **matplotlib**: Additional plotting capabilities

## Deployment

### Streamlit Community Cloud

The easiest way to deploy this application is through Streamlit Community Cloud:

1. **Push to GitHub**: Ensure your code is pushed to a GitHub repository
2. **Connect to Streamlit Cloud**:

   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository and branch
   - Set main file path to `app.py`
   - Click "Deploy"
3. **Configuration**:

   - Python version: 3.11
   - No additional environment variables required
   - The app will automatically install dependencies from `pyproject.toml`

### Local Development

For local development, use the provided uv workflow:

```bash
# Install dependencies
uv sync

# Run the application
uv run streamlit run app.py

# Run tests or other commands
uv run python <script>.py
```

## Architecture Notes

1. **Data Loading**: The application scans the `data` directory on startup to build the hierarchical structure of available options
2. **Segment Cutting**: Uses Shapely geometric operations to handle complex line segment cutting, including MultiLineString support
3. **Error Handling**: Includes comprehensive exception handling with user-friendly error messages
4. **Performance Optimization**: Utilizes GeoPandas for efficient spatial data processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly using `uv run streamlit run app.py`
5. Submit a pull request

## License

This project is for educational and research purposes. Please ensure compliance with California State Highway data usage terms and conditions.
