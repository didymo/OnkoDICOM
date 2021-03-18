# -*- mode: python ; coding: utf-8 -*-

import glob
import logging

block_cipher = None

# Search the numpy .libs directory for the libopenblas .dll file.
libopenblas_dll = glob.glob("venv/Lib/site-packages/numpy/.libs/*.dll")[0]
logging.info("Found libopenblas dll: " + libopenblas_dll)

added_files = [
    ('src', 'src'),
    ('venv/Lib/site-packages/country_list/country_data', 'country_list/country_data'),
    ('venv/Lib/site-packages/pymedphys/_trf/decode/config.json', 'pymedphys/_trf/decode'),
    ('venv/Lib/site-packages/pymedphys/_imports/imports.py', 'pymedphys/_imports')
]

a = Analysis(['main.py'],
             pathex=['venv/Lib/site-packages'],
             binaries=[(libopenblas_dll, '.')],
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
          console=False , icon='src/res/images/icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OnkoDICOM')
