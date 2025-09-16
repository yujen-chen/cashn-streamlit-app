import math
import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import LineString, MultiLineString


def plotting_map(
    lineGeoJSONPath=None,
    pointGeoJSONPath=None,
    lineGdf=None,
    pointGdf=None,
):

    if lineGeoJSONPath is not None:
        lineGdf = gpd.read_file(lineGeoJSONPath)
    if pointGeoJSONPath is not None:
        pointGdf = gpd.read_file(pointGeoJSONPath)

    if lineGdf is not None and not lineGdf.empty and lineGdf.crs is not None:
        if lineGdf.crs.to_epsg() != 4326:
            lineGdf = lineGdf.to_crs(epsg=4326)
    if pointGdf is not None and not pointGdf.empty and pointGdf.crs is not None:
        if pointGdf.crs.to_epsg() != 4326:
            pointGdf = pointGdf.to_crs(epsg=4326)

    try:
        # calculate the centroid
        if lineGdf is not None and len(lineGdf) > 0:
            bounds = lineGdf.total_bounds  # minx, miny, maxx, maxy
            center_coords = [
                (bounds[1] + bounds[3]) / 2,
                (bounds[0] + bounds[2]) / 2,
            ]
        else:
            raise ValueError("No Line geometry data.")

        fig = go.Figure()

        if lineGdf is not None and not lineGdf.empty:
            show_line_legend = True
            for geom in lineGdf.geometry:
                if geom is None or geom.is_empty:
                    continue
                segments = []
                if isinstance(geom, LineString):
                    segments = [geom.coords]
                elif isinstance(geom, MultiLineString):
                    segments = [line.coords for line in geom.geoms]
                for coords in segments:
                    if len(coords) < 2:
                        continue
                    lons, lats = zip(*coords)
                    fig.add_trace(
                        go.Scattermapbox(
                            lat=lats,
                            lon=lons,
                            mode="lines",
                            line=dict(color="#2c7fb8", width=4),
                            name="Highway Segment" if show_line_legend else None,
                            hoverinfo="none",
                            showlegend=show_line_legend,
                        )
                    )
                    show_line_legend = False

        if pointGdf is not None and not pointGdf.empty:
            def format_pm(row):
                value = row.get("PM") if hasattr(row, "get") else None
                if isinstance(value, (int, float)):
                    return f"PM {value:.2f}"
                if value is not None:
                    return f"PM {value}"
                return "Point"

            hover_text = pointGdf.apply(format_pm, axis=1)
            fig.add_trace(
                go.Scattermapbox(
                    lat=pointGdf.geometry.y,
                    lon=pointGdf.geometry.x,
                    mode="markers",
                    marker=dict(size=9, color="#f97316"),
                    name="Postmile Points",
                    text=hover_text,
                    hovertemplate="%{text}<extra></extra>",
                )
            )

        min_lon, min_lat, max_lon, max_lat = bounds
        padding_ratio = 0.05
        lon_span = max(max_lon - min_lon, 0.0001) * (1 + padding_ratio * 2)
        lat_span = max(max_lat - min_lat, 0.0001) * (1 + padding_ratio * 2)

        def calculate_zoom(lon_span_value, lat_span_value, latitude):
            lon_zoom = math.log(360 / lon_span_value) / math.log(2)
            cos_lat = max(math.cos(math.radians(latitude)), 1e-4)
            lat_zoom = math.log(360 / (lat_span_value * cos_lat)) / math.log(2)
            zoom = min(lon_zoom, lat_zoom)
            return float(min(max(zoom, 3), 16))

        approx_zoom = calculate_zoom(lon_span, lat_span, center_coords[0])

        mapbox_config = dict(
            style="carto-positron",
            center=dict(lat=center_coords[0], lon=center_coords[1]),
            zoom=approx_zoom,
        )

        fig.update_layout(
            mapbox=mapbox_config,
            margin=dict(l=0, r=0, t=0, b=0),
            width=960,
            height=720,
            legend=dict(orientation="h", y=0.01, yanchor="bottom", x=0.99, xanchor="right"),
        )

        return fig

    except Exception as e:
        print(f"Error: {str(e)}")
        raise
