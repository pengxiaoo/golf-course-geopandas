import xml.etree.ElementTree as ET

class ColorManager:
    _instance = None
    _colors = {}

    def __new__(cls, resource_path):
        if cls._instance is None:
            cls._instance = super(ColorManager, cls).__new__(cls)
            cls._instance._load_colors(resource_path)
        return cls._instance

    def _load_colors(self, resource_path):
        tree = ET.parse(f'{resource_path}/colors.xml')
        root = tree.getroot()
        for color in root.findall('color'):
            name = color.get('name')
            value = color.text
            self._colors[name] = value

    def get_color(self, color_name):
        return self._colors.get(color_name)
