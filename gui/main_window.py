# gui/main_window.py
"""
EN: Main window for GT23 Film Workflow GUI (tkinter version)
CN: GT23 胶片工作流主窗口（tkinter版本）
"""

import os
import sys
import webbrowser
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from gui.panels.border_panel import BorderPanel
from gui.panels.contact_panel import ContactPanel


class MainWindow:
    """
    EN: Main application window with tabbed interface
    CN: 主应用窗口，包含标签页界面
    """
    
    def __init__(self, root):
        self.root = root
        self.lang = "zh"  # EN: Language mode: "zh" or "en" / CN: 语言模式："zh" 或 "en"
        
        # EN: Setup menu bar / CN: 设置菜单栏
        self.setup_menu()
        
        # EN: Configure tab style / CN: 配置标签样式
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[10, 5])
        style.map("TNotebook.Tab",
                 background=[("selected", "#2780e3")],
                 foreground=[("selected", "white")])
        
        # EN: Create notebook (tabbed interface) / CN: 创建标签页界面
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # EN: Add tool panels / CN: 添加工具面板
        self.border_frame = ttk.Frame(self.notebook, padding=10)
        self.contact_frame = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.border_frame, text="边框工具")
        self.notebook.add(self.contact_frame, text="底片索引")
        
        # EN: Initialize panels / CN: 初始化面板
        self.border_panel = BorderPanel(self.border_frame)
        self.contact_panel = ContactPanel(self.contact_frame)
    
    def setup_menu(self):
        """
        EN: Create menu bar
        CN: 创建菜单栏
        """
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # EN: File menu / CN: 文件菜单
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="文件", menu=self.file_menu)
        
        self.file_menu.add_command(label="打开工作目录", command=self.open_working_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="退出", command=self.root.quit)
        
        # EN: Language menu (always in English for accessibility) / CN: 语言菜单（始终显示英文以便查找）
        self.lang_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Language", menu=self.lang_menu)
        
        self.lang_menu.add_command(label="中文", command=lambda: self.switch_language("zh"))
        self.lang_menu.add_command(label="English", command=lambda: self.switch_language("en"))
        
        # EN: Help menu / CN: 帮助菜单
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="帮助", menu=self.help_menu)
        
        self.help_menu.add_command(label="关于", command=self.show_about)
        self.help_menu.add_command(label="GitHub 仓库", command=self.open_github)
    
    def switch_language(self, lang):
        """
        EN: Switch UI language
        CN: 切换界面语言
        """
        self.lang = lang
        
        # EN: Update menu labels / CN: 更新菜单标签
        if lang == "zh":
            self.root.title("GT23 胶片工作流 v2.0.0-alpha.1")
            self.menubar.entryconfig(0, label="文件")
            # Language menu always stays as "Language" for accessibility
            self.menubar.entryconfig(2, label="帮助")
            
            self.file_menu.entryconfig(0, label="打开工作目录")
            self.file_menu.entryconfig(2, label="退出")
            
            self.help_menu.entryconfig(0, label="关于")
            self.help_menu.entryconfig(1, label="GitHub 仓库")
            
            self.notebook.tab(0, text="边框工具")
            self.notebook.tab(1, text="底片索引")
        else:
            self.root.title("GT23 Film Workflow v2.0.0-alpha.1")
            self.menubar.entryconfig(0, label="File")
            # Language menu always stays as "Language" for accessibility
            self.menubar.entryconfig(2, label="Help")
            
            self.file_menu.entryconfig(0, label="Open Folder")
            self.file_menu.entryconfig(2, label="Exit")
            
            self.help_menu.entryconfig(0, label="About")
            self.help_menu.entryconfig(1, label="GitHub Repository")
            
            self.notebook.tab(0, text="Border Tool")
            self.notebook.tab(1, text="Contact Sheet")
        
        # EN: Update panel languages / CN: 更新面板语言
        self.border_panel.update_language(lang)
        self.contact_panel.update_language(lang)
    
    def open_working_folder(self):
        self.help_menu.add_command(label="GitHub 仓库", command=self.open_github)
    
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
            tk.messagebox.showerror("错误 Error", f"无法打开目录 Failed to open folder:\n{e}")
    
    def show_about(self):
        """
        EN: Show about dialog
        CN: 显示关于对话框
        """
        if self.lang == "zh":
            title = "关于 GT23"
            about_text = """GT23 胶片工作流

版本: 2.0.0-alpha.1
作者: Hugo
邮箱: xjames007@gmail.com

专为胶片摄影师设计的数字接触印样与底片边框处理工具。

灵感来自 Contax G2 & T3 📷"""
        else:
            title = "About GT23"
            about_text = """GT23 Film Workflow

Version: 2.0.0-alpha.1
Author: Hugo
Email: xjames007@gmail.com

A dedicated tool for film photographers to generate
digital contact sheets and professionally processed film borders.

Inspired by Contax G2 & T3 📷"""
        
        tk.messagebox.showinfo(title, about_text)
    
    def open_github(self):
        """
        EN: Open GitHub repository in browser
        CN: 在浏览器中打开 GitHub 仓库
        """
        webbrowser.open("https://github.com/hugoxxxx/GT23_Workflow")
