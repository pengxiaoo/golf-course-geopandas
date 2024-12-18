import json
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from scipy.ndimage import gaussian_filter1d


def smooth_coordinates(coords, sigma):
    """
    使用高斯平滑来平滑坐标点。
    """
    longitudes, latitudes = zip(*coords)
    smooth_longs = gaussian_filter1d(longitudes, sigma)
    smooth_lats = gaussian_filter1d(latitudes, sigma)
    return list(zip(smooth_longs, smooth_lats))


def plot_leafy_trees(ax, points, color='darkolivegreen', marker='^', size=100, label='LeafyTree'):
    """
    绘制 LeafyTree 的位置。

    参数:
    - ax: Matplotlib Axes，绘图的轴。
    - points: list of tuples，每个元组包含一个点的经度和纬度。
    - color: str，点的颜色，默认为 'darkolivegreen'。
    - marker: str，点的形状，默认为 '^'。
    - size: int，点的大小，默认为 100。
    - label: str，图例标签，默认为 'LeafyTree'。
    """
    x = [point[0] for point in points]
    y = [point[1] for point in points]
    ax.scatter(x, y, color=color, marker=marker, s=size, label=label)


def plot_golf_course(json_file_path, output_image_path='golf_course_layout.jpg', sigma=2):
    # 定义颜色映射
    item_colors = {
        "TeeboxTrace": "green",
        "FairwayTrace": "lightgreen",
        "GreenTrace": "darkgreen",
        "BunkerTrace": "sandybrown",
        "WaterTrace": "blue",
        "CartpathTrace": "gray",
        "WaterPath": "cyan",
        "HoleBoundary": "none"
    }

    geometries = []
    attributes = []
    leafy_tree_points = []

    # 读取JSON文件
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # 遍历JSON数据并创建GeoDataFrame
    for item in data['gpsItems']:
        shape = item['shape']
        item_type = item['itemType']

        # 提取LeafyTree坐标点
        if item_type == "LeafyTree":
            for point in shape:
                leafy_tree_points.append((point['longitude'], point['latitude']))
        else:
            coords = [(point['longitude'], point['latitude']) for point in shape]

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

    gdf[gdf['itemType'] == "HoleBoundary"].plot(ax=ax, color='none', edgecolor='black', linewidth=2)
    gdf[gdf['itemType'] != "HoleBoundary"].plot(ax=ax, color=gdf[gdf['itemType'] != "HoleBoundary"]['color'],
                                                edgecolor='black')

    # 调用封装的函数来绘制 LeafyTree
    plot_leafy_trees(ax, leafy_tree_points)

    ax.set_title("Golf Course Hole Layout (Smoothed)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left", title="Course Elements")

    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    plot_golf_course(json_file_path='input_data/golf_course_hole_gps_items.json')
