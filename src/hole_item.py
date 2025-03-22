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
    def __init__(self, type: ItemType, category: ItemCategory, style: ItemStyle = ItemStyle.ColorFill):
        self.type = type
        self.category = category
        self.style = style
        
class Polygon(Item):
    def __init__(self, type: ItemType, color: str, texture: str=None, style: ItemStyle = ItemStyle.ColorFill):
        super().__init__(type, ItemCategory.Polygon, style)
        self.color = color
        self.texture = f'{root_dir}/textures/{texture}.png' if texture else None
        assert style == ItemStyle.ColorFill or self.texture is not None, "TextureFill style requires a texture"
        
class Line(Item):
    def __init__(self, type: ItemType, color: str, texture: str=None, line_width: float=0.0, style: ItemStyle = ItemStyle.ColorFill):
        super().__init__(type, ItemCategory.Line, style)
        self.color = color
        self.texture = f'{root_dir}/textures/{texture}.png' if texture else None
        self.line_width = line_width
        assert style == ItemStyle.ColorFill or self.texture is not None, "TextureFill style requires a texture"

class Marker(Item):
    def __init__(self, type: ItemType, color: str, symbol_icon: str=None, img_icon: str=None, base_size: int=100, style: ItemStyle = ItemStyle.ImageFill):
        super().__init__(type, ItemCategory.Marker, style)
        self.color = color
        self.symbol_icon = symbol_icon
        self.img_icon = f'{root_dir}/icons/{img_icon}.png' if img_icon else None
        self.base_size = base_size
        assert style == ItemStyle.ColorFill or self.img_icon is not None, "ImageFill style requires an image icon"