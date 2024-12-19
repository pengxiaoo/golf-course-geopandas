import json
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from scipy.ndimage import gaussian_filter1d


def smooth_coordinates(coords, sigma):
    longitudes, latitudes = zip(*coords)
    smooth_longs = gaussian_filter1d(longitudes, sigma)
    smooth_lats = gaussian_filter1d(latitudes, sigma)
    return list(zip(smooth_longs, smooth_lats))


def plot_leafy_trees(ax, points, boundary, color='darkolivegreen', marker='^', size=100, label='LeafyTree'):
    x, y = [], []
    for point in points:
        point_obj = Point(point)
        if boundary.contains(point_obj):
            x.append(point[0])
            y.append(point[1])
    ax.scatter(x, y, color=color, marker=marker, s=size, label=label)


def plot_golf_course(json_file_path, hole_index=0, output_image_path='output_data/golf_course_layout.jpg', sigma=2):
    item_colors = {
        "TeeboxTrace": "yellow",
        "FairwayTrace": "lightgreen",
        "GreenTrace": "darkgreen",
        "BunkerTrace": "sandybrown",
        "WaterTrace": "lightblue",
        "CartpathTrace": "gray",
        "WaterPath": "blue",
        "ShrubTree": "darkolivegreen",
    }
    geometries = []
    attributes = []
    leafy_tree_points = []
    hole_boundary = None
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    holes = data['holes']
    hole = holes[hole_index]
    for item in hole['gpsItems']:
        shape = item['shape']
        item_type = item['itemType']
        coords = [(point['longitude'], point['latitude']) for point in shape]
        if item_type == "HoleBoundary":
            if len(coords) > 2:
                smoothed_coords = smooth_coordinates(coords, sigma)
                hole_boundary = Polygon(smoothed_coords)
        elif item_type == "LeafyTree":
            leafy_tree_points.extend(coords)
        else:
            if len(coords) > 2:
                smoothed_coords = smooth_coordinates(coords, sigma)
                polygon = Polygon(smoothed_coords)
                geometries.append(polygon)
                attributes.append({'itemType': item_type, 'color': item_colors.get(item_type, "red")})
            else:
                point = Point(coords[0])
                geometries.append(point)
                attributes.append({'itemType': item_type, 'color': item_colors.get(item_type, "red")})
    gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
    fig, ax = plt.subplots(figsize=(15, 15))
    if hole_boundary:
        gdf['within_boundary'] = gdf['geometry'].apply(lambda x: hole_boundary.contains(x))
        gdf[gdf['within_boundary']].plot(ax=ax, color=gdf['color'], edgecolor='black')
        hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
        hole_boundary_gdf.plot(ax=ax, color='none', edgecolor='black', linewidth=2)
        plot_leafy_trees(ax, leafy_tree_points, hole_boundary)
    ax.set_title("Golf Course Hole Layout (Smoothed)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left", title="Course Elements")
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    plot_golf_course(json_file_path='input_data/golf_course_holes.json', hole_index=7)
