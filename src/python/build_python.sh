#!/bin/bash

# 确保在项目根目录下运行 poetry 命令
cd ../..

# 安装依赖
echo "Installing dependencies..."
poetry lock
poetry install --no-root 

# 验证安装
echo "Verifying installations..."
poetry run python -c "
import geopandas
import matplotlib
import pandas
import numpy
import scipy
import shapely
import fiona
import pyproj
import rtree
print('All required packages are installed successfully!')
"

# 回到 python 目录进行构建
cd src/python

poetry lock

# 使用 poetry 环境中的 pyinstaller
poetry run pyinstaller --onefile \
    --hidden-import geopandas \
    --hidden-import matplotlib \
    --hidden-import pandas \
    --hidden-import numpy \
    --hidden-import scipy \
    --hidden-import shapely \
    --hidden-import fiona \
    --hidden-import pyproj \
    --hidden-import rtree \
    --hidden-import pkg_resources.py2_warn \
    --hidden-import pandas._libs.tslibs.base \
    --hidden-import pandas._libs.tslibs.np_datetime \
    --hidden-import pandas._libs.tslibs.timedeltas \
    --add-data "hole_item.py:." \
    --add-data "utils.py:." \
    --add-data "color_manager.py:." \
    --add-data "../../resources:resources" \
    --exclude-module matplotlib.tests \
    --exclude-module pandas.tests \
    --exclude-module scipy.tests \
    --exclude-module shapely.tests \
    --exclude-module fiona.tests \
    --exclude-module pyproj.tests \
    --exclude-module rtree.tests \
    --clean \
    --noupx \
    --optimize=2 \
    plot_courses.py

# 添加调试信息
echo "PyInstaller build completed. Checking output:"
ls -la dist/

# 如果需要，可以添加额外的依赖路径
# poetry run pyinstaller --onefile --paths "$(poetry env info --path)/lib/python3.x/site-packages" plot_courses.py

# 在 src/python 目录下执行
poetry add --group dev pyinstaller