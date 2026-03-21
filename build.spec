# -*- mode: python ; coding: utf-8 -*-
# EN: PyInstaller spec file for GT23_Workflow
# CN: GT23_Workflow 的 PyInstaller 打包配置文件
import os
import sys
import glob

# EN: Add current directory to path to allow importing version
# CN: 将当前目录添加到路径以允许导入 version 模块
sys.path.append(os.getcwd())
import version

block_cipher = None

# EN: Data files to bundle into exe (config, assets, etc.)
# CN: 需要打包进 exe 的数据文件（配置、资源等）
datas = [
    ('config', 'config'),      # Config files (layouts, films)
    ('assets/libs', 'assets/libs'),  # Keep libs intact
    ('assets/GT23_Icon.ico', 'assets'),  # Include ICO for runtime window icon
    ('assets/GT23_Icon.png', 'assets'),  # Window icon
    # Fonts in use
    ('assets/fonts/consola.ttf', 'assets/fonts'),
    ('assets/fonts/LiquidCrystal-Bold.otf', 'assets/fonts'),
    ('assets/fonts/LED Dot-Matrix1.ttf', 'assets/fonts'),
    ('assets/fonts/intodotmatrix.ttf', 'assets/fonts'),
    ('assets/fonts/palab.ttf', 'assets/fonts'),
    ('assets/fonts/gara.ttf', 'assets/fonts'),
    ('core', 'core'),          # Core modules
    ('apps', 'apps'),          # App modules
]

# EN: Hidden imports (if needed)
# CN: 隐式导入（如果需要）
hiddenimports = []


# EN: Explicitly include python311.dll to prevent "Failed to load Python DLL"
# CN: 显式包含 python311.dll，防止出现“无法加载 Python DLL”的报错
root = os.getenv("CONDA_PREFIX", sys.base_prefix)
binary_overrides = []
python_dll = os.path.join(root, "python311.dll")
if os.path.exists(python_dll):
    binary_overrides.append((python_dll, "."))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binary_overrides,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy', 'pandas', 'PySide6', 'PyQt5', 'PyQt6',
        'IPython', 'notebook', 'jedi', 'psutil', 'pytest', 'sqlite3',
        'libcrypto', 'mkl', 'mkl_rt', 'libiomp5md'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# EN: Manual Binary Filtering - Stripping MKL/OpenMP bloat (150MB+)
# CN: 手动二进制过滤 - 剥离 MKL/OpenMP 冗余（可缩减 150MB+）
a.binaries = [x for x in a.binaries if not any(bloat in x[0].lower() for bloat in ['mkl_', 'libiomp', 'mkl_rt'])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    # a.binaries,  # Manual override if needed
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'GT23_Workflow_{version.get_version_string()}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                 # EN: ENABLE UPX to compress the executable / CN: 开启 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/GT23_Icon.ico',
)

# EN: Output structure:
# CN: 输出结构：
#
# dist/
#   └── GT23_Workflow.exe  (Self-contained single file)
#
# Root directory (user needs to create manually):
# 根目录（用户需要手动创建）：
#   └── photos_in/   (input folder)
#   └── photos_out/  (output folder)
