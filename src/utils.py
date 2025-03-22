import os
import logging
from scipy.ndimage import gaussian_filter1d
import numpy as np
from shapely.geometry import Polygon, Point

root_dir = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__))))
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{root_dir}/input_data/golf_course_plotting.log"),
        logging.StreamHandler(),
    ],
)
logger.warning(f"root_dir: {root_dir}")
smooth_sigma = 1
dpi = 300
target_meters_per_pixel = 0.2
lat_to_meter_ratio = 111000
base_area = 10 * 10  # 假设10x10英寸为基准尺寸


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


def calculate_pixel_resolution(west, south, east, north):
    center_lat = (south + north) / 2
    center_lat_rad = np.pi * center_lat / 180
    aspect_ratio = 1 / np.cos(center_lat_rad)
    width_meters = (east - west) * lat_to_meter_ratio * np.cos(center_lat_rad)
    height_meters = (north - south) * lat_to_meter_ratio
    pixels_width = int(width_meters / target_meters_per_pixel)
    pixels_height = int(height_meters / target_meters_per_pixel)
    fig_width = pixels_width / dpi
    fig_height = pixels_height / dpi
    return fig_width, fig_height, dpi, target_meters_per_pixel, aspect_ratio
