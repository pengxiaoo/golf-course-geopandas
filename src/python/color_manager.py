import xml.etree.ElementTree as ET
import os
import sys

class ColorManager:
    _instance = None
    _colors = {}
    _resources_dir = None

    def __new__(cls, resources_dir=None):
        if cls._instance is None:
            cls._instance = super(ColorManager, cls).__new__(cls)
            cls._instance._resources_dir = resources_dir
            cls._instance._load_colors()
        return cls._instance

    def _load_colors(self):
        # 如果提供了 resources_dir，使用它
        if self._resources_dir:
            resource_path = self._resources_dir
        else:
            resource_path = self._get_resource_path()
            
        tree = ET.parse(f'{resource_path}/colors.xml')
        root = tree.getroot()
        for color in root.findall('color'):
            name = color.get('name')
            value = color.text
            self._colors[name] = value

    def get_color(self, color_name):
        return self._colors.get(color_name)

    def _get_resource_path(self):
        # 判断是否是 PyInstaller 打包的环境
        if getattr(sys, 'frozen', False):
            # 如果是打包环境，使用 _MEIPASS
            base_path = sys._MEIPASS
        else:
            # 如果是开发环境，使用相对路径
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(base_path, 'resources')
