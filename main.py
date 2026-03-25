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
    # EN: Detect system language / CN: 检测系统语言
    _lang = detect_system_language()
    ver = get_version_string()
    _title = f"GT23 胶片工作流 {ver}" if _lang == "zh" else f"GT23 Film Workflow {ver}"
    
    # EN: Create application window / CN: 创建应用窗口
    app = ttk.Window(
        title=_title,
        themename="cosmo",
        size=(1400, 1100),
        resizable=(True, True)
    )
    
    # EN: Set window icon (Original PNG only) / CN: 设置窗口图标（仅使用原始 PNG）
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS  # type: ignore[attr-defined]
        elif getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        png_path = os.path.join(base_path, 'assets', 'GT23_Icon.png')
        
        if os.path.exists(png_path):
            try:
                from PIL import Image, ImageTk
                # EN: Let the system handle the original resolution as requested
                # CN: 遵照用户要求，不进行手动缩放，将原图直接交给系统处理
                img_pil = Image.open(png_path)
                img = ImageTk.PhotoImage(img_pil)
                
                # EN: Try multiple protocols for maximum compatibility
                # CN: 尝试多种协议以确保在不同版本的 Tk/Windows 下均能显示
                app.iconphoto(True, img)
                try:
                    app.wm_iconphoto(True, img) # type: ignore[attr-defined]
                except Exception:
                    pass
                
                # EN: Critical - persist reference to avoid GC / CN: 必须保持硬引用防止 GC
                app._icon_photo = img # type: ignore[attr-defined]
                print(f"CN: [✔] 已加载原始图标资产: {os.path.basename(png_path)} ({img_pil.size[0]}x{img_pil.size[1]})")
            except Exception as e:
                print(f"CN: [!] 图标加载失败 (PIL): {e}")
                try:
                    img = tk.PhotoImage(file=png_path)
                    app.iconphoto(True, img)
                    app._icon_photo = img # type: ignore[attr-defined]
                    print(f"CN: [✔] 已加载原始图标资产 (Native): {os.path.basename(png_path)}")
                except Exception as e2:
                    print(f"CN: [!] 图标加载失败 (Native): {e2}")
        else:
            print(f"CN: [!] 未找到图标文件: {png_path}")
    except Exception as e:
        print(f"CN: [!] 图标模块运行异常: {e}")
    
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
