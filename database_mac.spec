# -*- mode: python -*-

block_cipher = None


a = Analysis(['Cells Database.py'],
             pathex=['/Users/amjad_dabi/Google Drive/Python Projects/Database'],
             binaries=[],
             datas=[],
             hiddenimports=['numpy.random.common'],
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
          name='Cells Database',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
app = BUNDLE(exe,
             name='Cells Database.app',
             icon='Cells.icns',
             bundle_identifier=None,
			 info_plist={
            	'NSHighResolutionCapable': 'True'
                 },
	    	 )
