# -*- mode: python -*-

block_cipher = None


a = Analysis(['/Users/amjad_dabi/Google Drive/Python Projects/Database/updater_source/updater.py'],
             pathex=['/Users/amjad_dabi/Google Drive/Python Projects/Database'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='updater',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='updater.app',
             icon=None,
             bundle_identifier=None)
