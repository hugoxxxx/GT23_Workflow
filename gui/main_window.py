# gui/main_window.py
"""
EN: Main window for GT23 Film Workflow GUI
CN: GT23 胶片工作流主窗口
"""

import os
import sys
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMenuBar, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from gui.panels.border_panel import BorderPanel
from gui.panels.contact_panel import ContactPanel


class MainWindow(QMainWindow):
    """
    EN: Main application window with tabbed interface
    CN: 主应用窗口，包含标签页界面
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GT23 胶片工作流 | Film Workflow")
        self.setMinimumSize(1000, 700)
        
        # EN: Load stylesheet / CN: 加载样式表
        self.load_stylesheet()
        
        # EN: Setup menu bar / CN: 设置菜单栏
        self.setup_menu()
        
        # EN: Create central widget with tabs / CN: 创建带标签页的中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # EN: Create tab widget / CN: 创建标签页组件
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        
        # EN: Add tool panels / CN: 添加工具面板
        self.border_panel = BorderPanel(self)
        self.contact_panel = ContactPanel(self)
        
        tabs.addTab(self.border_panel, "🖼️ 边框工具 Border Tool")
        tabs.addTab(self.contact_panel, "📄 底片索引 Contact Sheet")
        
        layout.addWidget(tabs)
        
        # EN: Center window on screen / CN: 窗口居中显示
        self.center_on_screen()
    
    def load_stylesheet(self):
        """
        EN: Load and apply Qt stylesheet
        CN: 加载并应用 Qt 样式表
        """
        try:
            # EN: Get resources directory / CN: 获取资源目录
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            style_path = os.path.join(base_path, 'gui', 'resources', 'styles.qss')
            
            if os.path.exists(style_path):
                with open(style_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"EN: Failed to load stylesheet: {e} | CN: 样式表加载失败: {e}")
    
    def setup_menu(self):
        """
        EN: Create menu bar
        CN: 创建菜单栏
        """
        menubar = self.menuBar()
        
        # EN: File menu / CN: 文件菜单
        file_menu = menubar.addMenu("文件 File")
        
        open_folder_action = QAction("打开工作目录 Open Folder", self)
        open_folder_action.triggered.connect(self.open_working_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出 Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # EN: Help menu / CN: 帮助菜单
        help_menu = menubar.addMenu("帮助 Help")
        
        about_action = QAction("关于 About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        github_action = QAction("GitHub 仓库", self)
        github_action.triggered.connect(self.open_github)
        help_menu.addAction(github_action)
    
    def open_working_folder(self):
        """
        EN: Open working directory in file explorer
        CN: 在文件管理器中打开工作目录
        """
        try:
            if getattr(sys, 'frozen', False):
                working_dir = os.path.dirname(sys.executable)
            else:
                working_dir = os.getcwd()
            
            os.startfile(working_dir)
        except Exception as e:
            QMessageBox.warning(self, "错误 Error", f"无法打开目录 Failed to open folder: {e}")
    
    def show_about(self):
        """
        EN: Show about dialog
        CN: 显示关于对话框
        """
        about_text = """
<h2>GT23 胶片工作流 Film Workflow</h2>
<p><b>版本 Version:</b> 2.0.0-alpha.1</p>
<p><b>作者 Author:</b> Hugo</p>
<p><b>邮箱 Email:</b> xjames007@gmail.com</p>
<br>
<p>EN: A dedicated tool for film photographers to generate digital contact sheets and professionally processed film borders.</p>
<p>CN: 专为胶片摄影师设计的数字接触印样与底片边框处理工具。</p>
<br>
<p>Inspired by Contax G2 & T3 📷</p>
        """
        QMessageBox.about(self, "关于 About GT23", about_text)
    
    def open_github(self):
        """
        EN: Open GitHub repository in browser
        CN: 在浏览器中打开 GitHub 仓库
        """
        import webbrowser
        webbrowser.open("https://github.com/hugoxxxx/GT23_Workflow")
    
    def center_on_screen(self):
        """
        EN: Center the window on the screen
        CN: 将窗口在屏幕上居中
        """
        from PySide6.QtGui import QScreen
        screen = QScreen.availableGeometry(self.screen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
