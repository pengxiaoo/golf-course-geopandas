import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import gaussian_filter1d
import os
import logging
import numpy as np

script_dir = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{script_dir}/input_data/golf_course_plotting.log"),
        logging.StreamHandler(),
    ],
)
smooth_sigma = 1
geo_accuracy = 6
dpi = 300
max_pixels = 2000
target_meters_per_pixel = 0.2 
lat_to_meter_ratio = 111000
invalid_coordinates = {
    "longitude": -180,
    "latitude": -90,
}
default_width = 0.0
boarder_width = 0.1
base_area = 10 * 10  # 假设10x10英寸为基准尺寸
edge_color = "black"
item_colors = {
    # the following are polygons
    "TeeboxTrace": "lawngreen",
    "FairwayTrace": "lawngreen",
    "GreenTrace": "lawngreen",
    "BunkerTrace": "yellow",
    "VegetationTrace": "seagreen",
    "WaterTrace": "skyblue",
    "HoleBoundary": "forestgreen",  # boundary, i.e. the biggest polygon
    # the following are lines
    "WaterPath": "skyblue",
    "CartpathTrace": "lightgrey",
    "CartpathPath": "lightgrey",
    # the following are dots or small cluster of dots
    "LeafyTree": "darkgreen",
    "ShrubTree": "darkgreen",
    "PalmTree": "darkgreen",
    "PineTree": "darkgreen",
    "Green": "white",
    "Approach": "white",
    "Tee": "white",
}
item_markers = {
    "LeafyTree": "^",
    "ShrubTree": "+",
    "PalmTree": "o",
    "PineTree": "x",
    "Green": "o",
    "Approach": "o",
    "Tee": "o",
}
item_marker_icon_paths = {
    # create random icons initially. after success, we will have designer to provide better icons
    "LeafyTree": "icons/leafy_tree.png",
    "ShrubTree": "icons/shrub_tree.png",
    "PalmTree": "icons/palm_tree.png",
    "PineTree": "icons/pine_tree.png",
    "Green": "icons/green.webp",
    "Approach": "icons/approach.png",
    "Tee": "icons/tee.png",
}
item_marker_base_size = {
    # todo: need to scale according to the figure size
    "LeafyTree": 200,
    "ShrubTree": 200,
    "PalmTree": 200,
    "PineTree": 200,
    "Green": 100,
    "Approach": 100,
    "Tee": 100,
}
line_widths = {
    "WaterPath": 2.0,
    "CartpathTrace": default_width,
}
fairway_colors = [
    "lawngreen",
    "forestgreen",
]  # 定义两种交替的颜色


def smooth_coordinates(coords):
    longitudes, latitudes = zip(*coords)
    smooth_longs = gaussian_filter1d(longitudes, smooth_sigma)
    smooth_lats = gaussian_filter1d(latitudes, smooth_sigma)
    return list(zip(smooth_longs, smooth_lats))


def get_smooth_polygon(coords):
    count = len(coords)
    if count < 3:
        logger.warning(f"坐标点数量不足以创建多边形: {count} 个点")
        return None
    # 确保多边形是闭合的（首尾坐标相同）
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    smoothed_coords = smooth_coordinates(coords)
    try:
        return Polygon(smoothed_coords)
    except ValueError as e:
        logger.warning(f"创建多边形失败: {e}")
        return None


def get_marker_scale_size(ax, item_type):
    fig_width, fig_height = ax.figure.get_size_inches()
    fig_area = fig_width * fig_height
    scale_factor = fig_area / base_area
    marker_scaled_size = item_marker_base_size[item_type] * scale_factor
    return marker_scaled_size


def get_stripe_scale_factor(ax):
    fig_width, fig_height = ax.figure.get_size_inches()
    fig_area = fig_width * fig_height
    scale_factor = fig_area / base_area
    base_spaces = 10
    stripe_scale_factor = max(1, int(base_spaces * scale_factor))
    logger.warning(f"stripe_scale_factor: {stripe_scale_factor}")
    return stripe_scale_factor


