# -*- coding: utf-8 -*-
"""
EN: GUI entry point for GT23 Film Workflow (tkinter version)
CN: GT23 胶片工作流 GUI 入口（tkinter版本）
"""

import sys
import os
import tkinter as tk
import ttkbootstrap as ttk
import shutil
from gui.main_window import MainWindow, detect_system_language
from version import get_version_string
from core.renderer import bootstrap_logos
from utils.config_manager import config_manager


def main():
    """
    EN: Main function - initialize and run GUI application
    CN: 主程序 - 初始化并运行 GUI 应用程序
    """
    # EN: Enable DPI Awareness for high-resolution displays (Windows only)
    # CN: 针对高分辨率屏幕启用 DPI 感知（仅限 Windows），防止图标与文字模糊
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            from ctypes import windll
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # EN: Detect system language / CN: 检测系统语言
    _lang = detect_system_language()
    ver = get_version_string()
    _title = f"GT23 胶片工作流 {ver}" if _lang == "zh" else f"GT23 Film Workflow {ver}"
    
    # EN: Create application window / CN: 创建应用窗口
    app = ttk.Window(
        title=_title,
        themename="cosmo",  # Modern theme
        size=(1400, 1100),   # EN: Default window size
        resizable=(True, True)
    )
    
    # EN: Set window icon (if exists) / CN: 设置窗口图标（如果存在）
    try:
        # EN: Resolve asset base (supports PyInstaller onefile via _MEIPASS)
        # CN: 解析资源基础路径（支持 PyInstaller 单文件的 _MEIPASS 目录）
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS  # type: ignore[attr-defined]
        elif getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        ico_path = os.path.join(base_path, 'assets', 'GT23_Icon.ico')
        png_path = os.path.join(base_path, 'assets', 'GT23_Icon.png')

        # EN: Set both iconbitmap (classic Win) and iconphoto (modern HIDPI)
        # CN: 同时设置 iconbitmap (适配经典任务栏) 和 iconphoto (适配现代高分屏标题栏)
        if os.path.exists(ico_path):
            try:
                # EN: Method 1: Classic Win32 icon mapping
                app.iconbitmap(default=ico_path)
                app.iconbitmap(ico_path)
            except Exception:
                pass
        
        if os.path.exists(png_path):
            try:
                # EN: Method 2: Multi-size icon stack for titlebar and high-DPI
                # CN: 多尺度图标栈：提供全套尺寸，确保高分屏下的像素级清晰度
                from PIL import Image, ImageTk
                img_pil = Image.open(png_path).convert("RGBA")
                icon_sizes = [16, 32, 48, 64, 128, 256]
                
                # EN: Keep references to avoid garbage collection / CN: 必须保留引用防止 GC
                app._icon_photos = [] # type: ignore[attr-defined]
                for s in icon_sizes:
                    resized = img_pil.resize((s, s), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized)
                    app._icon_photos.append(photo) # type: ignore[attr-defined]
                
                # EN: Apply the best match for each context / CN: 应用最佳匹配
                app.iconphoto(True, *app._icon_photos) # type: ignore[attr-defined]
            except Exception:
                try:
                    photo = tk.PhotoImage(file=png_path)
                    app.iconphoto(True, photo)
                    app._icon_photo = photo # type: ignore[attr-defined]
                except Exception:
                    pass
    except Exception:
        # EN: Icon loading failed, continue without icon (silent fail is OK)
        # CN: 图标加载失败，不中止程序，默认失败可接受
        pass
    
    # EN: Center window on screen / CN: 居中显示窗口
    app.place_window_center()
    
    # EN: Ensure working folders exist / CN: 确保工作文件夹存在
    try:
        if getattr(sys, 'frozen', False):
            working_dir = os.path.dirname(sys.executable)
        else:
            working_dir = os.getcwd()

        photos_in = os.path.join(working_dir, 'photos_in')
        photos_out = os.path.join(working_dir, 'photos_out')
        os.makedirs(photos_in, exist_ok=True)
        os.makedirs(photos_out, exist_ok=True)
        
        # EN: Bootstrap logos early / CN: 尽早引导并释放 Logo 资源
        bootstrap_logos()
        # EN: Bootstrap configs / CN: 引导并释放默认配置文件
        bootstrap_configs()
    except Exception:
        # EN: Fail silently, not critical / CN: 默认失败，不影响使用
        pass

    # EN: Initialize main window / CN: 初始化主窗口
    MainWindow(app)
    
    # EN: Start event loop / CN: 启动事件循环
    app.mainloop()


def bootstrap_configs():
    """
    EN: Export internal config JSONs to GT23_Assets/config on the first run.
    CN: 首次运行时，将内置配置 JSON 释放到 GT23_Assets/config 目录。
    """
    # 1. EN: Determine external config dir / CN: 确定外部配置目录
    ext_config_dir = config_manager.get_managed_path("config")
    os.makedirs(ext_config_dir, exist_ok=True)
    
    # 2. EN: Determine internal source dir / CN: 确定内部源目录
    if getattr(sys, 'frozen', False):
        int_base = sys._MEIPASS
    else:
        # main.py is in root
        int_base = os.path.dirname(os.path.abspath(__file__))
    
    int_config_dir = os.path.join(int_base, "config")
    
    # 3. EN: Export missing files / CN: 释放缺失的文件
    exported = []
    for filename in ['layouts.json', 'films.json', 'contact_layouts.json']:
        src = os.path.join(int_config_dir, filename)
        dst = os.path.join(ext_config_dir, filename)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copy2(src, dst)
                exported.append(filename)
            except Exception:
                pass
    
    if exported:
        print(f"CN: [✔] 已释放默认配置到 GT23_Assets/config: {', '.join(exported)}")

if __name__ == "__main__":
    main()
