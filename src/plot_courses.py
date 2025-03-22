import os
import json
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import Point, LineString, Polygon as ShapelyPolygon
from hole_item import Item, ItemType, ItemStyle, Polygon, Line, Marker
from utils import logger, root_dir
import utils
import numpy as np

base_area = 10 * 10  # 假设10x10英寸为基准尺寸

# polygons
teeboxTrace = Polygon(ItemType.TeeboxTrace, "lawngreen", zorder=9)
fairwayTrace = Polygon(ItemType.FairwayTrace, "lawngreen", texture="fairway", style=ItemStyle.TextureFill, zorder=2)
greenTrace = Polygon(ItemType.GreenTrace, "lawngreen", zorder=9)
bunkerTrace = Polygon(ItemType.BunkerTrace, "yellow", zorder=1)
vegetationTrace = Polygon(ItemType.VegetationTrace, "seagreen", zorder=1)
waterTrace = Polygon(ItemType.WaterTrace, "skyblue", zorder=1)
holeBoundary = Polygon(ItemType.HoleBoundary, "forestgreen")
# lines
waterPath = Line(ItemType.WaterPath, "skyblue", line_width=2.0)
cartpathTrace = Line(ItemType.CartpathTrace, "lightgrey", line_width=0.5, zorder=11)
cartpathPath = Line(ItemType.CartpathPath, "lightgrey", line_width=0.5, zorder=12)
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


def plot_markers(ax, marker: Marker, coords, boundary):
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
            zorder=marker.zorder,
        )
    elif marker.style == ItemStyle.ImageFill:
        try:
            # todo: fix bugs here
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
                ab.zorder = marker.zorder
        except Exception as e:
            logger.warning(f"Error plotting image: {e}")
    else:
        logger.warning(f"Unknown marker style: {marker.style}")


def plot_polygon(ax, geo_series: gpd.GeoSeries, item: Item, alpha=1.0):
    if item.style == ItemStyle.ColorFill:
        geo_series.plot(
            ax=ax,
            color=item.color,
            alpha=alpha,
            zorder=item.zorder,
        )
    elif item.style == ItemStyle.TextureFill:
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
                    img = ax.imshow(texture_img,
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
            # 如果纹理加载失败,回退到纯色填充
            geo_series.plot(
                ax=ax,
                color=item.color,
                alpha=alpha,
                zorder=item.zorder,
            )
    else:
        logger.warning(f"Unknown polygon style: {item.style}")


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
            hole_boundary = utils.get_smooth_polygon(coords)
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
        fig_width, fig_height, adjusted_dpi, resolution, aspect_ratio = utils.calculate_pixel_resolution(
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
        logger.info(f"Resolution: {resolution:.2f} meters/pixel")
        logger.info(
            f"Final pixels: width={fig_width * adjusted_dpi}, height={fig_height * adjusted_dpi}"
        )

        # plot hole boundary
        hole_boundary_gdf = gpd.GeoDataFrame(geometry=[hole_boundary], crs=gdf.crs)
        plot_polygon(ax, hole_boundary_gdf, holeBoundary)
        # plot items inside hole boundary
        for _, row in gdf.iterrows():
            item = get_item_by_type(row["itemType"].value)
            if isinstance(row.geometry, LineString):
                x, y = row.geometry.xy
                ax.plot(x, y, color=row["color"], linewidth=row["lineWidth"], zorder=item.zorder)
            elif isinstance(row.geometry, ShapelyPolygon):
                polygon_trace = gpd.GeoSeries([row.geometry])
                plot_polygon(ax, polygon_trace, item)
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
        logger.error(f"Exception: {e}, {debug_info}")
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
