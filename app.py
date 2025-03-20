import streamlit as st
import geopandas as gpd
from pathlib import Path
import folium
from streamlit_folium import st_folium
from src.PostmileSegmentExtractor import PostmileSegmentExtractor
from src.MapPlotter import plotting_map

output_path = "data"

# Page Config
st.set_page_config(
    page_title="California State Highway Extractor", page_icon="🛣️", layout="wide"
)

# Title
st.title("California State Highway Extractor 🛣️")
st.markdown("---")


def get_available_data():
    """
    從資料目錄中獲取可用的資料選項，並建立層級關係
    """
    data_path = Path("data")
    line_path = data_path / "line"

    hierarchy = {}  # district -> county -> route -> direction

    if not line_path.exists():
        st.error(f"Directory not found: {line_path}")
        return {}, [], [], [], []

    for district_dir in line_path.glob("d*"):
        district = district_dir.name.replace("d", "")
        hierarchy[district] = {}

        for file in district_dir.glob("*.geojson"):
            try:
                filename = file.stem
                if "_route_" in filename:
                    parts = filename.split("_")
                    if len(parts) >= 4:
                        county = parts[0]
                        route = parts[2]
                        direction = parts[3]

                        point_file = (
                            data_path
                            / "point"
                            / f"d{district}"
                            / f"{county}_pm_{route}_{direction}.geojson"
                        )

                        if file.exists() and point_file.exists():

                            if county not in hierarchy[district]:
                                hierarchy[district][county] = {}
                            if route not in hierarchy[district][county]:
                                hierarchy[district][county][route] = []
                            if direction not in hierarchy[district][county][route]:
                                hierarchy[district][county][route].append(direction)

            except Exception as e:
                st.warning(f"Error processing file {file.name}: {str(e)}")
                continue

    if not hierarchy:
        st.warning("No valid data files found. Using default values.")
        return {}, ["12"], ["ORA"], ["5"], ["NB"]

    districts = sorted(hierarchy.keys())

    return hierarchy, districts, [], [], []


# side bar
with st.sidebar:
    st.header("Select Route")

    hierarchy, districts, _, _, _ = get_available_data()

    # District
    districts = sorted(districts, key=lambda x: int(x))
    district = st.selectbox("District", options=districts, help="Select District")

    # County
    counties = sorted(hierarchy.get(district, {}).keys()) if district else []
    county = st.selectbox("County", options=counties, help="Select County")

    # Route

    routes = (
        sorted(hierarchy.get(district, {}).get(county, {}).keys()) if county else []
    )
    routes = sorted(routes, key=lambda x: int(x))
    route = st.selectbox("Route", options=routes, help="Select Route")

    # Direction
    directions = (
        sorted(hierarchy.get(district, {}).get(county, {}).get(route, []))
        if route
        else []
    )
    direction = st.selectbox("Direction", options=directions, help="Select Direction")

    # verify the selection
    if district and county and route and direction:
        if direction in hierarchy.get(district, {}).get(county, {}).get(route, []):
            st.success("Valid combination selected!")
        else:
            st.error("Invalid combination selected!")

    st.header("Select Segments")
    try:
        temp_extractor = PostmileSegmentExtractor(
            district=district,
            county=county,
            route=route,
            direction=direction,
            dataPath="data",
        )

        min_pm = temp_extractor.SHNPointGdf["PM"].min()
        max_pm = temp_extractor.SHNPointGdf["PM"].max()

        col1, col2 = st.sidebar.columns(2)

        with col1:
            start_pm = st.number_input(
                "Start pm",
                min_value=float(min_pm),
                max_value=float(max_pm),
                value=float(min_pm),
                step=0.1,
                format="%.1f",
                help="Select the start pm",
            )
        with col2:
            end_pm = st.number_input(
                "End pm",
                min_value=float(min_pm),
                max_value=float(max_pm),
                value=float(max_pm),
                step=0.1,
                format="%.1f",
                help="Select the end pm",
            )
        if start_pm > end_pm:
            st.sidebar.warning("Start pm cannot be greater than end pm")
            start_pm_pm, end_pm = end_pm, start_pm

    except Exception as e:
        st.sidebar.info("Please choose pm")
        start_pm, end_pm = 0, 0


