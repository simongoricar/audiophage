# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Device lister
listdevices_a = Analysis(['list-audio-devices.py'],
                         pathex=[],
                         binaries=[],
                         datas=[],
                         hiddenimports=[],
                         hookspath=[],
                         hooksconfig={},
                         runtime_hooks=[],
                         excludes=[],
                         win_no_prefer_redirects=False,
                         win_private_assemblies=False,
                         cipher=block_cipher,
                         noarchive=False)

listdevices_pyz = PYZ(listdevices_a.pure, listdevices_a.zipped_data,
                      cipher=block_cipher)

listdevices_exe = EXE(listdevices_pyz,
                      listdevices_a.scripts,
                      [],
                      exclude_binaries=True,
                      name='list-audio-devices',
                      debug=False,
                      bootloader_ignore_signals=False,
                      strip=False,
                      upx=True,
                      console=True,
                      disable_windowed_traceback=False,
                      target_arch=None,
                      codesign_identity=None,
                      entitlements_file=None)

# Audiophage streamer
stream_a = Analysis(['stream.py'],
                    pathex=[],
                    binaries=[
                        ("./.venv/Lib/site-packages/discord/bin/libopus-0.x64.dll", "libs")
                    ],
                    datas=[
                        ("data/configuration.TEMPLATE.toml", "data"),
                    ],
                    hiddenimports=[
                        # "nacl",
                        # "nacl.secret",
                        # "nacl.utils",
                        "_cffi_backend",
                    ],
                    hookspath=[],
                    hooksconfig={},
                    runtime_hooks=[],
                    excludes=[],
                    win_no_prefer_redirects=False,
                    win_private_assemblies=False,
                    cipher=block_cipher,
                    noarchive=False)

stream_pyz = PYZ(stream_a.pure, stream_a.zipped_data,
                 cipher=block_cipher)

stream_exe = EXE(stream_pyz,
                 stream_a.scripts,
                 [],
                 exclude_binaries=True,
                 name='audiophage',
                 debug=False,
                 bootloader_ignore_signals=False,
                 strip=False,
                 upx=True,
                 console=True,
                 disable_windowed_traceback=False,
                 target_arch=None,
                 codesign_identity=None,
                 entitlements_file=None)

# Final
coll = COLLECT(stream_exe,
               stream_a.binaries,
               stream_a.zipfiles,
               stream_a.datas,
               listdevices_exe,
               listdevices_a.binaries,
               listdevices_a.zipfiles,
               listdevices_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='audiophage')
