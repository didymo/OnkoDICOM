# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('src', 'src'),
    ('venv/Lib/site-packages/country_list/country_data', 'country_list/country_data')
]

a = Analysis(['main.py'],
             pathex=['venv/Lib/site-packages'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
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
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True , icon='src/res/images/icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OnkoDICOM')
