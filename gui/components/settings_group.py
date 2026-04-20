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
    def __init__(self, parent, lang="en", on_change=None, on_sync_similar=None, vars=None):
        """
        Args:
            parent: Parent widget
            lang: "zh" or "en"
            on_change: Callback when any value changes
            on_sync_similar: Callback for "Sync Similar" button
            vars: Dict of {name: Var} - side, top, bottom, font, theme, branding
        """
        title = "高级设置" if lang == "zh" else "Advanced Settings"
        super().__init__(parent, text=title, padding=10)
        
        self.lang = lang
        self.on_change = on_change
        self.on_sync_similar = on_sync_similar
        self.vars = vars or {}
        
        self.setup_ui()

    def setup_ui(self):
        # EN: Top Switches Row 1 / CN: 顶部开关行 1
        row_sw1 = ttk.Frame(self)
        row_sw1.pack(fill=X, pady=(0, 2))
        
        branding_var = self.vars.get("branding")
        if branding_var:
            self.branding_toggle = ttk.Checkbutton(row_sw1, 
                                                text="开启镜头专属标识" if self.lang == "zh" else "Enable Lens Branding",
                                                variable=branding_var,
                                                command=self.on_change,
                                                bootstyle="round-toggle")
            self.branding_toggle.pack(side=LEFT, padx=2)
            
        # EN: Top Switches Row 2 / CN: 顶部开关行 2
        row_sw2 = ttk.Frame(self)
        row_sw2.pack(fill=X, pady=(0, 5))
        
        sync_lr_var = self.vars.get("sync_lr")
        if sync_lr_var:
            self.sync_lr_toggle = ttk.Checkbutton(row_sw2,
                                               text="左右边框同时调整" if self.lang == "zh" else "Sync L/R Borders",
                                               variable=sync_lr_var,
                                               command=self.on_change,
                                               bootstyle="round-toggle")
            self.sync_lr_toggle.pack(side=LEFT, padx=2)

        # EN: Advanced settings components
        row1 = ttk.Frame(self)
        row1.pack(fill=X, pady=2)
        row1.columnconfigure(0, weight=1, uniform="adv")
        row1.columnconfigure(1, weight=1, uniform="adv")
        
        row2 = ttk.Frame(self)
        row2.pack(fill=X, pady=2)
        row2.columnconfigure(0, weight=1, uniform="adv")
        row2.columnconfigure(1, weight=1, uniform="adv")

        self.left_label = self.add_setting(row1, "left", 0)
        self.right_label = self.add_setting(row1, "right", 1)
        self.top_label = self.add_setting(row2, "top", 0)
        self.bottom_label = self.add_setting(row2, "bottom", 1)
        
        # Row 3 for font and theme
        row3 = ttk.Frame(self)
        row3.pack(fill=X, pady=2)
        row3.columnconfigure(0, weight=1, uniform="adv")
        row3.columnconfigure(1, weight=1, uniform="adv")
        
        self.font_label = self.add_setting(row3, "font", 0)
        self.font_sub_label = self.add_setting(row3, "font_sub", 1)
        
        # Row 4 for offset
        row4 = ttk.Frame(self)
        row4.pack(fill=X, pady=2)
        row4.columnconfigure(0, weight=1, uniform="adv")
        row4.columnconfigure(1, weight=1, uniform="adv")
        
        self.font_offset_label = self.add_setting(row4, "font_offset", 0)

        # Row 7 for Sync Button
        row7 = ttk.Frame(self)
        row7.pack(fill=X, pady=(10, 0))
        self.sync_btn = ttk.Button(row7, 
                                 text="同步到同类图片 (画幅/旋转)" if self.lang == "zh" else "Apply to Similar Images",
                                 bootstyle="outline-primary",
                                 command=self.on_sync_similar)
        self.sync_btn.pack(fill=X)

        self.update_labels()

    def add_setting(self, parent, key, col):
        container = ttk.Frame(parent)
        container.grid(row=0, column=col, sticky=EW, padx=2)
        
        label_text = self._get_label_text(key)
        lbl = ttk.Label(container, text=label_text, width=15)
        lbl.pack(side=LEFT)
        
        var = self.vars.get(key)
        if var:
            entry = ttk.Entry(container, textvariable=var, width=12)
            entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
            entry.bind("<Return>", lambda e: self.on_change())
            entry.bind("<FocusOut>", lambda e: self.on_change())
        
        return lbl

    def _get_label_text(self, key):
        mapping = {
            "left": ("左边框 (px)", "Left Border (px)"),
            "right": ("右边框 (px)", "Right Border (px)"),
            "top": ("顶部边框 (px)", "Top Border (px)"),
            "bottom": ("底部边框 (px)", "Bottom Border (px)"),
            "font": ("型号字号 (px)", "Model Font Size (px)"),
            "font_sub": ("参数字号 (px)", "Param Font Size (px)"),
            "font_offset": ("文字垂直偏移 (px)", "Text Vertical Offset (px)")
        }
        idx = 0 if self.lang == "zh" else 1
        return mapping[key][idx]

    def update_language(self, lang):
        self.lang = lang
        self.config(text="高级设置" if lang == "zh" else "Advanced Settings")
        self.update_labels()
        self._update_theme_combo_values()
        self._update_ratio_combo_values()
        if hasattr(self, 'branding_toggle'):
            self.branding_toggle.config(text="开启镜头专属标识" if lang == "zh" else "Enable Lens Branding")
        if hasattr(self, 'sync_lr_toggle'):
            self.sync_lr_toggle.config(text="左右边框同时调整" if lang == "zh" else "Sync L/R Borders")
        if hasattr(self, 'sync_btn'):
            self.sync_btn.config(text="同步到同类图片 (画幅/旋转)" if lang == "zh" else "Apply to Similar Images")

    def update_labels(self):
        self.left_label.config(text=self._get_label_text("left"))
        self.right_label.config(text=self._get_label_text("right"))
        self.top_label.config(text=self._get_label_text("top"))
        self.bottom_label.config(text=self._get_label_text("bottom"))
        self.font_label.config(text=self._get_label_text("font"))
        self.font_sub_label.config(text=self._get_label_text("font_sub"))
        self.font_offset_label.config(text=self._get_label_text("font_offset"))
        
        # Adjust widths for English
        for lbl in [self.left_label, self.right_label, self.top_label, self.bottom_label, self.font_label, self.font_sub_label, self.font_offset_label]:
            lbl.configure(width=20 if self.lang == "en" else 15)

    def _update_theme_combo_values(self):
        """
        EN: Update theme combo box values with current language
        CN: 使用当前语言更新主题下拉框选项
        """
        if not hasattr(self, 'theme_combo'): return
        
        if self.lang == "zh":
            themes = ["浅色", "深色", "磨砂玻璃", "石板青", "马卡龙", "彩虹", "樱花粉"]
        else:
            themes = ["Default", "Dark Mode", "Frosted Glass", "Slate Teal", "Macaron", "Rainbow", "Sakura"]

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
            
    def _update_ratio_combo_values(self):
        """
        EN: Update ratio combo box values with current language
        CN: 使用当前语言更新比例下拉框选项
        """
        if not hasattr(self, 'ratio_combo'): return
        
        if self.lang == "zh":
            ratios = ["原图 (自由)", "1:1 (微信朋友圈)", "3:4 (小红书)", "4:3", "5:7 (Instagram)", "4:5", "9:16", "3:2", "16:9"]
        else:
            ratios = ["Original", "1:1 (WeChat)", "3:4 (LittleRedBook)", "4:3", "5:7 (Instagram)", "4:5", "9:16", "3:2", "16:9"]

        self.ratio_combo['values'] = ratios
        
        current = self.vars.get("target_ratio").get()
        # EN: Handle initial selection / CN: 处理初始选择
        found = False
        for i, r in enumerate(ratios):
            if current in r or (current == "Original" and "Original" in r):
                self.ratio_combo.current(i)
                found = True
                break
        if not found and ratios:
            self.ratio_combo.current(0)

