import xml.etree.ElementTree as ET

class ColorManager:
    _instance = None
    _colors = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ColorManager, cls).__new__(cls)
            cls._instance._load_colors()
        return cls._instance

    def _load_colors(self):
        tree = ET.parse('colors/colors.xml')
        root = tree.getroot()
        for color in root.findall('color'):
            name = color.get('name')
            value = color.text
            self._colors[name] = value

    def get_color(self, color_name):
        return self._colors.get(color_name)

# 创建一个便捷的访问方法
colors = ColorManager()