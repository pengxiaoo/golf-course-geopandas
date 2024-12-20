import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import gaussian_filter1d

smooth_sigma = 2
figsize = (15, 15)
geo_accuracy = 6
dpi = 200
default_width = 0.5
boarder_width = 1.0
edge_color = "black"
item_colors = {
    "TeeboxTrace": "yellow",
    "FairwayTrace": "lawngreen",
    "GreenTrace": "lawngreen",
    "BunkerTrace": "sandybrown",
    "WaterTrace": "lightblue",
    "WaterPath": "lightblue",  # line
    "CartpathTrace": "lightgrey",  # line
    "ShrubTree": "darkolivegreen",
    "HoleBoundary": "forestgreen",  # boundary
    # the following are markers
    "LeafyTree": "darkolivegreen",
    "Green": "white",
    "Approach": "white",
    "Tee": "white",
}
# todo: replace markers with icons
item_markers = {
    "LeafyTree": "^",
    "Green": "o",
    "Approach": "o",
    "Tee": "o",
}
marker_sizes = {
    "LeafyTree": 100,
    "Green": 20,
    "Approach": 20,
    "Tee": 20,
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


def plot_markers(ax, points, boundary, item_type):
    x, y = [], []
    for point in points:
        point_obj = Point(point)
        if boundary.contains(point_obj):
            x.append(point[0])
            y.append(point[1])
    ax.scatter(x, y, color=item_colors[item_type], marker=item_markers[item_type], s=marker_sizes[item_type],
               label=item_type)


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
    (green, approach, tee) = (hole['greenGPSCoordinate'], hole['approachGPSCoordinate'], hole['teeGPSCoordinate'])
    green_coord = (green['longitude'], green['latitude'])
    approach_coord = (approach['longitude'], approach['latitude'])
    tee_coord = (tee['longitude'], tee['latitude'])
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
                attributes.append({'itemType': item_type, 'color': item_colors[item_type],
                                   'lineWidth': line_widths[item_type]})
        else:
            if len(coords) > 2:
                polygon = get_smooth_polygon(coords)
                geometries.append(polygon)
                attributes.append({'itemType': item_type, 'color': item_colors[item_type]})
            else:
                point = Point(coords[0])
                geometries.append(point)
                attributes.append({'itemType': item_type, 'color': item_colors[item_type]})
    fig, ax = plt.subplots(figsize=figsize)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter(f'%.{geo_accuracy}f'))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter(f'%.{geo_accuracy}f'))
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
    hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
    hole_boundary_gdf.plot(ax=ax, color=item_colors["HoleBoundary"], edgecolor=edge_color, linewidth=boarder_width)
    for _, row in gdf.iterrows():
        if isinstance(row.geometry, LineString):  # 自定义线宽
            x, y = row.geometry.xy
            ax.plot(x, y, color=row['color'], linewidth=row['lineWidth'])
        elif row['itemType'] == "GreenTrace":  # 延后绘制 GreenTrace
            continue
        else:
            gpd.GeoSeries([row.geometry]).plot(ax=ax, color=row['color'], edgecolor=edge_color, linewidth=default_width)
    green_trace = gdf[gdf['itemType'] == "GreenTrace"]
    green_trace.plot(ax=ax, color=green_trace['color'], edgecolor=edge_color, linewidth=default_width)
    plot_markers(ax, leafy_tree_points, hole_boundary, "LeafyTree")
    plot_markers(ax, [green_coord], hole_boundary, "Green")
    plot_markers(ax, [approach_coord], hole_boundary, "Approach")
    plot_markers(ax, [tee_coord], hole_boundary, "Tee")
    ax.set_title(f"Golf Course Hole Layout (hole {hole_number})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    output_image_path = f"output_data/hole_{hole_number}_layout.jpg"
    plt.savefig(output_image_path, dpi=dpi, format='jpeg', bbox_inches='tight')


if __name__ == '__main__':
    for hole_number in range(1, 19):
        plot_golf_course(json_file_path='input_data/golf_course_holes_eagle_vines.json', hole_number=hole_number)
