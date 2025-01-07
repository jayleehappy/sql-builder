# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct

block_cipher = None

# 版本信息
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([
            StringTable(
                u'080404b0',
                [StringStruct(u'CompanyName', u'Your Company'),
                 StringStruct(u'FileDescription', u'SQL构建器'),
                 StringStruct(u'FileVersion', u'1.0.0'),
                 StringStruct(u'InternalName', u'sql_builder'),
                 StringStruct(u'LegalCopyright', u'Copyright (C) 2024'),
                 StringStruct(u'OriginalFilename', u'SQL构建器.exe'),
                 StringStruct(u'ProductName', u'SQL构建器'),
                 StringStruct(u'ProductVersion', u'1.0.0')])
        ]),
        VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
    ]
)

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pandas',
        'openpyxl',
        'numpy',
        'pytz',
        'six',
        'dateutil',
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
    name='SQL构建器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
    version=version_info,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SQL构建器',
) 