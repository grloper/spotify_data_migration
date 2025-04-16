# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['spotify_migrator.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/*', 'assets/')],
    hiddenimports=[
        'http.server', 
        'urllib.parse', 
        'queue', 
        'html.parser', 
        'json',
        'webbrowser',
        'pkg_resources',
        'spotipy',
        'spotipy.oauth2',
        'spotipy.client',
        'spotipy.cache_handler',
        'spotipy.exceptions'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SpotifyDataMigration',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SpotifyDataMigration',
)