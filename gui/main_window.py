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
from utils.asset_sync import sync_assets_async
from version import get_version_string, __version__, __author__, __email__
import tkinter.messagebox as messagebox
from tkinter import filedialog
from utils.config_manager import config_manager


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
        
        # EN: Add tabs with language-specific text / CN: 添加带语言的标签页
        border_text = "边框工具" if self.lang == "zh" else "Border Tool"
        contact_text = "底片索引" if self.lang == "zh" else "Contact Sheet"
        self.notebook.add(self.border_frame, text=border_text)
        self.notebook.add(self.contact_frame, text=contact_text)
        
        # EN: Initialize panels with detected language / CN: 使用检测到的语言初始化面板
        self.border_panel = BorderPanel(self.border_frame, lang=self.lang)
        self.contact_panel = ContactPanel(self.contact_frame, lang=self.lang)
        # EN: Apply detected language to panels immediately / CN: 立刻应用系统语言到面板
        self.border_panel.update_language(self.lang)
        self.contact_panel.update_language(self.lang)

        # EN: Check for missing assets on first run / CN: 首次启动检查是否缺少资源
        self.root.after(500, self.check_missing_assets)
    
    def check_missing_assets(self):
        """EN: Prompt user to sync if logos are missing. / CN: 如果缺少图标，提示用户进行同步。"""
        from core.renderer import bootstrap_logos
        try:
            logo_dir = bootstrap_logos()
            logo_count = 0
            if os.path.exists(logo_dir):
                files = os.listdir(logo_dir)
                logo_count = len([f for f in files if f.lower().endswith(('.svg', '.png'))])
            
            if logo_count == 0:
                title = "首次运行提示" if self.lang == "zh" else "First Run Hint"
                msg = ("检测到本地图标库为空。\n\n本版本为轻量化版（不打包 126+ 款相机图标）。\n"
                       "是否现在从云端仓库同步图标资源？") if self.lang == "zh" else \
                      ("No camera logos detected.\n\nThis is a lightweight version (logos not bundled).\n"
                       "Would you like to sync asset library from cloud now?")
                
                if messagebox.askyesno(title, msg):
                    self.sync_assets_command()
        except Exception:
            pass
    def setup_menu(self):
        """
        EN: Create menu bar
        CN: 创建菜单栏
        """
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # EN: File menu / CN: 文件菜单
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        file_label = "文件" if self.lang == "zh" else "File"
        self.menubar.add_cascade(label=file_label, menu=self.file_menu)
        
        open_label = "打开工作目录" if self.lang == "zh" else "Open Folder"
        exit_label = "退出" if self.lang == "zh" else "Exit"
        settings_label = "设置" if self.lang == "zh" else "Settings"
        
        self.file_menu.add_command(label=open_label, command=self.open_working_folder)
        self.file_menu.add_command(label=settings_label, command=self.show_settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=exit_label, command=self.root.quit)
        
        # EN: Language menu (always in English for accessibility) / CN: 语言菜单（始终显示英文以便查找）
        self.lang_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Language", menu=self.lang_menu)
        
        self.lang_menu.add_command(label="中文", command=lambda: self.switch_language("zh"))
        self.lang_menu.add_command(label="English", command=lambda: self.switch_language("en"))
        
        # EN: Help menu / CN: 帮助菜单
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        help_label = "帮助" if self.lang == "zh" else "Help"
        self.menubar.add_cascade(label=help_label, menu=self.help_menu)
        
        about_label = "关于" if self.lang == "zh" else "About"
        github_label = "GitHub 仓库" if self.lang == "zh" else "GitHub Repository"
        sync_label = "同步边框资源" if self.lang == "zh" else "Sync Border Assets"
        
        self.help_menu.add_command(label=sync_label, command=self.sync_assets_command)
        self.help_menu.add_separator()
        self.help_menu.add_command(label=about_label, command=self.show_about)
        self.help_menu.add_command(label=github_label, command=self.open_github)
    
    def switch_language(self, lang):
        """
        EN: Switch UI language
        CN: 切换界面语言
        """
        self.lang = lang
        
        # EN: Update menu labels / CN: 更新菜单标签
        if lang == "zh":
            self.root.title(f"GT23 胶片工作流 {get_version_string()}")
            self.menubar.entryconfig(0, label="文件")
            # Language menu always stays as "Language" for accessibility
            self.menubar.entryconfig(2, label="帮助")
            
            self.file_menu.entryconfig(0, label="打开工作目录")
            self.file_menu.entryconfig(1, label="设置")
            self.file_menu.entryconfig(3, label="退出")
            
            self.help_menu.entryconfig(0, label="同步边框资源")
            self.help_menu.entryconfig(2, label="关于")
            self.help_menu.entryconfig(3, label="GitHub 仓库")
            
            self.notebook.tab(0, text="边框工具")
            self.notebook.tab(1, text="底片索引")
        else:
            self.root.title(f"GT23 Film Workflow {get_version_string()}")
            self.menubar.entryconfig(0, label="File")
            # Language menu always stays as "Language" for accessibility
            self.menubar.entryconfig(2, label="Help")
            
            self.file_menu.entryconfig(0, label="Open Folder")
            self.file_menu.entryconfig(1, label="Settings")
            self.file_menu.entryconfig(3, label="Exit")
            
            self.help_menu.entryconfig(0, label="Sync Border Assets")
            self.help_menu.entryconfig(2, label="About")
            self.help_menu.entryconfig(3, label="GitHub Repository")
            
            self.notebook.tab(0, text="Border Tool")
            self.notebook.tab(1, text="Contact Sheet")
        
        # EN: Update panel languages / CN: 更新面板语言
        self.border_panel.update_language(lang)
        self.contact_panel.update_language(lang)
    
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
            if getattr(sys, 'frozen', False):
                working_dir = os.path.dirname(sys.executable)
            else:
                working_dir = os.getcwd()
            
            # EN: Cross-platform folder opening / CN: 跨平台打开文件夹
            system = platform.system()
            if system == "Windows":
                os.startfile(working_dir)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", working_dir])
            else:  # Linux and others
                subprocess.run(["xdg-open", working_dir])
        except Exception as e:
            tk.messagebox.showerror("错误 Error", f"无法打开目录 Failed to open folder:\n{e}")
    
    def show_about(self):
        """
        EN: Show about dialog
        CN: 显示关于对话框
        """
        version_str = f"v{__version__}"
        if self.lang == "zh":
            title = "关于 GT23"
            about_text = f"""GT23 胶片工作流
            
版本: {__version__}
作者: {__author__}
邮箱: {__email__}

专为胶片摄影师设计的数字全卷缩略图与底片边框处理工具。

灵感来自 Contax G2 & T3 📷"""
        else:
            title = "About GT23"
            about_text = f"""GT23 Film Workflow

Version: {__version__}
Author: {__author__}
Email: {__email__}

A dedicated tool for film photographers to generate
digital contact sheets and professionally processed film borders.

Inspired by Contax G2 & T3 📷"""
        
        messagebox.showinfo(title, about_text)

    def show_settings(self):
        """EN: Show settings dialog / CN: 显示设置对话框"""
        SettingsDialog(self.root, self.lang)

    def sync_assets_command(self):
        """
        EN: Trigger asset synchronization with a progress dialog
        CN: 带有进度条的资源同步触发器
        """
        dialog = SyncProgressDialog(self.root, self.lang)
        
        def on_complete(success, message):
            # EN: Filter bilingual message / CN: 过滤双语消息
            final_msg = message
            if "CN:" in message:
                parts = message.split("CN:")
                en_part = parts[0].replace("EN:", "").strip()
                zh_part = parts[1].strip()
                final_msg = zh_part if self.lang == "zh" else en_part
            
            dialog.stop(success, final_msg)
            if success:
                # EN: Refresh library to show new counts / CN: 刷新资源库以显示最新计数
                self.border_panel.load_film_library()
                
        sync_assets_async(on_complete)

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.lang = lang
        self.title("设置 Settings" if lang == "zh" else "Settings")
        
        # EN: Robust default size / CN: 稳健的默认尺寸
        self.geometry("650x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        # EN: Center relative to main window / CN: 相对于主窗口居中
        self.update_idletasks()
        w, h = 650, 480
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        container = ttk.Frame(self, padding=30)
        container.pack(fill=BOTH, expand=YES)

        # --- Section 1: Asset Path ---
        path_label = "自定义资产路径" if self.lang == "zh" else "Custom Asset Path"
        header_font = ("Microsoft YaHei", 11, "bold") if self.lang == "zh" else ("Segoe UI", 11, "bold")
        ttk.Label(container, text=path_label, font=header_font).pack(anchor=W, pady=(0, 10))
        
        path_frame = ttk.Frame(container)
        path_frame.pack(fill=X, pady=5)
        
        self.path_var = tk.StringVar(value=config_manager.get("custom_asset_path", ""))
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10), ipady=3)
        
        browse_btn = "浏览..." if self.lang == "zh" else "Browse..."
        ttk.Button(path_frame, text=browse_btn, command=self._browse_path, width=12, bootstyle="outline-secondary").pack(side=RIGHT)
        
        hint = "注：留空则使用程序默认目录" if self.lang == "zh" else "Note: Leave empty to use default directories."
        hint_font = ("Microsoft YaHei", 9) if self.lang == "zh" else ("Segoe UI", 9)
        ttk.Label(container, text=hint, font=hint_font, foreground="#888").pack(anchor=W, pady=(5, 0))

        # --- Divider ---
        ttk.Separator(container, orient="horizontal").pack(fill=X, pady=25)
        
        # --- Section 2: Sync Source ---
        source_label = "优先同步源" if self.lang == "zh" else "Preferred Sync Source"
        ttk.Label(container, text=source_label, font=header_font).pack(anchor=W, pady=(0, 15))
        
        self.source_var = tk.StringVar(value=config_manager.get("preferred_sync_source", "gitee"))
        source_frame = ttk.Frame(container)
        source_frame.pack(fill=X)
        
        # EN: Use vertical layout to avoid clipping / CN: 使用纵向布局避免长文本截断
        ttk.Radiobutton(source_frame, text="Gitee (国内推荐)" if self.lang == "zh" else "Gitee (CN Recommended)", 
                        variable=self.source_var, value="gitee", bootstyle="info").pack(anchor=W, pady=5)
        ttk.Radiobutton(source_frame, text="GitHub (全球/加速)" if self.lang == "zh" else "GitHub (Global/Proxy)", 
                        variable=self.source_var, value="github", bootstyle="info").pack(anchor=W, pady=5)

        # --- Footer: Actions ---
        footer = ttk.Frame(container)
        footer.pack(side=BOTTOM, fill=X, pady=(20, 0))
        
        save_btn = "保存并关闭" if self.lang == "zh" else "Save & Close"
        ttk.Button(footer, text=save_btn, style="primary", command=self._save).pack(side=RIGHT, padx=5)

    def _browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def _save(self):
        config_manager.set("custom_asset_path", self.path_var.get())
        config_manager.set("preferred_sync_source", self.source_var.get())
        messagebox.showinfo("Success" if self.lang == "en" else "成功", 
                            "设置已保存成功！某些更改可能需要重启程序生效。\nSettings saved! Some changes may require restart." if self.lang == "zh" else "Settings saved successfully!")
        self.destroy()

class SyncProgressDialog(tk.Toplevel):
    def __init__(self, parent, lang="en"):
        super().__init__(parent)
        self.lang = lang
        self.title("同步中 Syncing..." if lang == "zh" else "Syncing...")
        
        self.geometry("480x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        container = ttk.Frame(self, padding=35)
        container.pack(fill=BOTH, expand=YES)

        label_text = "正在同步边框资源库，请耐心等待...\nSyncing assets, please wait..."
        ttk.Label(container, text=label_text, justify=CENTER, font=("", 10)).pack(pady=(0, 20))
        
        self.progress = ttk.Progressbar(container, mode='indeterminate', length=350, bootstyle="success-striped")
        self.progress.pack()
        self.progress.start(10)

        # Center
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")

    def stop(self, success, message):
        self.progress.stop()
        self.destroy()
        title = "同步结果 Sync Result" if self.lang == "zh" else "Sync Result"
        if success:
            messagebox.showinfo(title, message)
        else:
            messagebox.showerror(title, message)
