from enum import Enum
from utils import root_dir


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
    Green = "Green"
    Approach = "Approach"
    Tee = "Tee"


class Item:
    def __init__(self, type: ItemType, category: ItemCategory, style: ItemStyle, color: str, zorder: int):
        self.type = type
        self.category = category
        self.style = style
        self.color = color
        self.zorder = zorder


class Polygon(Item):
    def __init__(self, type: ItemType, color: str, style: ItemStyle = ItemStyle.TextureFill, zorder: int = 0):
        super().__init__(type, ItemCategory.Polygon, style, color, zorder)
        self.texture = f'{root_dir}/textures/{type.value}.png'


class Line(Item):
    def __init__(self, type: ItemType, color: str, line_width: float = 0.0,
                 style: ItemStyle = ItemStyle.ColorFill, zorder: int = 10):
        super().__init__(type, ItemCategory.Line, style, color, zorder)
        self.texture = f'{root_dir}/textures/{type.value}.png'
        self.line_width = line_width


class Marker(Item):
    def __init__(self, type: ItemType, color: str, symbol_icon: str = None, base_size: int = 40,
                 style: ItemStyle = ItemStyle.ImageFill, zorder: int = 20):
        super().__init__(type, ItemCategory.Marker, style, color, zorder)
        self.symbol_icon = symbol_icon
        self.img_icon = f'{root_dir}/icons/{type.value}.png'
        self.base_size = base_size
