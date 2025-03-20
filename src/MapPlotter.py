import geopandas as gpd
from pathlib import Path
import leafmap.foliumap as leafmap

DATA_PATH = "data"


def plotting_map(
    lineGeoJSONPath=None,
    pointGeoJSONPath=None,
    lineGdf=None,
    pointGdf=None,
    dataPath=DATA_PATH,
):

    if lineGeoJSONPath is not None:
        lineGdf = gpd.read_file(lineGeoJSONPath)
    if pointGeoJSONPath is not None:
        pointGdf = gpd.read_file(pointGeoJSONPath)

    if lineGdf is not None:
        lineGdf = lineGdf
    if pointGdf is not None:
        pointGdf = pointGdf

    try:
        # calculate the centroid
        if lineGdf is not None and len(lineGdf) > 0:
            bounds = lineGdf.total_bounds
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
            lineGdf,
            layer_name="Entire Highway/StateRoute",
            style=line_style,
            hover_style=hover_style,
        )

        m.add_gdf(
            pointGdf,
            layer_name="Points",
            style=point_style,
            hover_style=hover_style,
            show=False,
        )

        m.add_layer_control()

        return m

    except Exception as e:
        print(f"Error: {str(e)}")
        raise
