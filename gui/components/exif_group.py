# gui/components/exif_group.py
"""
EN: EXIF Overrides component for the sidebar
CN: 侧边栏的 EXIF 覆盖配置组件
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class ExifGroup(ttk.Labelframe):
    """
    EN: Group of input fields and checkboxes for manual EXIF overrides
    CN: 用于手动 EXIF 覆盖的输入框和复选框组
    """
    def __init__(self, parent, lang="en", on_change=None, exif_vars=None, show_vars=None, global_sync_var=None):
        """
        Args:
            parent: Parent widget
            lang: "zh" or "en"
            on_change: Callback when any value changes
            exif_vars: Dict of {name: StringVar}
            show_vars: Dict of {name: IntVar/BooleanVar}
            global_sync_var: BooleanVar for "Apply to All"
        """
        title = "手动 EXIF 覆盖 (留空则读取原图)" if lang == "zh" else "Manual EXIF Overrides (Leave blank to use file EXIF)"
        super().__init__(parent, text=title, padding=5)
        
        self.lang = lang
        self.on_change = on_change
        self.exif_vars = exif_vars or {}
        self.show_vars = show_vars or {}
        self.global_sync_var = global_sync_var
        
        self.setup_ui()

    def setup_ui(self):
        # EN: Global Sync Switch (Master) / CN: 全局同步主开关
        if self.global_sync_var:
            sync_text = "全局应用" if self.lang == "zh" else "Apply to All"
            self.global_sync_check = ttk.Checkbutton(self, text=sync_text, 
                                                   variable=self.global_sync_var, 
                                                   command=self.on_change,
                                                   bootstyle="round-toggle")
            self.global_sync_check.pack(anchor=W, padx=5, pady=(5, 5))
        
        # Layout grids
        self.row1 = ttk.Frame(self)
        self.row1.pack(fill=X, pady=2)
        self.row1.columnconfigure(0, weight=1, uniform="exif")
        self.row1.columnconfigure(1, weight=1, uniform="exif")
        
        self.row2 = ttk.Frame(self)
        self.row2.pack(fill=X, pady=2)
        self.row2.columnconfigure(0, weight=1, uniform="exif")
        self.row2.columnconfigure(1, weight=1, uniform="exif")
        
        self.row3 = ttk.Frame(self)
        self.row3.pack(fill=X, pady=2)
        self.row3.columnconfigure(0, weight=1, uniform="exif")
        self.row3.columnconfigure(1, weight=1, uniform="exif")

        self.add_field(self.row1, "Make:", "make", 0)
        self.add_field(self.row1, "Model:", "model", 1)
        self.add_field(self.row2, "Shutter:", "shutter", 0)
        self.add_field(self.row2, "Aperture:", "aperture", 1)
        self.add_field(self.row3, "ISO:", "iso", 0)
        self.add_field(self.row3, "Lens:", "lens", 1)

    def add_field(self, parent, label_text, key, col):
        container = ttk.Frame(parent)
        container.grid(row=0, column=col, sticky=EW)
        
        # Visibility toggle
        show_var = self.show_vars.get(key)
        if show_var:
            cb_show = ttk.Checkbutton(container, variable=show_var, command=self.on_change)
            cb_show.pack(side=LEFT, padx=(2, 0))
            
        ttk.Label(container, text=label_text, width=8).pack(side=LEFT)
        
        var = self.exif_vars.get(key)
        if var:
            entry = ttk.Entry(container, textvariable=var, width=18)
            entry.pack(side=LEFT, padx=(0, 10), fill=X, expand=YES)
            entry.bind("<Return>", lambda e: self.on_change())

    def update_language(self, lang):
        self.lang = lang
        title = "手动 EXIF 覆盖 (留空则读取原图)" if lang == "zh" else "Manual EXIF Overrides (Leave blank to use file EXIF)"
        self.config(text=title)
