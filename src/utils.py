import os
import logging
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import Polygon

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
