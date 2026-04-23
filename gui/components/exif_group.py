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
    def __init__(self, parent, lang="en", on_change=None, exif_vars=None, show_vars=None, 
                 global_sync_var=None, on_save_favorite=None, on_apply_favorite=None):
        """
        Args:
            parent: Parent widget
            lang: "zh" or "en"
            on_change: Callback when any value changes
            exif_vars: Dict of {name: StringVar}
            show_vars: Dict of {name: IntVar/BooleanVar}
            global_sync_var: BooleanVar for "Apply to All"
            on_save_favorite: Callback to save current make/model/lens
            on_apply_favorite: Callback to load a favorite
        """
        title = "手动 EXIF 覆盖 (留空则读取原图)" if lang == "zh" else "Manual EXIF Overrides (Leave blank to use file EXIF)"
        super().__init__(parent, text=title, padding=5)
        
        self.lang = lang
        self.on_change = on_change
        self.exif_vars = exif_vars or {}
        self.show_vars = show_vars or {}
        self.global_sync_var = global_sync_var
        self.on_save_favorite = on_save_favorite
        self.on_apply_favorite = on_apply_favorite
        self.fields = {} # EN: Store container references / CN: 存储容器引用
        
        self.setup_ui()

    def setup_ui(self):
        # Row 0: Favorites
        row0 = ttk.Frame(self)
        row0.pack(fill=X, pady=(2, 5))
        row0.columnconfigure(0, weight=1, uniform="exif")
        
        fav_container = ttk.Frame(row0)
        fav_container.grid(row=0, column=0, columnspan=2, sticky=EW)
        
        self.fav_label = ttk.Label(fav_container, text="机型预设" if self.lang == "zh" else "Presets", width=8)
        self.fav_label.pack(side=LEFT, padx=(2, 0))
        
        self.fav_combo = ttk.Combobox(fav_container, state="readonly", width=30)
        self.fav_combo.pack(side=LEFT, padx=5, fill=X, expand=YES)
        self.fav_combo.bind("<<ComboboxSelected>>", self._handle_fav_selected)
        
        # EN: Use primary blue for consistent action color / CN: 使用 primary 蓝调统一动作色彩
        self.btn_fav = ttk.Button(fav_container, text="收藏" if self.lang=="zh" else "Fav", 
                                 command=self._handle_save_fav, bootstyle="outline-primary", padding=(8, 2))
        self.btn_fav.pack(side=LEFT, padx=(0, 10))

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
        self.fields[key] = container # Store for visibility control
        
        # Visibility toggle
        show_var = self.show_vars.get(key)
        if show_var:
            cb_show = ttk.Checkbutton(container, variable=show_var, command=self.on_change, bootstyle="round-toggle")
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

    def set_field_state(self, key, state):
        """EN: Toggle field state (normal/disabled) / CN: 切换字段状态 (正常/禁用)"""
        if key in self.fields:
            container = self.fields[key]
            # EN: Recursively set state for all children / CN: 递归设置所有子部件的状态
            def update_recursive(widget):
                try:
                    widget.configure(state=state)
                except:
                    pass
                for child in widget.winfo_children():
                    update_recursive(child)
            update_recursive(container)

    def _handle_fav_selected(self, event):
        name = self.fav_combo.get()
        if self.on_apply_favorite:
            self.on_apply_favorite(name)

    def _handle_save_fav(self):
        if self.on_save_favorite:
            self.on_save_favorite()

    def set_favorite_list(self, names):
        """EN: Update favorites list / CN: 更新收藏列表"""
        self.fav_combo['values'] = sorted(list(names))
        if not names:
            self.fav_combo.set("")