def plot_markers(ax, points, boundary, item_type, zorder=10):
    if points is None or len(points) == 0:
        return
    x, y = [], []
    for point in points:
        point_obj = Point(point)
        if boundary.contains(point_obj):
            x.append(point[0])
            y.append(point[1])
    scaled_size = get_marker_scale_size(ax, item_type)
    ax.scatter(
        x,
        y,
        color=item_colors[item_type],
        marker=item_markers[item_type],
        s=scaled_size,
        label=item_type,
        zorder=zorder,
    )


# todo: has bugs
def plot_markers_with_icons(ax, points, hole_boundary, item_type):
    if points is None or len(points) == 0:
        return
    for point in points:
        if inside_polygon(point, hole_boundary):
            scaled_size = get_marker_scale_size(ax, item_type)
            icon_path = item_marker_icon_paths[item_type]
            icon = plt.imread(icon_path)
            imagebox = OffsetImage(icon, zoom=scaled_size)
            ab = AnnotationBbox(imagebox, (point[0], point[1]), frameon=False, pad=0)
            ax.add_artist(ab)


def inside_polygon(coord, polygon):
    point = Point(coord)
    return polygon and polygon.contains(point)


def intersection_of_polygons(polygon1, polygon2):
    try:
        if not polygon1 or not polygon2:
            return None
        if not polygon1.is_valid:
            return None
        if not polygon2.is_valid:
            return None
        return polygon1.intersection(polygon2)
    except Exception as e:
        logger.warning(f"计算多边形相交时出错: {e}")
        return None


def calculate_pixel_resolution(bounds):
    x_min, y_min, x_max, y_max = bounds
    center_lat = (y_min + y_max) / 2
    center_lat_rad = np.pi * center_lat / 180
    width_meters = (x_max - x_min) * lat_to_meter_ratio * np.cos(center_lat_rad)
    height_meters = (y_max - y_min) * lat_to_meter_ratio

    # 计算需要的像素数
    pixels_width = int(width_meters / target_meters_per_pixel)
    pixels_height = int(height_meters / target_meters_per_pixel)

    # 计算所需的figure尺寸和dpi
    fig_width = pixels_width / dpi
    fig_height = pixels_height / dpi

    return fig_width, fig_height, dpi, target_meters_per_pixel, center_lat_rad


