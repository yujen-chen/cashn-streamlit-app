# California State Highway Extractor

   A Streamlit application for extracting and visualizing California State Highway segments based on postmile values.

## Features

- Select highway segments by District, County, Route, and Direction
- Display highway segments on an interactive map
- View postmile points and line data
- Extract specific segments based on postmile values

## Development Setup (uv)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and ensure version 0.1.18 or newer is available.
2. Install the pinned Python runtime and project dependencies:

   ```bash
   uv python install 3.11.8
   uv sync
   ```

   `uv sync` creates a local virtual environment (default `.venv`) and installs packages declared in `pyproject.toml`.
3. Launch the Streamlit app through uv:

   ```bash
   uv run streamlit run app.py
   ```

Use `uv run` for additional commands (e.g., `uv run python -m black src app.py`) to guarantee the correct interpreter and dependencies.
