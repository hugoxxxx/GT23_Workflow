# main.py
"""
EN: GUI entry point for GT23 Film Workflow (tkinter version)
CN: GT23 胶片工作流 GUI 入口（tkinter版本）
"""

import sys
import os
import ttkbootstrap as ttk
from gui.main_window import MainWindow


def main():
    """
    EN: Main function - initialize and run GUI application
    CN: 主函数 - 初始化并运行 GUI 应用程序
    """
    # EN: Create application window / CN: 创建应用窗口
    app = ttk.Window(
        title="GT23 胶片工作流 Film Workflow v2.0.0",
        themename="cosmo",  # Modern theme (others: darkly, superhero, solar, cyborg, vapor, journal)
        size=(1000, 850),
        resizable=(True, True)
    )
    
    # EN: Set window icon (if exists) / CN: 设置窗口图标（如果存在）
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            app.iconbitmap(icon_path)
    except Exception:
        pass
    
    # EN: Center window on screen / CN: 窗口居中显示
    app.place_window_center()
    
    # EN: Initialize main window / CN: 初始化主窗口
    MainWindow(app)
    
    # EN: Start event loop / CN: 启动事件循环
    app.mainloop()


if __name__ == "__main__":
    main()
