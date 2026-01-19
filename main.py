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
        themename="cosmo",  # Modern theme (others: darkly, superhero, solar, cyborg, vapor, journal)
        size=(1100, 1600),  # EN: Further increase window height for preview / CN: 增大窗口高度方便预览
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

        # EN: Prefer .ico on Windows for title bar + taskbar
        # CN: Windows 上优先使用 .ico，能同时影响标题栏与任务栏
        if os.path.exists(ico_path):
            try:
                # EN: Try multiple Tk variants for reliability on Windows
                # CN: 兼容性处理：尝试多种 Tk 设置方式，提升在 Windows 上的成功率
                app.iconbitmap(default=ico_path)
                app.iconbitmap(ico_path)
                try:
                    app.wm_iconbitmap(ico_path)  # type: ignore[attr-defined]
                except Exception:
                    pass
            except Exception:
                # EN: Fallback to PNG with iconphoto
                # CN: 回退到使用 PNG 的 iconphoto
                if os.path.exists(png_path):
                    img = tk.PhotoImage(file=png_path)
                    app.iconphoto(True, img)
                    app.iconphoto(False, img)
        elif os.path.exists(png_path):
            # EN: Non-Windows or missing .ico → use PNG
            # CN: 非 Windows 或无 .ico 时使用 PNG
            img = tk.PhotoImage(file=png_path)
            app.iconphoto(True, img)
            app.iconphoto(False, img)
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
