from enum import Enum
from utils import root_dir
from color_manager import colors

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


line_colors = {
    ItemType.WaterPath: colors.get_color("water_blue"),
    ItemType.CartpathTrace: colors.get_color("cartpath_grey"),
    ItemType.CartpathPath: colors.get_color("cartpath_grey"),
}


class Item:
    def __init__(self, type: ItemType, category: ItemCategory, style: ItemStyle, zorder: int):
        self.type = type
        self.category = category
        self.style = style
        self.zorder = zorder


class Polygon(Item):
    def __init__(self, type: ItemType, style: ItemStyle = ItemStyle.TextureFill, zorder: int = 0):
        super().__init__(type, ItemCategory.Polygon, style, zorder)
        self.texture = f'{root_dir}/resources/textures/{type.value}.png'


class Line(Item):
    def __init__(self, type: ItemType, line_width: float = 0.0,
                 style: ItemStyle = ItemStyle.ColorFill, zorder: int = 10):
        super().__init__(type, ItemCategory.Line, style, zorder)
        self.color = line_colors[type]
        self.line_width = line_width


class Marker(Item):
    def __init__(self, type: ItemType, base_size: int = 40,
                 style: ItemStyle = ItemStyle.ImageFill, zorder: int = 20):
        super().__init__(type, ItemCategory.Marker, style, zorder)
        self.img_icon = f'{root_dir}/resources/icons/{type.value}.png'
        self.base_size = base_size
