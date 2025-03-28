import sys
import os
from enum import Enum

# 添加当前目录到 Python 路径
if getattr(sys, 'frozen', False):
    # 如果是打包环境
    module_dir = sys._MEIPASS
else:
    # 如果是开发环境
    module_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(module_dir)

from color_manager import ColorManager

class ItemCategory(Enum):
    Polygon = "Polygon"
    Line = "Line"
    Marker = "Marker"


class ItemStyle(Enum):
    ColorFill = "ColorFill"
    TextureFill = "TextureFill"
    ImageFill = "ImageFill"


class ItemType(Enum):
    # polygons
    TeeboxTrace = "TeeboxTrace"
    FairwayTrace = "FairwayTrace"
    GreenTrace = "GreenTrace"
    BunkerTrace = "BunkerTrace"
    VegetationTrace = "VegetationTrace"
    WaterTrace = "WaterTrace"
    HoleBoundary = "HoleBoundary"
    # lines
    WaterPath = "WaterPath"
    CartpathTrace = "CartpathTrace"
    CartpathPath = "CartpathPath"
    # markers
    LeafyTree = "LeafyTree"
    ShrubTree = "ShrubTree"
    PalmTree = "PalmTree"
    PineTree = "PineTree"


class Item:
    def __init__(self, resources_dir, type: ItemType, category: ItemCategory, style: ItemStyle, zorder: int):
        self.resources_dir = resources_dir
        self.type = type
        self.category = category
        self.style = style
        self.zorder = zorder


class Polygon(Item):
    def __init__(self, resources_dir, type: ItemType, style: ItemStyle = ItemStyle.TextureFill, zorder: int = 0):
        super().__init__(resources_dir, type, ItemCategory.Polygon, style, zorder)
        self.texture = f'{resources_dir}/textures/{type.value}.png'


class Line(Item):

    def __init__(self, resources_dir: str, type: ItemType, line_width: float = 0.0,
                 style: ItemStyle = ItemStyle.ColorFill, zorder: int = 10):
        super().__init__(resources_dir, type, ItemCategory.Line, style, zorder)
        colors = ColorManager(resources_dir)
        line_colors = {
            ItemType.WaterPath: colors.get_color("water_blue"),
            ItemType.CartpathTrace: colors.get_color("cartpath_grey"),
            ItemType.CartpathPath: colors.get_color("cartpath_grey"),
        }
        self.color = line_colors[type]
        self.line_width = line_width


class Marker(Item):
    def __init__(self, resources_dir: str, type: ItemType, base_size: int = 40,
                 style: ItemStyle = ItemStyle.ImageFill, zorder: int = 20):
        super().__init__(resources_dir, type, ItemCategory.Marker, style, zorder)
        self.img_icon = f'{resources_dir}/icons/{type.value}.png'
        self.base_size = base_size