# Main Area
try:

    with st.spinner("Loading..."):
        extractor = PostmileSegmentExtractor(
            district=district,
            county=county,
            route=route,
            direction=direction,
            dataPath="data",
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Route Info:")
            st.write(f"- District: {district}")
            st.write(f"- County: {county}")
            st.write(f"- Route: {route}")
            st.write(f"- Direction: {direction}")

        with col2:
            st.subheader("Postmile Range")
            min_pm = extractor.SHNPointGdf["PM"].min()
            max_pm = extractor.SHNPointGdf["PM"].max()
            st.write(f"- Start PM: {min_pm:.1f}")
            st.write(f"- End PM: {max_pm:.1f}")

    st.subheader("Extract Route")
    # Extract the segment based on selected start_pm and end_pm
    splitted_result_gdf, splitted_point_gdf = extractor.cut_line_by_points(
        start_pm=start_pm, end_pm=end_pm
    )
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Split Line Segment Data")
        st.dataframe(splitted_result_gdf.drop(columns=["geometry"]), hide_index=True)

        def save_and_get_line_data():
            line_filename = f"splitted_d{district}_{county}_{route}_{direction}_{start_pm:.1f}_{end_pm:.1f}.geojson"
            splitted_line_path = Path(output_path) / "splitted" / line_filename
            splitted_line_path.parent.mkdir(parents=True, exist_ok=True)
            splitted_result_gdf.to_file(splitted_line_path, driver="GeoJSON")
            with open(splitted_line_path, "rb") as f:
                return f.read()

        st.download_button(
            label="Download Splitted Line (GeoJSON)",
            data=save_and_get_line_data(),
            file_name=f"splitted_d{district}_{county}_{route}_{direction}_{start_pm:.1f}_{end_pm:.1f}.geojson",
            mime="application/json",
            help="Download Splitted Line in GeoJSON Format",
        )

    with col4:
        st.subheader("Split Point Data")
        st.dataframe(
            splitted_point_gdf[["PM", "County", "Route", "Direction"]], hide_index=True
        )

        def save_and_get_point_data():
            point_filename = f"splitted_pm_d{district}_{county}_{route}_{direction}_{start_pm:.1f}_{end_pm:.1f}.geojson"
            splitted_point_path = Path(output_path) / "splitted" / point_filename
            splitted_point_path.parent.mkdir(parents=True, exist_ok=True)
            splitted_point_gdf.to_file(splitted_point_path, driver="GeoJSON")
            with open(splitted_point_path, "rb") as f:
                return f.read()

        st.download_button(
            label="Download Splitted Point (GeoJSON)",
            data=save_and_get_point_data(),
            file_name=f"splitted_pm_d{district}_{county}_{route}_{direction}_{start_pm:.1f}_{end_pm:.1f}.geojson",
            mime="application/json",
            help="Download Splitted Point in GeoJSON Format",
        )

    st.subheader("Route Map")

    try:
        m = plotting_map(lineGdf=splitted_result_gdf, pointGdf=splitted_point_gdf)

        # Streamlit map
        st_folium(m, width=960, height=720)

        if st.checkbox("Show Data Table"):
            tab1, tab2 = st.tabs(["Line Data", "Point Data"])

            with tab1:
                st.subheader("Line Data")
                st.dataframe(
                    splitted_result_gdf.drop(columns=["geometry"]), hide_index=True
                )

            with tab2:
                st.subheader("Point Data")
                st.dataframe(
                    splitted_point_gdf[["PM", "County", "Route", "Direction"]],
                    hide_index=True,
                )

    except Exception as e:
        st.error(f"Error plotting map: {str(e)}")

except Exception as e:
    st.error(f"Error loading data：{str(e)}")
