import os
import json
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import Point, LineString
import numpy as np
from hole_item import ItemType, ItemStyle, Polygon, Line, Marker
from utils import get_smooth_polygon, logger, root_dir

dpi = 300
target_meters_per_pixel = 0.2
lat_to_meter_ratio = 111000
default_width = 0.0
boarder_width = 0.1
base_area = 10 * 10  # 假设10x10英寸为基准尺寸
edge_color = "black"
fairway_colors = [
    "lawngreen",
    "forestgreen",
]  # 定义两种交替的颜色

# polygons
teeboxTrace = Polygon(ItemType.TeeboxTrace, "lawngreen")
fairwayTrace = Polygon(ItemType.FairwayTrace, "lawngreen")
greenTrace = Polygon(ItemType.GreenTrace, "lawngreen")
bunkerTrace = Polygon(ItemType.BunkerTrace, "yellow")
vegetationTrace = Polygon(ItemType.VegetationTrace, "seagreen")
waterTrace = Polygon(ItemType.WaterTrace, "skyblue")
holeBoundary = Polygon(ItemType.HoleBoundary, "forestgreen")
# lines
waterPath = Line(ItemType.WaterPath, "skyblue", line_width=2.0)
cartpathTrace = Line(ItemType.CartpathTrace, "lightgrey", line_width=0.5)
cartpathPath = Line(ItemType.CartpathPath, "lightgrey", line_width=0.5)
# markers
leafyTree = Marker(ItemType.LeafyTree, "darkgreen", symbol_icon="^", img_icon="leafy_tree")
shrubTree = Marker(ItemType.ShrubTree, "darkgreen", symbol_icon="*", img_icon="shrub_tree")
palmTree = Marker(ItemType.PalmTree, "darkgreen", symbol_icon="o", img_icon="palm_tree")
pineTree = Marker(ItemType.PineTree, "darkgreen", symbol_icon="|", img_icon="pine_tree")
green = Marker(ItemType.Green, "white", symbol_icon="o", img_icon="green", base_size=20)
approach = Marker(ItemType.Approach, "white", symbol_icon="o", img_icon="approach", base_size=20)
tee = Marker(ItemType.Tee, "white", symbol_icon="o", img_icon="tee", base_size=20)


def get_item_by_type(item_type: ItemType):
    if item_type == ItemType.TeeboxTrace.value:
        return teeboxTrace
    elif item_type == ItemType.FairwayTrace.value:
        return fairwayTrace
    elif item_type == ItemType.GreenTrace.value:
        return greenTrace
    elif item_type == ItemType.BunkerTrace.value:
        return bunkerTrace
    elif item_type == ItemType.VegetationTrace.value:
        return vegetationTrace
    elif item_type == ItemType.WaterTrace.value:
        return waterTrace
    elif item_type == ItemType.HoleBoundary.value:
        return holeBoundary
    elif item_type == ItemType.WaterPath.value:
        return waterPath
    elif item_type == ItemType.CartpathTrace.value:
        return cartpathTrace
    elif item_type == ItemType.CartpathPath.value:
        return cartpathPath
    elif item_type == ItemType.LeafyTree.value:
        return leafyTree
    elif item_type == ItemType.ShrubTree.value:
        return shrubTree
    elif item_type == ItemType.PalmTree.value:
        return palmTree
    elif item_type == ItemType.PineTree.value:
        return pineTree
    elif item_type == ItemType.Green.value:
        return green
    elif item_type == ItemType.Approach.value:
        return approach
    elif item_type == ItemType.Tee.value:
        return tee
    else:
        logger.warning(f"Unknown item type: {item_type}")
        return None


def get_marker_scale_size(ax, marker: Marker):
    fig_width, fig_height = ax.figure.get_size_inches()
    fig_area = fig_width * fig_height
    scale_factor = fig_area / base_area
    marker_scaled_size = marker.base_size * scale_factor
    return marker_scaled_size


def get_stripe_scale_factor(ax):
    fig_width, fig_height = ax.figure.get_size_inches()
    fig_area = fig_width * fig_height
    scale_factor = fig_area / base_area
    base_spaces = 10
    stripe_scale_factor = max(1, int(base_spaces * scale_factor))
    logger.info(f"stripe_scale_factor: {stripe_scale_factor}")
    return stripe_scale_factor


