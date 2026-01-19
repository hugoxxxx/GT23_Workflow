# -*- coding: utf-8 -*-
"""
EN: Generate a multi-size transparent ICO from PNG for proper Windows taskbar/title bar icons.
CN: 从 PNG 生成多尺寸透明 ICO，确保 Windows 任务栏与标题栏图标清晰正确。

Usage / 用法:
    python apps/make_icon.py

Inputs / 输入:
    assets/GT23_Icon.png  (should have transparent background / 需透明背景)

Outputs / 输出:
    assets/GT23_Icon.ico

Notes / 说明:
- EN: Include multiple sizes (16..256) to cover DPI scaling. Alpha channel is preserved.
- CN: 包含多尺寸(16..256)以适配 DPI 缩放，保留透明通道。
"""

import os
from PIL import Image

SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def make_ico(png_path: str, ico_path: str):
    """
    EN: Convert PNG to ICO with multiple sizes, preserving transparency.
    CN: 将 PNG 转为多尺寸 ICO，保留透明背景。
    """
    if not os.path.exists(png_path):
        raise FileNotFoundError(f"PNG not found: {png_path}")

    img = Image.open(png_path).convert("RGBA")

    # EN: Build resized images for ICO sizes / CN: 生成 ICO 所需各尺寸图像
    resized = []
    for s in SIZES:
        resized.append(img.resize((s, s), Image.LANCZOS))

    # EN: Save ICO with sizes / CN: 保存包含多尺寸的 ICO
    # Pillow accepts 'sizes' with tuples; base image supplies pixel data
    resized[0].save(ico_path, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"[OK] ICO generated: {ico_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)
    png = os.path.join(root_dir, "assets", "GT23_Icon.png")
    ico = os.path.join(root_dir, "assets", "GT23_Icon.ico")
    make_ico(png, ico)
