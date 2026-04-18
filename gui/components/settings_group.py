# gui/components/settings_group.py
"""
EN: Advanced Settings component for border parameters
CN: 边框参数的高级设置组件
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class SettingsGroup(ttk.Labelframe):
    """
    EN: Group of settings for border ratios, font scale, and theme
    CN: 包含边框比例、字体缩放和主题展示的设置组
    """
    def __init__(self, parent, lang="en", on_change=None, vars=None):
        """
        Args:
            parent: Parent widget
            lang: "zh" or "en"
            on_change: Callback when any value changes
            vars: Dict of {name: Var} - side, top, bottom, font, theme, branding
        """
        title = "高级设置" if lang == "zh" else "Advanced Settings"
        super().__init__(parent, text=title, padding=10)
        
        self.lang = lang
        self.on_change = on_change
        self.vars = vars or {}
        
        self.setup_ui()

    def setup_ui(self):
        # EN: Advanced settings components
        row1 = ttk.Frame(self)
        row1.pack(fill=X, pady=2)
        row1.columnconfigure(0, weight=1, uniform="adv")
        row1.columnconfigure(1, weight=1, uniform="adv")
        
        row2 = ttk.Frame(self)
        row2.pack(fill=X, pady=2)
        row2.columnconfigure(0, weight=1, uniform="adv")
        row2.columnconfigure(1, weight=1, uniform="adv")

        self.side_label = self.add_setting(row1, "side", 0)
        self.top_label = self.add_setting(row1, "top", 1)
        self.bottom_label = self.add_setting(row2, "bottom", 0)
        self.font_label = self.add_setting(row2, "font", 1)
        
        # EN: Global toggles row / CN: 全局开关行
        row3 = ttk.Frame(self)
        row3.pack(fill=X, pady=(5, 2))
        
        branding_var = self.vars.get("branding")
        if branding_var:
            self.branding_toggle = ttk.Checkbutton(row3, 
                                                text="开启镜头专属标识" if self.lang == "zh" else "Enable Lens Branding",
                                                variable=branding_var,
                                                command=self.on_change,
                                                bootstyle="round-toggle")
            self.branding_toggle.pack(side=LEFT, padx=2)

        row4 = ttk.Frame(self)
        row4.pack(fill=X, pady=2)
        row4.columnconfigure(0, weight=1, uniform="adv")
        row4.columnconfigure(1, weight=1, uniform="adv")

        # EN: Border Theme selector / CN: 边框主题选择
        theme_container = ttk.Frame(row4)
        theme_container.grid(row=0, column=0, sticky=EW, padx=2)
        self.theme_label = ttk.Label(theme_container, text="边框主题" if self.lang == "zh" else "Border Theme")
        self.theme_label.pack(side=LEFT)
        
        theme_var = self.vars.get("theme")
        if theme_var:
            self.theme_combo = ttk.Combobox(theme_container, textvariable=theme_var, state="readonly", width=20)
            self.theme_combo.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
            self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())
            self._update_theme_combo_values()

        self.update_labels()

    def add_setting(self, parent, key, col):
        container = ttk.Frame(parent)
        container.grid(row=0, column=col, sticky=EW, padx=2)
        
        label_text = self._get_label_text(key)
        lbl = ttk.Label(container, text=label_text, width=12)
        lbl.pack(side=LEFT)
        
        var = self.vars.get(key)
        if var:
            entry = ttk.Entry(container, textvariable=var, width=12)
            entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
            entry.bind("<Return>", lambda e: self.on_change())
        
        return lbl

    def _get_label_text(self, key):
        mapping = {
            "side": ("左右边框", "Side Margin"),
            "top": ("顶部留白", "Top Margin"),
            "bottom": ("底部留白", "Bottom Margin"),
            "font": ("字体基础", "Font Scale")
        }
        idx = 0 if self.lang == "zh" else 1
        return mapping[key][idx]

    def update_language(self, lang):
        self.lang = lang
        self.config(text="高级设置" if lang == "zh" else "Advanced Settings")
        self.update_labels()
        self._update_theme_combo_values()
        if hasattr(self, 'branding_toggle'):
            self.branding_toggle.config(text="开启镜头专属标识" if lang == "zh" else "Enable Lens Branding")

    def update_labels(self):
        self.side_label.config(text=self._get_label_text("side"))
        self.top_label.config(text=self._get_label_text("top"))
        self.bottom_label.config(text=self._get_label_text("bottom"))
        self.font_label.config(text=self._get_label_text("font"))
        self.theme_label.config(text="边框主题" if self.lang == "zh" else "Border Theme")
        
        # Adjust widths for English
        if self.lang == "en":
            for lbl in [self.side_label, self.top_label, self.bottom_label, self.font_label, self.theme_label]:
                lbl.configure(width=15)
        else:
            for lbl in [self.side_label, self.top_label, self.bottom_label, self.font_label, self.theme_label]:
                lbl.configure(width=12)

    def _update_theme_combo_values(self):
        """
        EN: Update theme combo box values with current language
        CN: 使用当前语言更新主题下拉框选项
        """
        if not hasattr(self, 'theme_combo'): return
        
        if self.lang == "zh":
            themes = ["浅色", "深色", "磨砂玻璃", "马卡龙", "彩虹", "樱花粉"]
        else:
            themes = ["Default", "Dark Mode", "Frosted Glass", "Macaron", "Rainbow", "Sakura"]

        theme_var = self.vars.get("theme")
        if not theme_var: return
        
        current = theme_var.get()
        self.theme_combo['values'] = themes

        # EN: Try to maintain selection / CN: 尝试保持之前的选择
        selected = False
        if current:
            for i, theme in enumerate(themes):
                # EN: Search by keyword / CN: 通过关键词搜索进行对齐
                for kw in ["Light", "Default", "Dark", "Macaron", "Rainbow", "Frosted", "Glass", "浅色", "深色", "马卡龙", "彩虹", "磨砂"]:
                    if kw.lower() in current.lower() and kw.lower() in theme.lower():
                        if "Rainbow" in current and "Rainbow" not in theme: continue
                        if "彩虹" in current and "彩虹" not in theme: continue
                        self.theme_combo.current(i)
                        selected = True
                        break
                if selected: break

        if not selected and themes:
            self.theme_combo.current(0)
