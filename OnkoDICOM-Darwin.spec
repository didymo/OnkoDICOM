# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('src', 'src'),
    ('venv/lib/python/site-packages/country_list/country_data', 'country_list/country_data')
]

a = Analysis(['main.py'],
             pathex=['venv/lib/python/site-packages/'],
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
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
App = BUNDLE(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='OnkoDICOM.app',
		          icon='src/res/images/icon.icns',
		          bundle_identifier=None,
    		      info_plist={
                'NSPrincipalClass': 'NSApplication',
                'NSAppleScriptEnabled': False,
                'CFBundleDocumentTypes': [
                    {
                        'CFBundleTypeName': 'OnkoDICOM',
                        'CFBundleTypeIconFile': 'onkodicom.icns',
                        'CFBundleExecutable': 'OnkoDICOM',
                        'CFBundleTypeRole': 'None',
			'CFBundleShortVersionString': '1.0.0',
                        'LSItemContentTypes': ['au.com.onkodicom'],
                        'LSHandlerRank': 'Owner'
                        }
                    ]
              },
)
