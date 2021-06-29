# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

added_files = [
    ('res', 'res'),
    ('data', 'data'),
    ('venv/Lib/site-packages/country_list/country_data', 'country_list/country_data'),
    ('venv/Lib/site-packages/pymedphys/_trf/decode/config.json', 'pymedphys/_trf/decode'),
    ('venv/Lib/site-packages/pymedphys/_imports/imports.py', 'pymedphys/_imports')
]

a = Analysis(['main.py'],
             pathex=['venv/Lib/site-packages'],
             binaries=collect_dynamic_libs("rtree"),
             datas=added_files,
             hiddenimports=['scipy.spatial.transform._rotation_groups'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='OnkoDICOM',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='res/images/icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OnkoDICOM')
