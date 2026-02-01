# -*- coding: utf-8 -*-
"""
EN: GUI entry point for GT23 Film Workflow (tkinter version)
CN: GT23 胶片工作流 GUI 入口（tkinter版本）
"""

import sys
import os
import tkinter as tk
import ttkbootstrap as ttk
from gui.main_window import MainWindow, detect_system_language
from version import get_version_string


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
        themename="darkly",  # EN: High-contrast Darkroom theme / CN: 高对比度暗房主题 (darkly)
        size=(1500, 1350),   # EN: Maximum height for preview clarity / CN: 再次增加高度确保预览完整
        resizable=(True, True)
    )
    
    # EN: Set window icon / CN: 设置窗口图标
    try:
        from utils.paths import get_asset_path
        ico_path = get_asset_path('GT23_Icon.ico')
        png_path = get_asset_path('GT23_Icon.png')

        if os.path.exists(ico_path):
            try:
                app.iconbitmap(default=ico_path)
                app.iconbitmap(ico_path)
            except Exception:
                if os.path.exists(png_path):
                    img = tk.PhotoImage(file=png_path)
                    app.iconphoto(True, img)
        elif os.path.exists(png_path):
            img = tk.PhotoImage(file=png_path)
            app.iconphoto(True, img)
    except Exception:
        pass
    
    # EN: Center window / CN: 居中显示
    app.place_window_center()
    
    # EN: Ensure working folders / CN: 确保工作文件夹
    try:
        from utils.paths import ensure_working_folders
        ensure_working_folders()
    except Exception:
        pass

    # EN: Initialize main window / CN: 初始化主窗口
    MainWindow(app)
    
    # EN: Start event loop / CN: 启动事件循环
    app.mainloop()


if __name__ == "__main__":
    main()
