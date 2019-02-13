# -*- mode: python -*-

block_cipher = None
from kivy.deps import sdl2, glew

a = Analysis(['src\\print_label.py'],
             pathex=['C:\\Users\\pale\\Documents\\AeN_print'],
             binaries=[],
             datas=[('src/Images', 'Images')],
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

a.datas += [('label.kv', 'src/label.kv','DATA')]
 
exe = EXE(pyz, Tree('src/Images', 'Images'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='print_label',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='src/Images/data_matrix.ico')
