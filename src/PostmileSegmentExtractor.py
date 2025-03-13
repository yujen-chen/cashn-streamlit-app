import geopandas as gpd
from shapely.ops import split, linemerge, substring
from shapely.geometry import Point, LineString, MultiLineString
from pathlib import Path

DATA_PATH = "data"


class PostmileSegmentExtractor:
    """
    A class for extracting line segments based on start and end PM values.
    """

    def __init__(
        self,
        district,
        county,
        route,
        direction,
        dataPath=DATA_PATH,
    ):
        """
        Initialization function

        parameter:
        SHNLineGeoJSON: Separated Highway Line GeoJSON
        SHNPointGeoJSON: Separated Highway PM Point GeoJSON
        """
        self.lineFilePath = (
            Path(dataPath)
            / "line"
            / f"d{district}"
            / f"{county}_route_{route}_{direction}.geojson"
        )
        self.pointFilePath = (
            Path(dataPath)
            / "point"
            / f"d{district}"
            / f"{county}_pm_{route}_{direction}.geojson"
        )
        self.SHNLineGdf = gpd.read_file(self.lineFilePath)
        self.SHNPointGdf = gpd.read_file(self.pointFilePath)

    # works for discontinuous and continuous lines 03062025

    def cut_line_by_points(self, start_pm, end_pm, output_path=DATA_PATH):
        """
        根據起點和終點切割線段，保持不連續線段的間隔

        參數:


        返回:
        GeoDataFrame: 包含切割後線段的 GeoDataFrame
        """

        # 篩選指定 PM 範圍內的點
        points_gdf = self.SHNPointGdf[
            (self.SHNPointGdf["PM"] >= start_pm) & (self.SHNPointGdf["PM"] <= end_pm)
        ]
        # # 讀取線段和點的 GeoJSON 檔案
        # line_gdf = gpd.read_file(line_geojson)
        # points_gdf = gpd.read_file(points_geojson)

        # 確保點按照 PM 值排序
        points_gdf = points_gdf.sort_values(["PM", "Odometer"])
        start_point = points_gdf.iloc[0].geometry
        end_point = points_gdf.iloc[-1].geometry

        # 獲取線段幾何
        original_line = self.SHNLineGdf.geometry.iloc[0]

        def process_line_segment(line_segment, start_point, end_point):
            """處理單個線段"""
            coords = list(line_segment.coords)

            # 找到最接近起點和終點的位置
            start_dist = float("inf")
            end_dist = float("inf")
            start_idx = 0
            end_idx = 0
            start_proj = None
            end_proj = None

            # 遍歷每個線段找最近點
            for i in range(len(coords) - 1):
                segment = LineString([coords[i], coords[i + 1]])

                # 檢查起點
                dist_to_start = segment.distance(start_point)
                if dist_to_start < start_dist:
                    start_dist = dist_to_start
                    start_idx = i
                    start_proj = segment.interpolate(segment.project(start_point))

                # 檢查終點
                dist_to_end = segment.distance(end_point)
                if dist_to_end < end_dist:
                    end_dist = dist_to_end
                    end_idx = i
                    end_proj = segment.interpolate(segment.project(end_point))

            # 如果這個線段包含了起點或終點，返回切割後的部分
            if start_proj is not None and end_proj is not None:
                # 確保起點在終點之前
                if start_idx > end_idx:
                    start_idx, end_idx = end_idx, start_idx
                    start_proj, end_proj = end_proj, start_proj

                new_coords = []
                new_coords.append((start_proj.x, start_proj.y))
                new_coords.extend(coords[start_idx + 1 : end_idx + 1])
                new_coords.append((end_proj.x, end_proj.y))

                return LineString(new_coords)

            return None

        try:
            cut_segments = []

            # 如果是 MultiLineString，分別處理每個線段
            if isinstance(original_line, MultiLineString):
                for line_segment in original_line.geoms:
                    result = process_line_segment(line_segment, start_point, end_point)
                    if result is not None:
                        cut_segments.append(result)
            else:
                # 單一 LineString 的情況
                result = process_line_segment(original_line, start_point, end_point)
                if result is not None:
                    cut_segments.append(result)

            if not cut_segments:
                raise ValueError("未找到包含起點和終點的有效線段")

            # 創建 MultiLineString（如果有多個線段）或 LineString（如果只有一個線段）
            final_geometry = (
                MultiLineString(cut_segments)
                if len(cut_segments) > 1
                else cut_segments[0]
            )

            # 創建新的 GeoDataFrame，保持原始 CRS
            splitted_result_gdf = gpd.GeoDataFrame(
                {
                    "District": [self.SHNPointGdf.iloc[0]["District"]],
                    "County": [self.SHNPointGdf.iloc[0]["County"]],
                    "Route": [self.SHNPointGdf.iloc[0]["Route"]],
                    "Direction": [self.SHNPointGdf.iloc[0]["Direction"]],
                    "start_pm": [points_gdf.iloc[0]["PM"]],
                    "end_pm": [points_gdf.iloc[-1]["PM"]],
                    "geometry": [final_geometry],
                },
                crs=self.SHNLineGdf.crs,
            )

            splitted_point_gdf = splitted_point_gdf = points_gdf.iloc[[0, -1]].copy()

            # TODO: add export to geojson in splitted folder
            district = splitted_point_gdf["District"].iloc[0]
            county = splitted_point_gdf["County"].iloc[0]
            route = splitted_point_gdf["Route"].iloc[0]
            direction = splitted_point_gdf["Direction"].iloc[0]
            splitted_output_path = (
                Path(output_path)
                / "splitted"
                / f"splitted_d{district}_{county}_{route}_{direction}_{start_pm}_{end_pm}.geojson"
            )
            splitted_point_output_path = (
                Path(output_path)
                / "splitted"
                / f"splitted_pm_d{district}_{county}_{route}_{direction}_{start_pm}_{end_pm}.geojson"
            )
            splitted_result_gdf.to_file(splitted_output_path, driver="GeoJSON")
            splitted_point_gdf.to_file(splitted_point_output_path, driver="GeoJSON")

            return splitted_result_gdf, splitted_point_gdf

        except Exception as e:
            print(f"處理線段時發生錯誤: {str(e)}")
            return None