def plot_markers(ax, marker: Marker, coords, boundary, zorder=10):
    if coords is None or len(coords) == 0:
        return
    x, y = [], []
    for coord in coords:
        coord_obj = Point(coord)
        if boundary.contains(coord_obj):
            x.append(coord[0])
            y.append(coord[1])
    scaled_size = get_marker_scale_size(ax, marker)
    if marker.style == ItemStyle.ColorFill:
        ax.scatter(
            x,
            y,
            color=marker.color,
            marker=marker.symbol_icon,
            s=scaled_size,
            label=marker.type,
            zorder=zorder,
        )
    elif marker.style == ItemStyle.ImageFill:
        try:
            icon = plt.imread(marker.img_icon)
            for i in range(len(x)):
                imagebox = OffsetImage(icon, zoom=scaled_size)
                ab = AnnotationBbox(
                    imagebox, 
                    (x[i], y[i]), 
                    frameon=False,
                    pad=0,
                    box_alignment=(0.5, 0.5),
                    bboxprops=dict(alpha=1)
                )
                ax.add_artist(ab)
                ab.zorder = zorder
        except Exception as e:
            logger.warning(f"Error plotting image: {e}")
    else:
        logger.warning(f"Unknown marker style: {marker.style}")


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
    (green_data, approach_data, tee_data) = (
        hole.get("greenGPSCoordinate", None),
        hole.get("approachGPSCoordinate", None),
        hole.get("teeGPSCoordinate", None),
    )
    green_coord = (green_data["longitude"], green_data["latitude"]) if green_data else None
    approach_coord = (approach_data["longitude"], approach_data["latitude"]) if approach_data else None
    tee_coord = (tee_data["longitude"], tee_data["latitude"]) if tee_data else None
    markers = []
    if green_coord:
        markers.append((green, [green_coord]))
    if approach_coord:
        markers.append((approach, [approach_coord]))
    if tee_coord:
        markers.append((tee, [tee_coord]))
    hole_boundary = None
    geometries = []
    attributes = []
    # record the hole boundary first
    for gpsItem in hole["gpsItems"]:
        item_type = gpsItem["itemType"]
        item = get_item_by_type(item_type)
        if item == holeBoundary:
            coords = [
                (point["longitude"], point["latitude"]) for point in gpsItem["shape"]
            ]
            hole_boundary = get_smooth_polygon(coords)
            if hole_boundary:
                geometries.append(hole_boundary)
                attributes.append(
                    {"itemType": holeBoundary.type, "color": holeBoundary.color}
                )
            break
    # record the rest of the items, other than hole boundary
    for gpsItem in hole["gpsItems"]:
        item_type = gpsItem["itemType"]
        item = get_item_by_type(item_type)
        if item == holeBoundary:
            continue
        coords = [(point["longitude"], point["latitude"]) for point in gpsItem["shape"]]
        if len(coords) == 0:
            continue
        if isinstance(item, Marker):
            markers.append((item, coords))
        elif isinstance(item, Line):
            coords = [coord for coord in coords if inside_polygon(coord, hole_boundary)]
            if len(coords) > 1:
                geometries.append(LineString(coords))
                attributes.append(
                    {
                        "itemType": item.type,
                        "color": item.color,
                        "lineWidth": item.line_width,
                    }
                )
        else:
            if item_type is None:
                logger.warning(
                    f"item_type not identified, item_type: {item_type}, {debug_info}"
                )
            if len(coords) > 2:
                item_polygon = get_smooth_polygon(coords)
                item_intersection = intersection_of_polygons(item_polygon, hole_boundary)
                if item_intersection and (not item_intersection.is_empty):
                    geometries.append(item_intersection)
                    attributes.append(
                        {"itemType": item.type, "color": item.color}
                    )
    try:
        # check data integrity
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
        if "itemType" not in gdf.columns or hole_boundary is None:
            logger.info(
                f"itemType not in gdf.columns, or hole_boundary is None. {debug_info}"
            )
            return
        # initialize the plot
        bounds = hole_boundary.bounds
        fig_width, fig_height, adjusted_dpi, resolution, center_lat_rad = calculate_pixel_resolution(bounds)
        _, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor="none")
        ax.set_facecolor("none")  # 设置坐标轴区域透明
        ax.spines["top"].set_visible(False)  # 隐藏上边框
        ax.spines["right"].set_visible(False)  # 隐藏右边框
        ax.spines["bottom"].set_visible(False)  # 隐藏下边框
        ax.spines["left"].set_visible(False)  # 隐藏左边框
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        ax.set_aspect(1 / np.cos(center_lat_rad))
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        logger.info(f"Figure size (inches): width={fig_width}, height={fig_height}")
        logger.info(f"Resolution: {resolution:.2f} meters/pixel")
        logger.info(
            f"Final pixels: width={fig_width * adjusted_dpi}, height={fig_height * adjusted_dpi}"
        )

        # plot hole boundary
        hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
        hole_boundary_gdf.plot(
            ax=ax,
            color=holeBoundary.color,
            edgecolor=edge_color,
            linewidth=boarder_width,
        )
        for _, row in gdf.iterrows():
            if isinstance(row.geometry, LineString):
                # plot lines
                x, y = row.geometry.xy
                ax.plot(x, y, color=row["color"], linewidth=row["lineWidth"], zorder=5)
            elif row["itemType"] == greenTrace.type:
                # plot green trace later
                continue
            elif row["itemType"] == fairwayTrace.type:
                # plot fairway trace
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
                # plot polygons
                gpd.GeoSeries([row.geometry]).plot(
                    ax=ax,
                    color=row["color"],
                    edgecolor=edge_color,
                    linewidth=default_width,
                )
        # plot green trace
        green_trace = gdf[gdf["itemType"] == greenTrace.type]
        green_trace.plot(
            ax=ax,
            color=green_trace["color"],
            edgecolor=edge_color,
            linewidth=default_width,
        )
        for marker, coords in markers:
            plot_markers(ax, marker, coords, hole_boundary)

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
        root_dir, "input_data", "golf_course_layout_samples.jsonl"
    )
    output_path = os.path.join(root_dir, "output_data")
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    os.makedirs(output_path, exist_ok=True)
    plot_courses(input_path, output_path)
