import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import gaussian_filter1d

item_colors = {
    "TeeboxTrace": "yellow",
    "FairwayTrace": "lawngreen",
    "GreenTrace": "forestgreen",
    "BunkerTrace": "sandybrown",
    "WaterTrace": "lightblue",
    "WaterPath": "lightblue",  # line
    "CartpathTrace": "lightgrey",  # line
    "ShrubTree": "darkolivegreen",
    "LeafyTree": "darkolivegreen",  # points
    "HoleBoundary": "forestgreen",  # boundary
}
item_markers = {
    "LeafyTree": "^",
}
line_widths = {
    # todo: this doesn't work
    "WaterPath": 3.0,
    "CartpathTrace": 0.5,
}


def smooth_coordinates(coords, sigma):
    longitudes, latitudes = zip(*coords)
    smooth_longs = gaussian_filter1d(longitudes, sigma)
    smooth_lats = gaussian_filter1d(latitudes, sigma)
    return list(zip(smooth_longs, smooth_lats))


def get_smooth_polygon(coords, sigma=2):
    smoothed_coords = smooth_coordinates(coords, sigma)
    return Polygon(smoothed_coords)


def plot_markers(ax, points, boundary, item_type, size=100):
    # todo: set image as marker
    x, y = [], []
    for point in points:
        point_obj = Point(point)
        if boundary.contains(point_obj):
            x.append(point[0])
            y.append(point[1])
    ax.scatter(x, y, color=item_colors[item_type], marker=item_markers[item_type], s=size, label=item_type)


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
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    holes = data['holes']
    hole = holes[hole_number - 1]
    for item in hole['gpsItems']:
        item_type = item['itemType']
        if item_type == "HoleBoundary":
            coords = [(point['longitude'], point['latitude']) for point in item['shape']]
            hole_boundary = get_smooth_polygon(coords)
            geometries.append(hole_boundary)
            attributes.append({'itemType': item_type, 'color': item_colors[item_type]})
            break
    for item in hole['gpsItems']:
        item_type = item['itemType']
        if item_type == "HoleBoundary":
            continue
        coords = [(point['longitude'], point['latitude']) for point in item['shape']]
        if len(coords) == 0:
            continue
        if item_type == "LeafyTree":
            leafy_tree_points.extend(coords)
        elif item_type == "WaterTrace":
            water_polygon = get_smooth_polygon(coords)
            water_in_course = intersection_of_polygons(water_polygon, hole_boundary)
            if not water_in_course.is_empty:
                geometries.append(water_in_course)
                attributes.append({'itemType': item_type, 'color': item_colors[item_type]})
        elif item_type == "CartpathTrace" or item_type == "WaterPath":
            coords = [coord for coord in coords if inside_polygon(coord, hole_boundary)]
            if len(coords) > 1:
                line = LineString(coords)
                geometries.append(line)
                attributes.append(
                    {'itemType': item_type, 'color': item_colors[item_type], 'lineWidth': line_widths[item_type]})
        else:
            if len(coords) > 2:
                polygon = get_smooth_polygon(coords)
                geometries.append(polygon)
                attributes.append({'itemType': item_type, 'color': item_colors[item_type]})
            else:
                point = Point(coords[0])
                geometries.append(point)
                attributes.append({'itemType': item_type, 'color': item_colors[item_type]})
    fig, ax = plt.subplots(figsize=(15, 15))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.6f'))  # 保留6位小数
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.6f'))
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
    hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
    hole_boundary_gdf.plot(ax=ax, color=item_colors["HoleBoundary"], edgecolor='black', linewidth=2)
    gdf.plot(ax=ax, color=gdf['color'], edgecolor='black')
    plot_markers(ax, leafy_tree_points, hole_boundary, "LeafyTree")
    ax.set_title(f"Golf Course Hole Layout (hole {hole_number})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    output_image_path = f"output_data/hole_{hole_number}_layout.png"
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    for hole_number in range(1, 19):
        plot_golf_course(json_file_path='input_data/golf_course_holes_eagle_vines.json', hole_number=hole_number)