def plot_course(club_id, course_id, hole_number, holes, output_folder_path):
    debug_info = f"clubId: {club_id}, courseId: {course_id}, holeNumber: {hole_number}"
    hole = holes[hole_number - 1]
    geometries = []
    attributes = []
    hole_boundary = None
    (green, approach, tee) = (
        hole.get("greenGPSCoordinate", invalid_coordinates),
        hole.get("approachGPSCoordinate", invalid_coordinates),
        hole.get("teeGPSCoordinate", invalid_coordinates),
    )
    green_coord = (green["longitude"], green["latitude"])
    approach_coord = (approach["longitude"], approach["latitude"])
    tee_coord = (tee["longitude"], tee["latitude"])
    # record the hole boundary first
    for item in hole["gpsItems"]:
        item_type = item["itemType"]
        if item_type == "HoleBoundary":
            coords = [
                (point["longitude"], point["latitude"]) for point in item["shape"]
            ]
            hole_boundary = get_smooth_polygon(coords)
            if hole_boundary:
                geometries.append(hole_boundary)
                attributes.append(
                    {"itemType": item_type, "color": item_colors[item_type]}
                )
            break
    # record the rest of the items, other than hole boundary
    leafy_tree_points = []
    shrub_tree_points = []
    palm_tree_points = []
    pine_tree_points = []
    for item in hole["gpsItems"]:
        item_type = item["itemType"]
        if item_type == "HoleBoundary":
            continue
        coords = [(point["longitude"], point["latitude"]) for point in item["shape"]]
        if len(coords) == 0:
            continue
        if item_type == "LeafyTree":
            leafy_tree_points.extend(coords)
        elif item_type == "ShrubTree":
            shrub_tree_points.extend(coords)
        elif item_type == "PalmTree":
            palm_tree_points.extend(coords)
        elif item_type == "PineTree":
            pine_tree_points.extend(coords)
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
            if item_type not in item_colors:
                logger.warning(
                    f"item_type not in item_colors, item_type: {item_type}, {debug_info}"
                )
            if len(coords) > 2:
                item_polygon = get_smooth_polygon(coords)
                item_in_course = intersection_of_polygons(item_polygon, hole_boundary)
                if item_in_course and (not item_in_course.is_empty):
                    geometries.append(item_in_course)
                    attributes.append(
                        {"itemType": item_type, "color": item_colors[item_type]}
                    )
    try:
        # 先绘制所有内容
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
        if "itemType" not in gdf.columns or hole_boundary is None:
            logger.warning(
                f"itemType not in gdf.columns, or hole_boundary is None. {debug_info}"
            )
            return

        # 计算中心纬度
        bounds = hole_boundary.bounds

        # 计算图像尺寸和分辨率
        fig_width, fig_height, adjusted_dpi, resolution, center_lat_rad = calculate_pixel_resolution(bounds)

        # 创建图形
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor="none")
        ax.set_facecolor("none")  # 设置坐标轴区域透明
        ax.spines["top"].set_visible(False)  # 隐藏上边框
        ax.spines["right"].set_visible(False)  # 隐藏右边框
        ax.spines["bottom"].set_visible(False)  # 隐藏下边框
        ax.spines["left"].set_visible(False)  # 隐藏左边框

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
            elif row["itemType"] == "FairwayTrace":
                stripe_scale_factor = get_stripe_scale_factor(ax)
                hatch_pattern = "\\" + " " * stripe_scale_factor
                gpd.GeoSeries([row.geometry]).plot(
                    ax=ax,
                    color=fairway_colors[0],
                    edgecolor=fairway_colors[0],
                    linewidth=default_width,
                    hatch=hatch_pattern,
                    alpha=0.3,
                )
            else:
                gpd.GeoSeries([row.geometry]).plot(
                    ax=ax,
                    color=row["color"],
                    edgecolor=edge_color,
                    linewidth=default_width,
                )
        green_trace = gdf[gdf["itemType"] == "GreenTrace"]
        green_trace.plot(
            ax=ax,
            color=green_trace["color"],
            edgecolor=edge_color,
            linewidth=default_width,
        )
        plot_markers(ax, leafy_tree_points, hole_boundary, "LeafyTree")
        plot_markers(ax, shrub_tree_points, hole_boundary, "ShrubTree")
        plot_markers(ax, palm_tree_points, hole_boundary, "PalmTree")
        plot_markers(ax, pine_tree_points, hole_boundary, "PineTree")
        # plot_markers_with_icons(ax, [green_coord], hole_boundary, "Green")
        # plot_markers_with_icons(ax, [approach_coord], hole_boundary, "Approach")
        # plot_markers_with_icons(ax, [tee_coord], hole_boundary, "Tee")
        # 在所有内容绘制完成后，设置坐标轴属性
        ax.set_aspect("equal")  # 先设置为等比例

        # 隐藏坐标轴刻度和标签
        ax.set_xticks([])
        ax.set_yticks([])

        # 调整坐标轴范围，不添加额外的边距
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])

        # 设置图形边距为0
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # 最后再设置正确的纵横比
        ax.set_aspect(1 / np.cos(center_lat_rad))

        logger.info(f"Figure size (inches): width={fig_width}, height={fig_height}")
        logger.info(f"Resolution: {resolution:.2f} meters/pixel")
        logger.info(
            f"Final pixels: width={fig_width * adjusted_dpi}, height={fig_height * adjusted_dpi}"
        )

        # 保存图片
        plt.savefig(
            f"{output_folder_path}/{club_id}_{course_id}_{hole_number}.png",
            dpi=adjusted_dpi,
            format="png",
            bbox_inches="tight",
            pad_inches=0,
            transparent=True,
        )
    except Exception as e:
        logger.info(f"Exception: {e}, {debug_info}")
        raise
    finally:
        plt.close("all")


def plot_courses(input_jsonl_file_path, output_folder_path):
    with open(input_jsonl_file_path, "r", newline="", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line)
            club_id = data["clubId"]
            course_id = data["courseId"]
            holes = data["holes"]
            hole_count = len(holes)
            for hole_number in range(1, hole_count + 1):
                plot_course(club_id, course_id, hole_number, holes, output_folder_path)


if __name__ == "__main__":
    input_path = os.path.join(
        script_dir, "input_data", "golf_course_layout_samples.jsonl"
    )
    output_path = os.path.join(script_dir, "output_data")
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    os.makedirs(output_path, exist_ok=True)
    plot_courses(input_path, output_path)
