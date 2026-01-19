# -*- mode: python ; coding: utf-8 -*-
# EN: PyInstaller spec file for GT23_Workflow
# CN: GT23_Workflow 的 PyInstaller 打包配置文件
import os
import sys
import glob

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


def _find_mkl_binaries():
    """
    EN: Collect Intel MKL/OpenMP runtime DLLs from the conda env so numpy can unpack safely.
    CN: 从 conda 环境收集 MKL/OpenMP 运行时 DLL，避免 numpy 解包时报缺失。
    """
    root = os.getenv("CONDA_PREFIX", sys.base_prefix)
    bin_dir = os.path.join(root, "Library", "bin")
    patterns = ["mkl_*.dll", "mkl_rt*.dll", "libiomp5md.dll"]
    dlls = []
    for pat in patterns:
        dlls.extend(glob.glob(os.path.join(bin_dir, pat)))
    # Dedup and map to (src, dest)
    return list({dll: (dll, ".") for dll in dlls}.values())


# EN: Bundle MKL/OpenMP binaries to fix "Failed to extract entry: mkl_avx2.2.dll"
# CN: 打包 MKL/OpenMP 运行库，修复 "Failed to extract entry: mkl_avx2.2.dll" 问题
binary_overrides = _find_mkl_binaries()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binary_overrides,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GT23_Workflow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # EN: GUI app (no console) / CN: 图形应用（不显示控制台）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/GT23_Icon.ico',  # EN: Windows exe icon / CN: Windows 可执行文件图标
)

# EN: Output structure:
# CN: 输出结构：
#
# dist/
#   └── GT23_Workflow.exe  (contains: config/, assets/, core/, apps/)
#
# Root directory (user needs to create manually):
# 根目录（用户需要手动创建）：
#   └── photos_in/   (input folder)
#   └── photos_out/  (output folder)
