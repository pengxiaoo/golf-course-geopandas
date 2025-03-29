# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['plot_courses.py'],
    pathex=[],
    binaries=[],
    datas=[('hole_item.py', '.'), ('utils.py', '.'), ('color_manager.py', '.'), ('../../resources', 'resources')],
    hiddenimports=['geopandas', 'matplotlib', 'pandas', 'numpy', 'scipy', 'shapely', 'fiona', 'pyproj', 'rtree', 'pkg_resources.py2_warn', 'pandas._libs.tslibs.base', 'pandas._libs.tslibs.np_datetime', 'pandas._libs.tslibs.timedeltas'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='plot_courses',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
