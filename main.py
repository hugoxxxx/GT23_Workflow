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


def main():
    """
    EN: Main function - initialize and run GUI application
    CN: 主程序 - 初始化并运行 GUI 应用程序
    """
    # EN: Detect system language / CN: 检测系统语言
    _lang = detect_system_language()
    _title = "GT23 胶片工作流 v2.0.0" if _lang == "zh" else "GT23 Film Workflow v2.0.0"
    
    # EN: Create application window / CN: 创建应用窗口
    app = ttk.Window(
        title=_title,
        themename="cosmo",  # Modern theme (others: darkly, superhero, solar, cyborg, vapor, journal)
        size=(1100, 1600),  # EN: Further increase window height for preview / CN: 增大窗口高度方便预览
        resizable=(True, True)
    )
    
    # EN: Set window icon (if exists) / CN: 设置窗口图标（如果存在）
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, 'assets', 'GT23_Icon.png')
        if os.path.exists(icon_path):
            app.iconphoto(False, tk.PhotoImage(file=icon_path))
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
    except Exception:
        # EN: Fail silently, not critical / CN: 默认失败，不影响使用
        pass

    # EN: Initialize main window / CN: 初始化主窗口
    MainWindow(app)
    
    # EN: Start event loop / CN: 启动事件循环
    app.mainloop()


if __name__ == "__main__":
    main()
