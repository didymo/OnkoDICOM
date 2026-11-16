# -*- mode: python ; coding: utf-8 -*-
# macOS (Apple silicon) app bundle. Build from the project environment:  uv run pyinstaller --noconfirm OnkoDICOM-Darwin.spec
# Package data is found through PyInstaller's helpers, so no site-packages path is written here: whatever environment
# runs PyInstaller is the one bundled.
import tomllib

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

with open('pyproject.toml', 'rb') as f:
    VERSION = tomllib.load(f)['project']['version']

block_cipher = None

added_files = [
    ('res', 'res'),
    ('data', 'data'),
    *collect_data_files('country_list'),
    *collect_data_files('pymedphys', includes=['_trf/decode/config.json']),
    *collect_data_files('pymedphys', include_py_files=True, includes=['_imports/imports.py']),
    # imblearn reads VERSION.txt on import.
    *collect_data_files('imblearn'),
    # pyradiomics validates its parameters against schemas/paramSchema.yaml, with schemaFuncs.py loaded by path.
    *collect_data_files('radiomics', include_py_files=True, subdir='schemas'),
]

a = Analysis(['main.py'],
             pathex=[],
             binaries=collect_dynamic_libs("rtree"),
             datas=added_files,
             hiddenimports=['scipy.spatial.transform._rotation_groups'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          upx=False,
          console=False,
          target_arch='arm64')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='OnkoDICOM')
app = BUNDLE(coll,
             name='OnkoDICOM.app',
             icon='res/images/icon.icns',
             bundle_identifier=None,
             version=VERSION,
             info_plist={
                 'NSPrincipalClass': 'NSApplication',
                 'NSAppleScriptEnabled': False,
                 'NSHighResolutionCapable': True,
                 'LSMinimumSystemVersion': '15.0',
             },
)
