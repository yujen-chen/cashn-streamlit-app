import streamlit as st
import geopandas as gpd
from pathlib import Path
import folium
from streamlit_folium import st_folium
from src.PostmileSegmentExtractor import PostmileSegmentExtractor
from src.MapPlotter import MapPlotter

# 設定頁面配置
st.set_page_config(
    page_title="California State Highway Extractor", page_icon="🛣️", layout="wide"
)

# 設定標題
st.title("California State Highway Extractor 🛣️")
st.markdown("---")


def get_available_data():
    """
    從資料目錄中獲取可用的資料選項，並建立層級關係
    """
    data_path = Path("data")
    line_path = data_path / "line"

    # 建立層級關係的字典
    hierarchy = {}  # district -> county -> route -> direction

    # 檢查目錄是否存在
    if not line_path.exists():
        st.error(f"Directory not found: {line_path}")
        return {}, [], [], [], []

    # 遍歷 line 目錄下的所有檔案
    for district_dir in line_path.glob("d*"):
        district = district_dir.name.replace("d", "")
        hierarchy[district] = {}

        # 檢查是否有 geojson 檔案
        for file in district_dir.glob("*.geojson"):
            try:
                filename = file.stem
                if "_route_" in filename:
                    parts = filename.split("_")
                    if len(parts) >= 4:
                        county = parts[0]
                        route = parts[2]
                        direction = parts[3]

                        # 檢查對應的 point 檔案是否存在
                        point_file = (
                            data_path
                            / "point"
                            / f"d{district}"
                            / f"{county}_pm_{route}_{direction}.geojson"
                        )

                        if file.exists() and point_file.exists():
                            # 建立層級關係
                            if county not in hierarchy[district]:
                                hierarchy[district][county] = {}
                            if route not in hierarchy[district][county]:
                                hierarchy[district][county][route] = []
                            if direction not in hierarchy[district][county][route]:
                                hierarchy[district][county][route].append(direction)

            except Exception as e:
                st.warning(f"Error processing file {file.name}: {str(e)}")
                continue

    # 如果沒有找到任何有效的組合，提供預設值
    if not hierarchy:
        st.warning("No valid data files found. Using default values.")
        return {}, ["1"], ["DN"], ["101"], ["NB"]

    # 獲取所有可用的選項（用於初始化）
    districts = sorted(hierarchy.keys())

    return hierarchy, districts, [], [], []


# side bar
with st.sidebar:
    st.header("Select Route")

    # 獲取可用的資料選項和層級關係
    hierarchy, districts, _, _, _ = get_available_data()

    # District 選擇
    districts = sorted(districts, key=lambda x: int(x))
    district = st.selectbox("District", options=districts, help="Select District")

    # County 選擇（基於選擇的 District）
    counties = sorted(hierarchy.get(district, {}).keys()) if district else []
    county = st.selectbox("County", options=counties, help="Select County")

    # Route 選擇（基於選擇的 County）

    routes = (
        sorted(hierarchy.get(district, {}).get(county, {}).keys()) if county else []
    )
    routes = sorted(routes, key=lambda x: int(x))
    route = st.selectbox("Route", options=routes, help="Select Route")

    # Direction 選擇（基於選擇的 Route）
    directions = (
        sorted(hierarchy.get(district, {}).get(county, {}).get(route, []))
        if route
        else []
    )
    direction = st.selectbox("Direction", options=directions, help="Select Direction")

    # 顯示選擇的組合是否有效
    if district and county and route and direction:
        if direction in hierarchy.get(district, {}).get(county, {}).get(route, []):
            st.success("Valid combination selected!")
        else:
            st.error("Invalid combination selected!")

# 主要內容區域
try:
    # 建立提取器實例
    with st.spinner("Loading..."):
        extractor = PostmileSegmentExtractor(
            district=district,
            county=county,
            route=route,
            direction=direction,
            dataPath="data",
        )

        # 顯示資料基本資訊
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

    st.subheader("Route Map")

    # plot the map
    map_plotter = MapPlotter(
        lineGeoJSONPath=extractor.lineFilePath, pointGeoJSONPath=extractor.pointFilePath
    )
    try:
        m = map_plotter.plotting_map(
            lineGdf=map_plotter.lineGdf, pointGdf=map_plotter.pointGdf
        )

        # 在 Streamlit 中顯示地圖
        st_folium(m, width=960, height=720)

        # 添加資料表格顯示選項
        if st.checkbox("Show Data Table"):
            tab1, tab2 = st.tabs(["Line Data", "Point Data"])

            with tab1:
                st.subheader("Line Data")
                st.dataframe(
                    map_plotter.lineGdf.drop(columns=["geometry"]), hide_index=True
                )

            with tab2:
                st.subheader("Point Data")
                st.dataframe(
                    map_plotter.pointGdf[["PM", "County", "Route", "Direction"]],
                    hide_index=True,
                )

    except Exception as e:
        st.error(f"Error plotting map: {str(e)}")

except Exception as e:
    st.error(f"載入資料時發生錯誤：{str(e)}")
    st.info("請確認選擇的參數是否正確")
