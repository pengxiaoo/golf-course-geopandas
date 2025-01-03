import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import gaussian_filter1d

smooth_sigma = 2
figsize = (15, 15)
geo_accuracy = 6
dpi = 300
default_width = 0.5
boarder_width = 1.0
edge_color = "black"
item_colors = {
    # the following are polygons
    "TeeboxTrace": "yellow",
    "FairwayTrace": "lawngreen",
    "GreenTrace": "greenyellow",
    "BunkerTrace": "sandybrown",
    "VegetationTrace": "seagreen",
    "ShrubTree": "darkgreen",
    "WaterTrace": "skyblue",
    "HoleBoundary": "forestgreen",  # boundary, i.e. the biggest polygon
    # the following are lines
    "WaterPath": "skyblue",
    "CartpathTrace": "lightgrey",
    # the following are markers, i.e. points
    "LeafyTree": "darkgreen",
    "Green": "white",
    "Approach": "white",
    "Tee": "white",
}
item_markers = {
    "LeafyTree": "^",
    "Green": "o",
    "Approach": "o",
    "Tee": "o",
}
item_marker_icon_paths = {
    # todo: ask designer to provide better icons
    "LeafyTree": "icons/leafy_tree.png",
    "Green": "icons/green.webp",
    "Approach": "icons/approach.png",
    "Tee": "icons/tee.png",
}
marker_sizes = {
    "LeafyTree": 200,
    "Green": 100,
    "Approach": 10,
    "Tee": 100,
}
line_widths = {
    "WaterPath": 2.0,
    "CartpathTrace": default_width,
}


def smooth_coordinates(coords):
    longitudes, latitudes = zip(*coords)
    smooth_longs = gaussian_filter1d(longitudes, smooth_sigma)
    smooth_lats = gaussian_filter1d(latitudes, smooth_sigma)
    return list(zip(smooth_longs, smooth_lats))


def get_smooth_polygon(coords):
    smoothed_coords = smooth_coordinates(coords)
    return Polygon(smoothed_coords)


def plot_markers(ax, points, boundary, item_type, zorder=10):
    x, y = [], []
    for point in points:
        point_obj = Point(point)
        if boundary.contains(point_obj):
            x.append(point[0])
            y.append(point[1])
    ax.scatter(
        x,
        y,
        color=item_colors[item_type],
        marker=item_markers[item_type],
        s=marker_sizes[item_type],
        label=item_type,
        zorder=zorder,
    )


def plot_markers_with_icons(ax, points, hole_boundary, item_type):
    for point in points:
        if inside_polygon(point, hole_boundary):
            icon_path = item_marker_icon_paths[item_type]
            icon = plt.imread(icon_path)
            zoom_factor = (marker_sizes[item_type] / 100) * 0.05
            imagebox = OffsetImage(icon, zoom=zoom_factor)
            ab = AnnotationBbox(imagebox, (point[0], point[1]), frameon=False, pad=0)
            ax.add_artist(ab)


def inside_polygon(coord, polygon):
    point = Point(coord)
    return polygon.contains(point)


def intersection_of_polygons(polygon1, polygon2):
    return polygon1.intersection(polygon2)


def plot_golf_course(json_file_path, hole_number):
    geometries = []
    attributes = []
    leafy_tree_points = []
    hole_boundary = None
    with open(json_file_path, "r") as file:
        data = json.load(file)
    holes = data["holes"]
    hole = holes[hole_number - 1]
    (green, approach, tee) = (
        hole["greenGPSCoordinate"],
        hole["approachGPSCoordinate"],
        hole["teeGPSCoordinate"],
    )
    green_coord = (green["longitude"], green["latitude"])
    approach_coord = (approach["longitude"], approach["latitude"])
    tee_coord = (tee["longitude"], tee["latitude"])
    for item in hole["gpsItems"]:
        item_type = item["itemType"]
        if item_type == "HoleBoundary":
            coords = [
                (point["longitude"], point["latitude"]) for point in item["shape"]
            ]
            hole_boundary = get_smooth_polygon(coords)
            geometries.append(hole_boundary)
            attributes.append({"itemType": item_type, "color": item_colors[item_type]})
            break
    for item in hole["gpsItems"]:
        item_type = item["itemType"]
        if item_type == "HoleBoundary":
            continue
        coords = [(point["longitude"], point["latitude"]) for point in item["shape"]]
        if len(coords) == 0:
            continue
        if item_type == "LeafyTree":
            leafy_tree_points.extend(coords)
        elif item_type == "CartpathTrace" or item_type == "WaterPath":
            coords = [coord for coord in coords if inside_polygon(coord, hole_boundary)]
            if len(coords) > 1:
                line = LineString(coords)
                geometries.append(line)
                attributes.append(
                    {
                        "itemType": item_type,
                        "color": item_colors[item_type],
                        "lineWidth": line_widths[item_type],
                    }
                )
        else:
            if len(coords) > 2:
                item_polygon = get_smooth_polygon(coords)
                item_in_course = intersection_of_polygons(item_polygon, hole_boundary)
                if not item_in_course.is_empty:
                    geometries.append(item_in_course)
                    attributes.append(
                        {"itemType": item_type, "color": item_colors[item_type]}
                    )
    fig, ax = plt.subplots(figsize=figsize)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter(f"%.{geo_accuracy}f"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter(f"%.{geo_accuracy}f"))
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
    hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
    hole_boundary_gdf.plot(
        ax=ax,
        color=item_colors["HoleBoundary"],
        edgecolor=edge_color,
        linewidth=boarder_width,
    )
    for _, row in gdf.iterrows():
        if isinstance(row.geometry, LineString):  # 自定义线宽
            x, y = row.geometry.xy
            ax.plot(x, y, color=row["color"], linewidth=row["lineWidth"], zorder=5)
        elif row["itemType"] == "GreenTrace":  # 延后绘制 GreenTrace
            continue
        else:
            gpd.GeoSeries([row.geometry]).plot(
                ax=ax, color=row["color"], edgecolor=edge_color, linewidth=default_width
            )
    green_trace = gdf[gdf["itemType"] == "GreenTrace"]
    green_trace.plot(
        ax=ax, color=green_trace["color"], edgecolor=edge_color, linewidth=default_width
    )
    plot_markers(ax, leafy_tree_points, hole_boundary, "LeafyTree")
    # plot_markers_with_icons(ax, [green_coord], hole_boundary, "Green")
    # plot_markers_with_icons(ax, [approach_coord], hole_boundary, "Approach")
    # plot_markers_with_icons(ax, [tee_coord], hole_boundary, "Tee")
    ax.set_title(f"Golf Course Hole Layout (hole {hole_number})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    output_image_path = f"output_data/hole_{hole_number}_layout.jpg"
    # compress the image
    plt.savefig(
        output_image_path, dpi=dpi, format="jpeg", bbox_inches="tight"
    )


if __name__ == "__main__":
    for hole_number in range(1, 19):
        plot_golf_course(
            json_file_path="input_data/golf_course_holes_eagle_vines.json",
            hole_number=hole_number,
        )