class AestheticGroup(ttk.Labelframe):
    """
    EN: Group of settings for target ratio and border theme
    CN: 包含目标比例和边框主题的风格设置组
    """
    def __init__(self, parent, lang="en", on_change=None, vars=None):
        title = "主题与比例" if lang == "zh" else "Theme & Aspect"
        super().__init__(parent, text=title, padding=10)
        
        self.lang = lang
        self.on_change = on_change
        self.vars = vars or {}
        
        self.setup_ui()

    def setup_ui(self):
        # Row 1 for Target Ratio
        row1 = ttk.Frame(self)
        row1.pack(fill=X, pady=2)
        row1.columnconfigure(0, weight=1, uniform="aes")
        
        ratio_container = ttk.Frame(row1)
        ratio_container.grid(row=0, column=0, sticky=EW, padx=2)
        self.ratio_label = ttk.Label(ratio_container, text="目标比例" if self.lang == "zh" else "Target Ratio")
        self.ratio_label.pack(side=LEFT)
        
        ratio_var = self.vars.get("target_ratio")
        if ratio_var:
            self.ratio_combo = ttk.Combobox(ratio_container, textvariable=ratio_var, state="readonly", width=25)
            self.ratio_combo.pack(side=LEFT, fill=X, expand=YES, padx=(10, 0))
            self.ratio_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())
            self._update_ratio_combo_values()

        # Row 2 for Border Theme
        row2 = ttk.Frame(self)
        row2.pack(fill=X, pady=(5, 2))
        row2.columnconfigure(0, weight=1, uniform="aes")

        theme_container = ttk.Frame(row2)
        theme_container.grid(row=0, column=0, sticky=EW, padx=2)
        self.theme_label = ttk.Label(theme_container, text="边框主题" if self.lang == "zh" else "Border Theme")
        self.theme_label.pack(side=LEFT)
        
        theme_var = self.vars.get("theme")
        if theme_var:
            self.theme_combo = ttk.Combobox(theme_container, textvariable=theme_var, state="readonly", width=25)
            self.theme_combo.pack(side=LEFT, fill=X, expand=YES, padx=(10, 0))
            self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.on_change())
            self._update_theme_combo_values()

        self.update_labels()

    def update_language(self, lang):
        self.lang = lang
        self.config(text="主题与比例" if lang == "zh" else "Theme & Aspect")
        self.update_labels()
        self._update_theme_combo_values()
        self._update_ratio_combo_values()

    def update_labels(self):
        self.theme_label.config(text="边框主题" if self.lang == "zh" else "Border Theme")
        self.ratio_label.config(text="目标比例" if self.lang == "zh" else "Target Ratio")
        for lbl in [self.theme_label, self.ratio_label]:
            lbl.configure(width=20 if self.lang == "en" else 15)

    def _update_theme_combo_values(self):
        if not hasattr(self, 'theme_combo'): return
        themes = ["浅色", "深色", "磨砂玻璃", "石板青", "马卡龙", "彩虹", "樱花粉"] if self.lang == "zh" else \
                 ["Default", "Dark Mode", "Frosted Glass", "Slate Teal", "Macaron", "Rainbow", "Sakura"]
        self.theme_combo['values'] = themes
        
        theme_var = self.vars.get("theme")
        if theme_var and theme_var.get():
            current = theme_var.get()
            for i, theme in enumerate(themes):
                for kw in ["Light", "Default", "Dark", "Macaron", "Rainbow", "Frosted", "Glass", "石板", "Teal", "浅色", "深色", "马卡龙", "彩虹", "磨砂", "樱花", "Sakura"]:
                    if kw.lower() in current.lower() and kw.lower() in theme.lower():
                        self.theme_combo.current(i)
                        return
            self.theme_combo.current(0)

    def _update_ratio_combo_values(self):
        if not hasattr(self, 'ratio_combo'): return
        ratios = ["原图 (自由)", "1:1 (微信朋友圈)", "3:4 (小红书)", "4:3", "5:7 (Instagram)", "4:5", "9:16", "3:2", "16:9"] if self.lang == "zh" else \
                 ["Original", "1:1 (WeChat)", "3:4 (LittleRedBook)", "4:3", "5:7 (Instagram)", "4:5", "9:16", "3:2", "16:9"]
        self.ratio_combo['values'] = ratios
        
        ratio_var = self.vars.get("target_ratio")
        if ratio_var and ratio_var.get():
            current = ratio_var.get()
            for i, r in enumerate(ratios):
                if current.split(' (')[0] in r:
                    self.ratio_combo.current(i)
                    return
            self.ratio_combo.current(0)
