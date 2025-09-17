import streamlit as st
from pathlib import Path
import zipfile
import tempfile
from src.PostmileSegmentExtractor import PostmileSegmentExtractor
from src.MapPlotter import plotting_map


output_path = "data"

if "split_confirmed" not in st.session_state:
    st.session_state["split_confirmed"] = False
if "confirmed_params" not in st.session_state:
    st.session_state["confirmed_params"] = None
if "pending_changes" not in st.session_state:
    st.session_state["pending_changes"] = False

# Page Config
st.set_page_config(
    page_title="Caltrans D12 Route Extractor", page_icon="🛣️", layout="wide"
)

# Title
st.title("Caltrans D12 Route Extractor 🛣️")
st.markdown("---")


def get_available_data():
    """
    Obtain available data options from the data directory and establish hierarchical relationships.
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

    districts = sorted(districts, key=lambda x: int(x))
    default_district = districts[0] if districts else ""
    district = st.selectbox(
        "District", options=districts, index=0, help="Select District"
    )

    counties = sorted(hierarchy.get(district or default_district, {}).keys())
    default_county = counties[0] if counties else ""
    county = st.selectbox(
        "County",
        options=counties,
        index=0 if counties else None,
        help="Select County",
    )

    routes = sorted(
        hierarchy.get(district, {}).get(county or default_county, {}).keys()
    )
    routes = sorted(routes, key=lambda x: int(x)) if routes else []
    route = st.selectbox(
        "Route",
        options=routes,
        index=0 if routes else None,
        help="Select Route",
    )

    directions = sorted(
        hierarchy.get(district, {}).get(county, {}).get(route, []) if route else []
    )
    direction = st.selectbox(
        "Direction",
        options=directions,
        index=0 if directions else None,
        help="Select Direction",
    )

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
            start_pm, end_pm = end_pm, start_pm

        btn_col1, btn_col2 = st.sidebar.columns(2)
        with btn_col1:
            confirm_clicked = st.button("Confirm Split", type="primary")
        with btn_col2:
            reset_clicked = st.button("Reset Selection")

        if confirm_clicked:
            st.session_state["confirmed_params"] = {
                "district": district,
                "county": county,
                "route": route,
                "direction": direction,
                "start_pm": float(start_pm),
                "end_pm": float(end_pm),
            }
            st.session_state["split_confirmed"] = True
            st.session_state["pending_changes"] = False
            st.sidebar.success("Split range confirmed.")

        if reset_clicked:
            st.session_state["split_confirmed"] = False
            st.session_state["confirmed_params"] = None
            st.session_state["pending_changes"] = False
            st.session_state.pop("Start pm", None)
            st.session_state.pop("End pm", None)
            st.sidebar.warning("Selection has been reset. Confirm again to proceed.")

    except Exception as e:
        st.sidebar.info("Please choose pm")
        start_pm, end_pm = 0, 0
        confirm_clicked = False
        reset_clicked = False

confirmed_params = st.session_state.get("confirmed_params")

if confirmed_params:
    selection_changed = any(
        [
            confirmed_params.get("district") != district,
            confirmed_params.get("county") != county,
            confirmed_params.get("route") != route,
            confirmed_params.get("direction") != direction,
            confirmed_params.get("start_pm") != float(start_pm),
            confirmed_params.get("end_pm") != float(end_pm),
        ]
    )
    if selection_changed:
        st.session_state["split_confirmed"] = False
        st.session_state["pending_changes"] = True
    else:
        st.session_state["pending_changes"] = False
else:
    st.session_state["split_confirmed"] = False

if st.session_state.get("pending_changes") and not st.session_state.get(
    "split_confirmed"
):
    st.sidebar.info("Selections were modified. Please confirm to apply the new range.")


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

    show_results = st.session_state.get("split_confirmed") and st.session_state.get(
        "confirmed_params"
    )

    if show_results:
        params = st.session_state["confirmed_params"]
        start_pm_confirmed = params["start_pm"]
        end_pm_confirmed = params["end_pm"]

        # Extract the segment based on confirmed start_pm and end_pm
        splitted_result_gdf, splitted_point_gdf = extractor.cut_line_by_points(
            start_pm=start_pm_confirmed, end_pm=end_pm_confirmed
        )

        st.caption(
            f"Displaying confirmed range: PM {start_pm_confirmed:.1f} – {end_pm_confirmed:.1f}"
        )

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("Split Line Segment Data")
            st.dataframe(
                splitted_result_gdf.drop(columns=["geometry"]), hide_index=True
            )

            def save_and_get_line_data():
                return splitted_result_gdf.to_json().encode("utf-8")

            st.download_button(
                label="Download Splitted Line (GeoJSON)",
                data=save_and_get_line_data(),
                file_name=(
                    f"splitted_d{district}_{county}_{route}_{direction}_{start_pm_confirmed:.1f}_{end_pm_confirmed:.1f}.geojson"
                ),
                mime="application/json",
                help="Download Splitted Line in GeoJSON Format",
            )

            def create_shapefile_zip():
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)

                    # Create shapefile name
                    shapefile_name = f"splitted_d{district}_{county}_{route}_{direction}_{start_pm_confirmed:.1f}_{end_pm_confirmed:.1f}"
                    shapefile_path = temp_path / f"{shapefile_name}.shp"

                    # Save line shapefile
                    splitted_result_gdf.to_file(shapefile_path, driver="ESRI Shapefile")

                    # Create zip file
                    zip_path = temp_path / f"{shapefile_name}.zip"
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for file in temp_path.iterdir():
                            if file.is_file() and file.suffix != ".zip":
                                zipf.write(file, file.name)

                    # Read zip file content
                    with open(zip_path, "rb") as f:
                        return f.read()

            st.download_button(
                label="Download Splitted Line (Shapefile ZIP)",
                data=create_shapefile_zip(),
                file_name=(
                    f"splitted_d{district}_{county}_{route}_{direction}_{start_pm_confirmed:.1f}_{end_pm_confirmed:.1f}.zip"
                ),
                mime="application/zip",
                help="Download Splitted Line as Zipped Shapefile",
            )

        with col4:
            st.subheader("Split Point Data")
            st.dataframe(
                splitted_point_gdf[["PM", "County", "Route", "Direction"]],
                hide_index=True,
            )

            def save_and_get_point_data():
                return splitted_point_gdf.to_json().encode("utf-8")

            st.download_button(
                label="Download Splitted Point (GeoJSON)",
                data=save_and_get_point_data(),
                file_name=(
                    f"splitted_pm_d{district}_{county}_{route}_{direction}_{start_pm_confirmed:.1f}_{end_pm_confirmed:.1f}.geojson"
                ),
                mime="application/json",
                help="Download Splitted Point in GeoJSON Format",
            )

            def create_point_shapefile_zip():
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)

                    # Create shapefile name
                    shapefile_name = f"splitted_pm_d{district}_{county}_{route}_{direction}_{start_pm_confirmed:.1f}_{end_pm_confirmed:.1f}"
                    shapefile_path = temp_path / f"{shapefile_name}.shp"

                    # Save point shapefile
                    splitted_point_gdf.to_file(shapefile_path, driver="ESRI Shapefile")

                    # Create zip file
                    zip_path = temp_path / f"{shapefile_name}.zip"
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for file in temp_path.iterdir():
                            if file.is_file() and file.suffix != ".zip":
                                zipf.write(file, file.name)

                    # Read zip file content
                    with open(zip_path, "rb") as f:
                        return f.read()

            st.download_button(
                label="Download Splitted Point (Shapefile ZIP)",
                data=create_point_shapefile_zip(),
                file_name=(
                    f"splitted_pm_d{district}_{county}_{route}_{direction}_{start_pm_confirmed:.1f}_{end_pm_confirmed:.1f}.zip"
                ),
                mime="application/zip",
                help="Download Splitted Point as Zipped Shapefile",
            )

        st.subheader("Route Map")

        try:
            map_fig = plotting_map(
                lineGdf=splitted_result_gdf, pointGdf=splitted_point_gdf
            )

            st.plotly_chart(
                map_fig, use_container_width=False, config={"scrollZoom": True}
            )

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
    else:
        st.info("Confirm the split range to generate preview and downloads.")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
