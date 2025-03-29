import argparse
import os
import json
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import Point, LineString, Polygon as ShapelyPolygon
from hole_item import Item, ItemType, Polygon, Line, Marker
from utils import logger
import utils
import numpy as np


class Resources:
    def __init__(self, resources_dir):
        # polygons
        self.teeboxTrace = Polygon(resources_dir, ItemType.TeeboxTrace, zorder=9)
        self.fairwayTrace = Polygon(resources_dir, ItemType.FairwayTrace, zorder=2)
        self.greenTrace = Polygon(resources_dir, ItemType.GreenTrace, zorder=9)
        self.bunkerTrace = Polygon(resources_dir, ItemType.BunkerTrace, zorder=1)
        self.vegetationTrace = Polygon(resources_dir, ItemType.VegetationTrace, zorder=1)
        self.waterTrace = Polygon(resources_dir, ItemType.WaterTrace, zorder=1)
        self.holeBoundary = Polygon(resources_dir, ItemType.HoleBoundary, zorder=0)

        # lines
        self.waterPath = Line(resources_dir, ItemType.WaterPath, line_width=1.0)
        self.cartpathTrace = Line(resources_dir, ItemType.CartpathTrace, line_width=0.5, zorder=11)
        self.cartpathPath = Line(resources_dir, ItemType.CartpathPath, line_width=0.5, zorder=12)

        # markers
        self.leafyTree = Marker(resources_dir, ItemType.LeafyTree)
        self.shrubTree = Marker(resources_dir, ItemType.ShrubTree)
        self.palmTree = Marker(resources_dir, ItemType.PalmTree)
        self.pineTree = Marker(resources_dir, ItemType.PineTree)


def create_parser():
    parser = argparse.ArgumentParser(description="Hole skin changer")
    parser.add_argument("--root-data-dir", help="Root data directory")
    return parser


def get_item_by_type(item_type: ItemType, resources: Resources):
    if item_type == ItemType.TeeboxTrace.value:
        return resources.teeboxTrace
    elif item_type == ItemType.FairwayTrace.value:
        return resources.fairwayTrace
    elif item_type == ItemType.GreenTrace.value:
        return resources.greenTrace
    elif item_type == ItemType.BunkerTrace.value:
        return resources.bunkerTrace
    elif item_type == ItemType.VegetationTrace.value:
        return resources.vegetationTrace
    elif item_type == ItemType.WaterTrace.value:
        return resources.waterTrace
    elif item_type == ItemType.HoleBoundary.value:
        return resources.holeBoundary
    elif item_type == ItemType.WaterPath.value:
        return resources.waterPath
    elif item_type == ItemType.CartpathTrace.value:
        return resources.cartpathTrace
    elif item_type == ItemType.CartpathPath.value:
        return resources.cartpathPath
    elif item_type == ItemType.LeafyTree.value:
        return resources.leafyTree
    elif item_type == ItemType.ShrubTree.value:
        return resources.shrubTree
    elif item_type == ItemType.PalmTree.value:
        return resources.palmTree
    elif item_type == ItemType.PineTree.value:
        return resources.pineTree
    else:
        logger.warning(f"Unknown item type: {item_type}")
        return None


def plot_marker(ax, marker: Marker, marker_pixels, coords, boundary):
    if coords is None or len(coords) == 0:
        return
    logger.info(f"Plotting marker: {marker.type} with style: {marker.style}, marker_pixels: {marker_pixels}")
    x, y = [], []
    for coord in coords:
        coord_obj = Point(coord)
        if boundary.contains(coord_obj):
            x.append(coord[0])
            y.append(coord[1])
    try:
        icon = plt.imread(marker.img_icon)
        for i in range(len(x)):
            zoom = marker_pixels / utils.marker_icon_pixels
            imagebox = OffsetImage(icon, zoom=zoom)
            ab = AnnotationBbox(
                imagebox,
                (x[i], y[i]),
                frameon=False,
                pad=0,
                box_alignment=(0.5, 0.5),
                bboxprops=dict(alpha=1)
            )
            ax.add_artist(ab)
            ab.zorder = marker.zorder
    except Exception as e:
        logger.warning(f"Error plotting image: {e}, marker.type: {marker.type}")


def plot_polygon(ax, geo_series: gpd.GeoSeries, item: Item, alpha=1.0):
    try:
        texture_img = plt.imread(item.texture)
        bounds = geo_series.total_bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        # 创建平铺纹理
        # 设置纹理基础大小（在经纬度坐标系中）
        base_size = min(width, height) * 0.1  # 纹理基础大小为区域最小边长的10%
        # 计算需要多少个纹理来覆盖整个区域
        nx = int(np.ceil(width / base_size))
        ny = int(np.ceil(height / base_size))
        # 创建裁剪路径
        polygon = geo_series.iloc[0]
        coords = polygon.exterior.coords
        path = Path(coords)
        patch = PathPatch(path, facecolor='none', edgecolor='none')
        ax.add_patch(patch)
        # 为每个网格创建纹理
        for i in range(nx):
            for j in range(ny):
                x = bounds[0] + i * base_size
                y = bounds[1] + j * base_size
                ax.imshow(texture_img,
                    extent=[x, x + base_size, y, y + base_size],
                    alpha=0.7,
                    zorder=item.zorder,
                    aspect='auto',
                    interpolation='bilinear',
                    clip_path=patch)
        # 绘制多边形边界
        geo_series.plot(
            ax=ax,
            facecolor='none',
            zorder=item.zorder,
            linewidth=0,
        )
    except Exception as e:
        logger.error(f"Error in texture plotting: {str(e)}")
        logger.error(f"Error details: {e.__class__.__name__}")


