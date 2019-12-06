# -*- mode: python -*-

block_cipher = None


a = Analysis(['Cells Database.py'],
             pathex=['/Users/amjad_dabi/PycharmProjects/Updater'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Cells Database',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='cells.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Cells Database')
app = BUNDLE(coll,
             name='Cells Database.app',
             icon='cells.icns',
             bundle_identifier=None)
