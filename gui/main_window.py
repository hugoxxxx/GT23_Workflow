# gui/main_window.py
"""
EN: Main window for GT23 Film Workflow GUI (tkinter version)
CN: GT23 胶片工作流主窗口（tkinter版本）
"""

import os
import sys
import locale
import platform
import subprocess
import webbrowser
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from gui.panels.border_panel import BorderPanel
from gui.panels.contact_panel import ContactPanel
from gui.panels.matin_panel import MatinPanel
from version import get_version_string

import tkinter.font as tkfont


def detect_system_language():
    """
    EN: Auto-detect system language based on locale settings
    CN: 根据系统区域设置自动检测语言
    
    Returns:
        str: "zh" for Chinese, "en" for English (default)
    """
    try:
        # EN: Try to get system locale / CN: 尝试获取系统区域设置
        system_locale = locale.getdefaultlocale()[0]
        if system_locale:
            # EN: Check if locale starts with 'zh' (zh_CN, zh_TW, etc.) / CN: 检查是否为中文区域
            if system_locale.startswith('zh'):
                return "zh"
        
        # EN: Fallback: check LANG environment variable / CN: 回退方案：检查 LANG 环境变量
        lang_env = os.environ.get('LANG', '')
        if lang_env.startswith('zh'):
            return "zh"
            
    except Exception:
        # EN: Language detection failed, silently fallback to default
        # CN: 语言检测失败，静默回退到默认值
        # Note: Silent fail is intentional - doesn't affect app functionality
        pass
    
    # EN: Default to English / CN: 默认为英文
    return "en"


