# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.utils.hooks.qt import add_qt6_dependencies
from pathlib import Path

vendor_dir = Path('rtmp_client/vendor')
extra_datas = []
if vendor_dir.exists():
    extra_datas.append((str(vendor_dir), 'rtmp_client/vendor'))

qt_plugin_datas = []
qt_plugin_datas += collect_data_files('PySide6', includes=['Qt/plugins/platforms/*'])
qt_plugin_datas += collect_data_files('PySide6', includes=['Qt/plugins/imageformats/*'])
qt_plugin_datas += collect_data_files('PySide6', includes=['Qt/plugins/mediaservice/*'])

a = Analysis(
    ['rtmp_client/__main__.py'],
    pathex=[],
    binaries=[],
    datas=extra_datas + qt_plugin_datas,
    hiddenimports=collect_submodules('PySide6'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

add_qt6_dependencies(a)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RTMP Client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rtmp-client',
)
