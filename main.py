# main.py
"""
EN: GT23 Film Workflow - GUI Entry Point
CN: GT23 胶片工作流 - GUI 入口
"""

import sys
import os

# EN: Setup paths for both dev and PyInstaller / CN: 为开发和打包环境设置路径
if getattr(sys, 'frozen', False):
    # EN: Running as PyInstaller exe / CN: 以打包exe运行
    root_path = os.path.dirname(sys.executable)
    sys.path.insert(0, os.path.join(sys._MEIPASS))
else:
    # EN: Running as Python script / CN: 以脚本运行
    root_path = os.path.dirname(os.path.abspath(__file__))
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from gui.main_window import MainWindow


def main():
    """
    EN: Main entry point for GT23 GUI application
    CN: GT23 GUI 应用主入口
    """
    # EN: Enable high DPI scaling / CN: 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    # EN: Create application / CN: 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("GT23 Film Workflow")
    app.setApplicationVersion("2.0.0-alpha.1")
    app.setOrganizationName("GT23")
    
    # EN: Set application style / CN: 设置应用样式
    app.setStyle("Fusion")
    
    # EN: Create and show main window / CN: 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # EN: Run event loop / CN: 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
