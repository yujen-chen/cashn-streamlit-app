import geopandas as gpd
from pathlib import Path
import leafmap.foliumap as leafmap

DATA_PATH = "data"


class MapPlotter:

    def __init__(self, lineGeoJSONPath, pointGeoJSONPath, dataPath=DATA_PATH):
        self.lineGdf = gpd.read_file(lineGeoJSONPath)
        self.pointGdf = gpd.read_file(pointGeoJSONPath)

    def plotting_map(self, lineGdf, pointGdf):
        try:
            # calculate the centroid
            if len(self.lineGdf) > 0:
                bounds = self.lineGdf.total_bounds
                center_coords = [
                    (bounds[1] + bounds[3]) / 2,
                    (bounds[0] + bounds[2]) / 2,
                ]
            else:
                raise ValueError("No Line geometry data.")

            m = leafmap.Map(center=center_coords, zoom=13)

            line_style = {
                "color": "blue",
                "weight": 3,
                "opacity": 1,
            }

            point_style = {
                "radius": 5,
                "color": "red",
                "fillOpacity": 0.8,
                "fillColor": "orange",
                "weight": 3,
            }

            hover_style = {"fillColor": "yellow", "fillOpacity": 1.0}

            # Add point layer with styling

            m.add_gdf(
                self.lineGdf,
                layer_name="Original Line",
                style=line_style,
                hover_style=hover_style,
            )

            m.add_gdf(
                self.pointGdf,
                layer_name="Points",
                style=point_style,
                hover_style=hover_style,
            )

            m.add_layer_control()

            return m

        except Exception as e:
            print(f"Error: {str(e)}")
            raise