class MainWindow:
    """
    EN: Main application window with tabbed interface
    CN: 主应用窗口，包含标签页界面
    """
    
    def __init__(self, root):
        self.root = root
        # EN: Auto-detect system language / CN: 自动检测系统语言
        self.lang = detect_system_language()
        
        # EN: Setup menu bar / CN: 设置菜单栏
        self.setup_menu()
        
        self.setup_styles()
        self.root.configure(background="#0D0D0D") # Almost black
        # self.setup_header() # Removed banner
        
        # EN: Create notebook (tabbed interface) / CN: 创建标签页界面
        self.notebook = ttk.Notebook(root, bootstyle="secondary")
        self.notebook.pack(fill=BOTH, expand=YES, padx=20, pady=(20, 20))

        
        # EN: Add tool panels / CN: 添加工具面板
        self.border_frame = ttk.Frame(self.notebook)
        self.contact_frame = ttk.Frame(self.notebook)
        self.matin_frame = ttk.Frame(self.notebook)

        
        from utils.i18n import get_string
        
        # EN: Add tabs with language-specific text / CN: 添加带语言的标签页
        self.notebook.add(self.border_frame, text=get_string("border_tool", self.lang))
        self.notebook.add(self.contact_frame, text=get_string("contact_sheet", self.lang))
        self.notebook.add(self.matin_frame, text=get_string("slide_mode", self.lang))
        
        # EN: Initialize panels with detected language / CN: 使用检测到的语言初始化面板
        self.border_panel = BorderPanel(self.border_frame, lang=self.lang)
        self.contact_panel = ContactPanel(self.contact_frame, lang=self.lang)
        self.matin_panel = MatinPanel(self.matin_frame, lang=self.lang)



    def setup_styles(self):
        """
        EN: Configure custom styles for a TRULY minimalist, border-less look
        CN: 配置真正的极简无边界样式
        """
        self.style = ttk.Style()
        bg_color = "#0D0D0D"
        accent_color = "#F58223"
        
        # EN: Global Settings
        self.style.configure("TNotebook", background=bg_color, borderwidth=0, padding=0)
        self.style.configure("TNotebook.Tab", 
                            padding=[20, 12], 
                            font=("Segoe UI", 10, "bold"),
                            background=bg_color,
                            foreground="#555555",
                            borderwidth=0,
                            focuscolor=bg_color)
        self.style.map("TNotebook.Tab",
                      background=[("selected", bg_color), ("active", "#1A1A1A")],
                      foreground=[("selected", accent_color), ("active", "#FFFFFF")],
                      expand=[("selected", [1, 1, 1, 0])])
        
        # EN: Frames & Labels
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground="#A0A0A0")
        self.style.configure("Header.TLabel", background=bg_color, foreground="#FFFFFF")
        
        # EN: Flat Inputs / CN: 扁平化输入框
        self.style.configure("TEntry", 
                            fieldbackground="#1A1A1A", 
                            foreground="#FFFFFF", 
                            borderwidth=0)
        self.style.map("TEntry",
                      fieldbackground=[("focus", "#222222")])
                      
        self.style.configure("TCombobox", 
                            fieldbackground="#1A1A1A", 
                            background="#1A1A1A",
                            foreground="#FFFFFF",
                            borderwidth=0, 
                            arrowcolor="#666")
        self.style.map("TCombobox",
                      fieldbackground=[("focus", "#222222")])
        
        # EN: Custom Radiobuttons / CN: 自定义单选按钮
        self.style.configure("TRadiobutton", background=bg_color, foreground="#888")
        self.style.map("TRadiobutton", 
                      foreground=[("selected", accent_color), ("active", "#FFFFFF")])
        
        # EN: Modern Primary Button / CN: 现代主按钮
        self.style.configure("Action.TButton", 
                            background="#1A1A1A",
                            foreground="#F58223",
                            font=("Segoe UI", 10, "bold"),
                            borderwidth=1,
                            relief=FLAT,
                            padding=(20, 10))
        self.style.map("Action.TButton", 
                      background=[("active", "#F58223"), ("pressed", "#D46D1E")],
                      foreground=[("active", "#000000"), ("pressed", "#000000")])
        
        # EN: Panedwindow / CN: 分割窗格
        self.style.configure("TPanedwindow", background=bg_color, borderwidth=0)

    def setup_header(self):
        """
        EN: Create a minimalist, professional header
        CN: 创建极简专业的页眉
        """
        header_frame = ttk.Frame(self.root, padding=(20, 8))
        header_frame.pack(fill=X)
        
        # EN: Main Title - Clean, Bold, Modern / CN: 主标题 - 简洁、加粗、现代
        title_font = ("Segoe UI", 14, "bold") if platform.system() == "Windows" else ("Helvetica", 14, "bold")
        sub_font = ("Segoe UI", 8)
        
        title_label = ttk.Label(header_frame, text="GT23 FILM WORKFLOW", font=title_font, style="Header.TLabel")
        title_label.pack(side=LEFT)
        
        # EN: Subtle Version/Tag / CN: 微小的版本或装饰性文字
        tag_text = "DARKROOM EDITION"
        tag_label = ttk.Label(header_frame, text=tag_text, font=sub_font, foreground="#F58223")
        tag_label.pack(side=LEFT, padx=15, pady=(4, 0))

        # EN: Right-aligned description / CN: 右对齐的描述
        from utils.i18n import get_string
        self.desc_label = ttk.Label(header_frame, text=get_string("desc", self.lang), font=sub_font, foreground="#666")
        self.desc_label.pack(side=RIGHT, pady=(4, 0))

        # EN: Thin divider / CN: 极细分割线
        divider = ttk.Frame(self.root, height=1, bootstyle="secondary")
        divider.pack(fill=X, padx=20)

    def setup_menu(self):
        """
        EN: Create menu bar
        CN: 创建菜单栏
        """
        from utils.i18n import get_string
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # EN: File menu / CN: 文件菜单
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=get_string("file", self.lang), menu=self.file_menu)
        self.file_menu.add_command(label=get_string("open_folder", self.lang), command=self.open_working_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=get_string("exit", self.lang), command=self.root.quit)
        
        # EN: Language menu
        self.lang_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Language", menu=self.lang_menu)
        self.lang_menu.add_command(label="中文", command=lambda: self.switch_language("zh"))
        self.lang_menu.add_command(label="English", command=lambda: self.switch_language("en"))
        
        # EN: Help menu / CN: 帮助菜单
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=get_string("help", self.lang), menu=self.help_menu)
        self.help_menu.add_command(label=get_string("about", self.lang), command=self.show_about)
        self.help_menu.add_command(label=get_string("github", self.lang), command=self.open_github)
    
    def switch_language(self, lang):
        """
        EN: Switch UI language
        CN: 切换界面语言
        """
        self.lang = lang
        from utils.i18n import get_string
        
        # EN: Update window title / CN: 更新窗口标题
        title = f"GT23 胶片工作流 {get_version_string()}" if lang == "zh" else f"GT23 Film Workflow {get_version_string()}"
        self.root.title(title)
        
        # EN: Update menu labels / CN: 更新菜单标签
        self.menubar.entryconfig(0, label=get_string("file", lang))
        self.menubar.entryconfig(2, label=get_string("help", lang))
        
        self.file_menu.entryconfig(0, label=get_string("open_folder", lang))
        self.file_menu.entryconfig(2, label=get_string("exit", lang))
        
        self.help_menu.entryconfig(0, label=get_string("about", lang))
        self.help_menu.entryconfig(1, label=get_string("github", lang))
        
        self.notebook.tab(0, text=get_string("border_tool", lang))
        self.notebook.tab(1, text=get_string("contact_sheet", lang))
        self.notebook.tab(2, text=get_string("slide_mode", lang))
        self.desc_label.config(text=get_string("desc", lang))

        
        # EN: Update panel languages / CN: 更新面板语言
        self.border_panel.update_language(lang)
        self.contact_panel.update_language(lang)
        self.matin_panel.update_language(lang)

    
    def open_github(self):
        """
        EN: Open GitHub repository in browser
        CN: 在浏览器中打开 GitHub 仓库
        """
        webbrowser.open("https://github.com/hugoxxxx/GT23_Workflow")

    def open_working_folder(self):
        """
        EN: Open working directory in file explorer (cross-platform)
        CN: 在文件管理器中打开工作目录（跨平台）
        """
        try:
            from utils.paths import get_working_dir
            working_dir = get_working_dir()
            
            # EN: Cross-platform folder opening / CN: 跨平台打开文件夹
            system = platform.system()
            if system == "Windows":
                os.startfile(working_dir)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", working_dir])
            else:  # Linux and others
                subprocess.run(["xdg-open", working_dir])
        except Exception as e:
            err_title = "错误" if self.lang == "zh" else "Error"
            err_msg = f"无法打开目录:\n{e}" if self.lang == "zh" else f"Failed to open folder:\n{e}"
            tk.messagebox.showerror(err_title, err_msg)
    
    def show_about(self):
        """
        EN: Show about dialog
        CN: 显示关于对话框
        """
        from utils.i18n import get_string
        tk.messagebox.showinfo(
            get_string("about_title", self.lang),
            get_string("about_text", self.lang)
        )