def plot_course(club_id, course_id, hole_number, holes, output_folder_path, resources):
    debug_info = f"clubId: {club_id}, courseId: {course_id}, holeNumber: {hole_number}"
    hole = holes[hole_number - 1]
    hole_boundary = None
    geometries = []
    attributes = []
    markers = []
    # record the hole boundary first
    for gpsItem in hole["gpsItems"]:
        item_type = gpsItem["itemType"]
        item = get_item_by_type(item_type, resources)
        if item == resources.holeBoundary:
            coords = [
                (point["longitude"], point["latitude"]) for point in gpsItem["shape"]
            ]
            hole_boundary = utils.get_smooth_polygon(coords)
            if hole_boundary:
                geometries.append(hole_boundary)
                attributes.append(
                    {"itemType": resources.holeBoundary.type}
                )
            break
    # record the rest of the items, other than hole boundary
    for gpsItem in hole["gpsItems"]:
        item_type = gpsItem["itemType"]
        item = get_item_by_type(item_type, resources)
        if item == resources.holeBoundary:
            continue
        coords = [(point["longitude"], point["latitude"]) for point in gpsItem["shape"]]
        if len(coords) == 0:
            continue
        if isinstance(item, Marker):
            markers.append((item, coords))
        elif isinstance(item, Line):
            coords = [coord for coord in coords if utils.inside_polygon(coord, hole_boundary)]
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
                item_polygon = utils.get_smooth_polygon(coords)
                item_intersection = utils.intersection_of_polygons(item_polygon, hole_boundary)
                if item_intersection and (not item_intersection.is_empty):
                    geometries.append(item_intersection)
                    attributes.append(
                        {"itemType": item.type}
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
        fig_width, fig_height, adjusted_dpi, aspect_ratio, marker_pixels = utils.calculate_pixel_resolution(
            *hole_boundary.bounds)
        _, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor="none")
        ax.set_facecolor("none")  # 设置坐标轴区域透明
        ax.spines["top"].set_visible(False)  # 隐藏上边框
        ax.spines["right"].set_visible(False)  # 隐藏右边框
        ax.spines["bottom"].set_visible(False)  # 隐藏下边框
        ax.spines["left"].set_visible(False)  # 隐藏左边框
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(hole_boundary.bounds[0], hole_boundary.bounds[2])
        ax.set_ylim(hole_boundary.bounds[1], hole_boundary.bounds[3])
        ax.set_aspect(aspect_ratio)
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        logger.info(f"Figure size (inches): width={fig_width}, height={fig_height}")
        logger.info(
            f"Final pixels: width={fig_width * adjusted_dpi}, height={fig_height * adjusted_dpi}"
        )

        # plot hole boundary
        hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
        plot_polygon(ax, hole_boundary_gdf, resources.holeBoundary)
        # plot items inside hole boundary
        for _, row in gdf.iterrows():
            item = get_item_by_type(row["itemType"].value, resources)
            if isinstance(row.geometry, LineString):
                x, y = row.geometry.xy
                ax.plot(x, y, color=row["color"], linewidth=row["lineWidth"], zorder=item.zorder)
            elif isinstance(row.geometry, ShapelyPolygon):
                polygon_trace = gpd.GeoSeries([row.geometry])
                plot_polygon(ax, polygon_trace, item)
        for marker, coords in markers:
            plot_marker(ax, marker, marker_pixels, coords, hole_boundary)

        plt.savefig(
            f"{output_folder_path}/{club_id}_{course_id}_{hole_number}.png",
            dpi=adjusted_dpi,
            format="png",
            bbox_inches="tight",
            pad_inches=0,
            transparent=True,
        )
        print(f"Generated image: {output_folder_path}/{club_id}_{course_id}_{hole_number}.png", flush=True)
    except Exception as e:
        logger.error(f"Exception: {e}, {debug_info}")
    finally:
        plt.close("all")


def plot_courses(input_jsonl_file_path, resources_dir, output_folder_path):
    resources = Resources(resources_dir)
    with open(input_jsonl_file_path, "r", newline="", encoding="utf-8") as file:
        for line in file:
            data = json.loads(line)
            club_id = data["clubId"]
            course_id = data["courseId"]
            holes = data["holes"]
            hole_count = len(holes)
            # todo: for now only plot the first hole. update this later.
            for hole_number in range(1, hole_count + 1):
                plot_course(club_id, course_id, hole_number, holes, output_folder_path, resources)


if __name__ == "__main__":
    parser = create_parser()
    args, _ = parser.parse_known_args()
    root_data_dir = args.root_data_dir
    input_path = os.path.join(args.root_data_dir, "input_data", "golf_course_layout_samples.jsonl")
    output_path = os.path.join(args.root_data_dir, "output_data")
    resources_dir = os.path.join(args.root_data_dir, "resources")
    os.makedirs(output_path, exist_ok=True)
    plot_courses(input_path, resources_dir, output_path)
