# gui/panels/border_panel.py
"""
EN: Border Tool panel for GUI (tkinter version)
CN: 边框工具 GUI 面板（tkinter版本）
"""

import os
import sys
import platform
import subprocess
import json
import tempfile
import shutil
import threading
import time
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer, bootstrap_logos
from concurrent.futures import ThreadPoolExecutor


class ThumbnailStrip(ttk.Frame):
    """
    EN: XHS-style horizontal thumbnail strip for image selection
    CN: 小红书风格的水平样片导航条，用于图片选择
    """
    def __init__(self, parent, lang="en", on_select=None, on_delete=None, on_add=None, on_order_changed=None):
        super().__init__(parent)
        self.lang = lang
        self.on_select = on_select
        self.on_delete = on_delete
        self.on_add = on_add
        self.on_order_changed = on_order_changed
        self.thumbs = {} # path -> photoimage
        self.active_path = None
        self.drag_widget = None # EN: Currently dragging widget / CN: 当前正在拖拽的组件
        self._drag_data = {"x": 0, "y": 0}
        
        # UI Components
        self.canvas = tk.Canvas(self, height=185, bg=ttk.Style().colors.bg, highlightthickness=0)
        self.canvas.pack(side=TOP, fill=X, expand=YES)
        
        self.scrollbar = ttk.Scrollbar(self, orient=HORIZONTAL, command=self.canvas.xview, bootstyle="round")
        self.scrollbar.pack(side=BOTTOM, fill=X)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=NW)
        
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _on_mousewheel(self, event):
        # EN: Support horizontal scrolling with mouse wheel / CN: 支持滚轮水平滑动
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")

    def update_images(self, paths):
        """EN: Load and render thumbnails from list of paths / CN: 从路径列表加载并渲染缩略图"""
        # Clear old
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        if not paths:
            return
            
        for idx, path in enumerate(paths):
            self._create_thumb_widget(path, idx)
            
        # EN: Add "+" button at the end / CN: 在末尾添加“+”按钮
        self._create_add_button()

    def _create_add_button(self):
        frame = ttk.Frame(self.inner_frame, padding=5)
        frame.pack(side=LEFT)
        
        # EN: Square placeholder for + / CN: 用于 + 的方型占位符
        btn = ttk.Label(frame, text="+", font=("Segoe UI", 28, "bold"), 
                       width=5, anchor=CENTER, cursor="hand2", 
                       bootstyle="secondary", padding=40)
        btn.pack()
        btn.bind("<Button-1>", lambda e: self.on_add() if self.on_add else None)
        
        ttk.Label(frame, text="Add" if self.lang == "en" else "添加", 
                 font=("Segoe UI", 8), foreground="gray").pack()

    def _create_thumb_widget(self, path, index):
        from PIL import ImageOps, ImageDraw
        
        container = ttk.Frame(self.inner_frame, padding=2)
        container.pack(side=LEFT)
        
        # EN: Actual frame for the thumbnail with 3px border space / CN: 带有 3px 描边空间的样片容器
        frame = ttk.Frame(container, padding=3, bootstyle="default")
        frame.pack()
        
        lbl = ttk.Label(frame, text="...", cursor="hand2")
        lbl.pack()
        
        # EN: Small Delete button at top-right (Hidden by default, hover to show)
        # CN: 右上角的小删除按钮 (默认隐藏，悬停显示)
        del_btn = ttk.Label(frame, text="×", cursor="hand2", font=("Segoe UI", 12), foreground="gray")
        # del_btn.place() is called in hover events
        del_btn.bind("<Button-1>", lambda e: self.on_delete(path) if self.on_delete else None)

        # EN: Async thumbnail generation / CN: 异步生成缩略图
        def generate():
            try:
                with Image.open(path) as img:
                    # EN: Force 1:1 Square Crop (Increased size) / CN: 强制 1:1 方型裁切 (增加尺寸)
                    img = ImageOps.fit(img, (120, 120), Image.Resampling.LANCZOS)
                    
                    # EN: Create rounded corners with PIL / CN: 使用 PIL 制作 8px 圆角
                    mask = Image.new('L', img.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.rounded_rectangle((0, 0) + img.size, radius=8, fill=255)
                    img.putalpha(mask)
                    
                    # EN: IMPORTANT - Do NOT create PhotoImage in sub-thread
                    # CN: 重要 - 不要在子线程中创建 PhotoImage，否则会导致 Tcl/Tk 内部报错 (AttributeError)
                    processed_img = img.copy()
                    
                    # EN: Safely update UI using the parent frame's after()
                    # CN: 使用父框架的 after() 安全更新 UI
                    def safe_update(pil_img=processed_img, target_lbl=lbl):
                        try:
                            if target_lbl.winfo_exists():
                                # EN: Create PhotoImage in MAIN thread
                                # CN: 在主线程中创建 PhotoImage
                                photo = ImageTk.PhotoImage(pil_img)
                                self.thumbs[path] = photo # EN: Persist reference / CN: 保持引用防止 GC
                                target_lbl.configure(image=photo, text="")
                        except Exception:
                            pass
                    self.after(0, safe_update)
            except Exception:
                pass
                
        self.executor.submit(generate)
        
        # EN: Interaction Events / CN: 交互事件
        def on_enter(e):
            del_btn.place(relx=1.0, rely=0.0, anchor=NE, x=-5, y=5)
            
        def on_leave(e):
            del_btn.place_forget()

        # EN: Drag and Drop Handlers / CN: 拖拽排序逻辑
        def on_drag_start(event):
            self.drag_widget = container
            self._drag_data["x"] = event.x
            self.drag_widget.configure(cursor="fleur")
            # EN: Visually highlight the one being moved / CN: 视觉高亮正在移动的对象
            frame.configure(bootstyle="info")

        def on_drag_motion(event):
            if not self.drag_widget: return
            
            # EN: Calculate global X of parent container / CN: 计算父容器的全局 X 坐标
            current_x = self.drag_widget.winfo_x() + (event.x - self._drag_data["x"])
            
            # EN: Find new insertion point among siblings / CN: 在兄弟组件中寻找新的插入点
            siblings = self.inner_frame.pack_slaves()
            # EN: Exclude ourselves and the "+" button (last child) / CN: 排除自身和末尾的 "+" 按钮
            for other in siblings[:-1]:
                if other == self.drag_widget: continue
                
                other_x = other.winfo_x()
                other_w = other.winfo_width()
                
                # EN: If center point passed, swap order / CN: 如果超过中心点，则交换位置
                if current_x < (other_x + other_w // 2) and self.drag_widget.winfo_x() > other_x:
                    self.drag_widget.pack_forget()
                    self.drag_widget.pack(side=LEFT, before=other)
                    break
                elif current_x > (other_x + other_w // 2) and self.drag_widget.winfo_x() < other_x:
                    self.drag_widget.pack_forget()
                    # EN: To pack AFTER 'other', we need to find the one after 'other'
                    idx = siblings.index(other)
                    if idx + 1 < len(siblings):
                        self.drag_widget.pack(side=LEFT, before=siblings[idx+1])
                    else:
                        # EN: Should not happen because of "+" button, but safe fallback
                        self.drag_widget.pack(side=LEFT)
                    break

        def on_drag_stop(event):
            if not self.drag_widget: return
            self.drag_widget.configure(cursor="hand2")
            # EN: Restore original highlight if it was active / CN: 如果之前是激活态，恢复高亮
            if getattr(lbl, '_img_path', None) == self.active_path:
                frame.configure(bootstyle="primary")
            else:
                frame.configure(bootstyle="default")
            
            self.drag_widget = None
            # EN: Inform order change / CN: 通知顺序已改变
            self._notify_order_changed()

        # EN: Re-bind selection vs drag logic / CN: 重新绑定选择与拖拽逻辑
        # Use B1-Motion for drag start to avoid conflict with Click
        lbl.bind("<Button-1>", on_drag_start, add="+")
        lbl.bind("<B1-Motion>", on_drag_motion)
        lbl.bind("<ButtonRelease-1>", on_drag_stop)
        
        container.bind("<Enter>", on_enter)
        container.bind("<Leave>", on_leave)
        lbl.bind("<Enter>", on_enter) # Ensure child labels also trigger
        # Note: del_btn itself needs to keep showing on enter
        del_btn.bind("<Enter>", lambda e: del_btn.place(relx=1.0, rely=0.0, anchor=NE, x=-5, y=5))
        
        lbl._img_path = path 
        lbl._original_on_click = lambda e: self.on_select(path)
        # Bind original click AFTER drag handlers to see if we moved
        lbl.bind("<Button-1>", lambda e: self.on_select(path), add="+")
        
        # Filename label (shortened)
        fname = os.path.basename(path)
        if len(fname) > 12: fname = fname[:10] + ".."
        ttk.Label(container, text=fname, font=("Segoe UI", 8), foreground="gray").pack()

    def set_active(self, path):
        self.active_path = path
        # EN: Update highlight border / CN: 更新高亮边框 (主色调蓝色 3px 描边)
        for container in self.inner_frame.pack_slaves():
            # The frame is inside the container
            widgets = container.winfo_children()
            if not widgets: continue
            frame = widgets[0]
            lbl_widgets = frame.winfo_children()
            if lbl_widgets:
                lbl = lbl_widgets[0]
                if getattr(lbl, '_img_path', None) == path:
                    frame.configure(bootstyle="primary") # Indicates 3px border in some themes
                else:
                    frame.configure(bootstyle="default")

    def _notify_order_changed(self):
        """EN: Extract current paths from UI order and notify / CN: 从 UI 顺序提取路径并通知"""
        new_paths = []
        for container in self.inner_frame.pack_slaves():
            # Skip the "+" button frame (it doesn't have an _img_path label at idx 0 index 0)
            widgets = container.winfo_children()
            if widgets:
                frame = widgets[0]
                lbl_widgets = frame.winfo_children()
                if lbl_widgets:
                    lbl = lbl_widgets[0]
                    if hasattr(lbl, '_img_path'):
                        new_paths.append(lbl._img_path)
        
        if self.on_order_changed:
            self.on_order_changed(new_paths)


class BorderPanel:
    """
    EN: Border Tool GUI panel
    CN: 边框工具图形界面面板
    """
    
    def __init__(self, parent, lang="en"):
        """
        Args:
            parent: Parent widget / 父部件
            lang: UI language ("zh" or "en") / 界面语言（"zh" 或 "en"）
        """
        self.parent = parent
        self.worker_thread = None
        self.preview_thread = None
        self.preview_job_id = 0  # EN: Preview job marker / CN: 预览任务标记
        self.preview_after_id = None # EN: Debounce timer ID / CN: 防抖计时器 ID
        self.film_list = []
        self.lang = lang  # EN: Use provided language / CN: 使用传入的语言
        self.rotation_var = tk.IntVar(value=0) # EN: Manual rotation state / CN: 手动旋转状态
        
        # EN: Per-image configuration storage / CN: 每张图片的独立配置存储
        self.image_configs = {} # absolute_path -> {params_dict}
        self.current_image_path = None
        self.batch_width_cache = {} # normalized_path -> aspect_ratio
        self.current_batch_paths = [] # Ordered normalized paths
        self._loading_state = False # EN: Guard for trace feedback / CN: 防止监听回环的任务锁
        self.preview_source_cache = {} # EN: path -> {rotation: pil_img}
        
        # EN: Global EXIF flag (Single master switch)
        # CN: 全局 EXIF 标志位，一个开关控制所有字段是否“全局同步”
        self.exif_global_var = tk.BooleanVar(value=False)
        
        # EN: Load layout config for parameter initialization / CN: 加载布局配置用于参数初始化
        self.layout_config = {}
        self.load_layout_config()
        
        self.setup_ui()
        self.load_film_library()
    
    def load_layout_config(self):
        """
        EN: Load layout config from JSON
        CN: 从JSON加载布局配置
        """
        try:
            from core.metadata import MetadataHandler
            config_path = MetadataHandler._resolve_config_path('layouts.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.layout_config = json.load(f)
        except Exception as e:
            # EN: Failed to load, use defaults / CN: 加载失败，使用默认值
            self.layout_config = {}
    
    def setup_ui(self):
        """
        EN: Setup user interface
        CN: 设置用户界面
        """
        # EN: Create Two-Column Layout Container using PanedWindow / CN: 使用可拖动的 PanedWindow 创建双栏布局容器
        self.main_container = ttk.Panedwindow(self.parent, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # EN: Left panel for scrollable settings and pinned bottom button / CN: 固定宽度的左侧容器
        self.left_panel = ttk.Frame(self.main_container, width=750)
        self.left_panel.pack_propagate(False) # Force width to 750px
        self.main_container.add(self.left_panel, weight=0)
        
        # Bottom actions in left side
        self.bottom_left_frame = ttk.Frame(self.left_panel)
        self.bottom_left_frame.pack(side=BOTTOM, fill=X, pady=(10, 0))
        
        # Scrolled settings area inside the remaining left space
        from ttkbootstrap.widgets.scrolled import ScrolledFrame
        self.left_scrolled = ScrolledFrame(self.left_panel, autohide=True)
        self.left_scrolled.pack(side=TOP, fill=BOTH, expand=YES)
        self.left_frame = self.left_scrolled # Directly use ScrolledFrame as parent
        
        self.right_frame = ttk.Frame(self.main_container)
        self.main_container.add(self.right_frame, weight=1) # weight=1 allows it to expand
        
        # EN: Mode selection / CN: 模式选择
        mode_text = "工作模式" if self.lang == "zh" else "Working Mode"
        self.mode_frame = ttk.Labelframe(self.left_frame, text=mode_text, padding=10)
        self.mode_frame.pack(fill=X, pady=(0, 10))
        
        self.mode_var = ttk.StringVar(value="film")
        film_text = "胶片项目" if self.lang == "zh" else "Film Project"
        digital_text = "数码项目" if self.lang == "zh" else "Digital Project"
        self.film_radio = ttk.Radiobutton(self.mode_frame, text=film_text, variable=self.mode_var, 
                       value="film", command=self.on_mode_changed, bootstyle="primary")
        self.film_radio.pack(side=LEFT, padx=10)
        self.digital_radio = ttk.Radiobutton(self.mode_frame, text=digital_text, variable=self.mode_var, 
                       value="digital", command=self.on_mode_changed, bootstyle="primary")
        self.digital_radio.pack(side=LEFT, padx=10)
        
        pure_text = "纯净模式" if self.lang == "zh" else "Pure Mode"
        self.pure_radio = ttk.Radiobutton(self.mode_frame, text=pure_text, variable=self.mode_var, 
                       value="pure", command=self.on_mode_changed, bootstyle="primary")
        self.pure_radio.pack(side=LEFT)
        
        # EN: Input folder / CN: 输入文件夹
        folder_text = "输入文件夹" if self.lang == "zh" else "Input Folder"
        self.folder_frame = ttk.Labelframe(self.left_frame, text=folder_text, padding=10)
        self.folder_frame.pack(fill=X, pady=(0, 10))
        
        input_row = ttk.Frame(self.folder_frame)
        input_row.pack(fill=X, pady=(0, 5))
        
        self.input_folder_var = ttk.StringVar()
        ttk.Entry(input_row, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        refresh_text = "刷新" if self.lang == "zh" else "Refresh"
        self.refresh_button = ttk.Button(input_row, text=refresh_text, command=self.refresh_input_folder, bootstyle="info-outline", width=8)
        self.refresh_button.pack(side=RIGHT, padx=(2, 5))
        browse_text = "浏览" if self.lang == "zh" else "Browse"
        self.browse_button = ttk.Button(input_row, text=browse_text, command=self.select_input_folder, bootstyle="info-outline")
        self.browse_button.pack(side=RIGHT)
        
        no_folder_text = "未选择文件夹" if self.lang == "zh" else "No folder selected"
        self.file_count_label = ttk.Label(self.folder_frame, text=no_folder_text, foreground="gray")
        self.file_count_label.pack(anchor=W)

        # EN: Selection changed listener / CN: 参数变更监听
        self.side_ratio_var = ttk.DoubleVar(value=0.04)
        self.top_ratio_var = ttk.DoubleVar(value=0.04)
        self.bottom_ratio_var = ttk.DoubleVar(value=0.13)
        self.font_scale_var = ttk.DoubleVar(value=0.032)
        self.theme_var = ttk.StringVar(value="light")

        # EN: Setup traces for sync / CN: 设置同步监听
        self.side_ratio_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.top_ratio_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.bottom_ratio_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.font_scale_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        if hasattr(self, 'theme_var'):
            self.theme_var.trace('w', lambda *args: self.on_params_changed(sync_all=True))
        
        # EN: Film selection / CN: 胶片选择
        film_selection_text = "胶片选择" if self.lang == "zh" else "Film Selection"
        self.film_selection_frame = ttk.Labelframe(self.left_frame, text=film_selection_text, padding=10)
        self.film_selection_frame.pack(fill=X, pady=(0, 10))
        
        self.auto_detect_var = ttk.BooleanVar(value=True)
        auto_detect_text = "自动识别胶片（从EXIF）" if self.lang == "zh" else "Auto Detect from EXIF"
        self.auto_detect_check = ttk.Checkbutton(self.film_selection_frame, text=auto_detect_text, 
                       variable=self.auto_detect_var, command=self.on_auto_detect_changed, 
                       bootstyle="round-toggle")
        self.auto_detect_check.pack(anchor=W, pady=(0, 5))
        
        film_row = ttk.Frame(self.film_selection_frame)
        film_row.pack(fill=X)
        manual_text = "手动选择:" if self.lang == "zh" else "Manual Select:"
        self.manual_label = ttk.Label(film_row, text=manual_text)
        self.manual_label.pack(side=LEFT, padx=(0, 10))
        self.film_combo = ttk.Combobox(film_row, state="disabled")
        self.film_combo.pack(side=LEFT, fill=X, expand=YES)
        # EN: Refresh preview when selection changes or Enter is pressed
        # CN: 选择改变或敲击回车时刷新预览
        self.film_combo.bind("<<ComboboxSelected>>", lambda e: self.on_params_changed())
        self.film_combo.bind("<Return>", lambda e: self.on_params_changed())

        # EN: Advanced settings (border parameters) / CN: 高级设置（边框参数）
        advanced_text = "高级设置" if self.lang == "zh" else "Advanced Settings"
        self.advanced_frame = ttk.Labelframe(self.left_frame, text=advanced_text, padding=10)
        self.advanced_frame.pack(fill=X, pady=(0, 10))
        # EN: Advanced settings components
        row1 = ttk.Frame(self.advanced_frame)
        row1.pack(fill=X, pady=2)
        row1.columnconfigure(0, weight=1, uniform="adv")
        row1.columnconfigure(1, weight=1, uniform="adv")
        
        row2 = ttk.Frame(self.advanced_frame)
        row2.pack(fill=X, pady=2)
        row2.columnconfigure(0, weight=1, uniform="adv")
        row2.columnconfigure(1, weight=1, uniform="adv")

        def add_setting_to_grid(parent, label_text, var, col):
            container = ttk.Frame(parent)
            container.grid(row=0, column=col, sticky=EW, padx=2)
            lbl = ttk.Label(container, text=label_text, width=12)
            lbl.pack(side=LEFT)
            entry = ttk.Entry(container, textvariable=var, width=12)
            entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
            entry.bind("<Return>", lambda e: self.on_params_changed())
            return lbl

        self.side_label = add_setting_to_grid(row1, "左右边框" if self.lang == "zh" else "Side Margin", self.side_ratio_var, 0)
        self.top_label = add_setting_to_grid(row1, "顶部留白" if self.lang == "zh" else "Top Margin", self.top_ratio_var, 1)
        self.bottom_label = add_setting_to_grid(row2, "底部留白" if self.lang == "zh" else "Bottom Margin", self.bottom_ratio_var, 0)
        self.font_label = add_setting_to_grid(row2, "字体基础" if self.lang == "zh" else "Font Scale", self.font_scale_var, 1)
        
        row3 = ttk.Frame(self.advanced_frame)
        row3.pack(fill=X, pady=2)
        row3.columnconfigure(0, weight=1, uniform="adv")
        row3.columnconfigure(1, weight=1, uniform="adv")

        # EN: Border Theme selector / CN: 边框主题选择
        theme_container = ttk.Frame(row3)
        theme_container.grid(row=0, column=0, sticky=EW, padx=2)
        self.theme_label = ttk.Label(theme_container, text="边框主题" if self.lang == "zh" else "Border Theme", width=12)
        self.theme_label.pack(side=LEFT)
        self.theme_combo = ttk.Combobox(theme_container, textvariable=self.theme_var, state="readonly", width=20)
        self.theme_combo.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.on_params_changed())
        self._update_theme_combo_values()

        # EN: Manual EXIF Overrides / CN: 手动 EXIF 覆盖
        exif_text = "手动 EXIF 覆盖 (留空则读取原图)" if self.lang == "zh" else "Manual EXIF Overrides (Leave blank to use file EXIF)"
        self.exif_frame = ttk.Labelframe(self.left_frame, text=exif_text, padding=5)
        self.exif_frame.pack(fill=X, pady=(0, 5))

        # EN: Global Sync Switch (Master) / CN: 全局同步主开关
        sync_text = "全局应用" if self.lang == "zh" else "Apply to All"
        self.global_sync_check = ttk.Checkbutton(self.exif_frame, text=sync_text, 
                                               variable=self.exif_global_var, 
                                               command=self.on_params_changed,
                                               bootstyle="round-toggle")
        self.global_sync_check.pack(anchor=W, padx=5, pady=(5, 5))

        # Variables for EXIF overrides
        self.exif_make_var = ttk.StringVar()
        self.exif_model_var = ttk.StringVar()
        self.exif_lens_var = ttk.StringVar()
        self.exif_shutter_var = ttk.StringVar()
        self.exif_aperture_var = ttk.StringVar()
        self.exif_iso_var = ttk.StringVar()

        # EN: Visibility toggles / CN: 显示开关
        self.show_make_var = tk.IntVar(value=1)
        self.show_model_var = tk.IntVar(value=1)
        self.show_shutter_var = tk.IntVar(value=1)
        self.show_aperture_var = tk.IntVar(value=1)
        self.show_iso_var = tk.IntVar(value=1)
        self.show_lens_var = tk.IntVar(value=1)

        # Layout grids - Restored to 3x2 grid
        ex_row1 = ttk.Frame(self.exif_frame)
        ex_row1.pack(fill=X, pady=2)
        ex_row1.columnconfigure(0, weight=1, uniform="exif")
        ex_row1.columnconfigure(1, weight=1, uniform="exif")
        
        ex_row2 = ttk.Frame(self.exif_frame)
        ex_row2.pack(fill=X, pady=2)
        ex_row2.columnconfigure(0, weight=1, uniform="exif")
        ex_row2.columnconfigure(1, weight=1, uniform="exif")
        
        ex_row3 = ttk.Frame(self.exif_frame)
        ex_row3.pack(fill=X, pady=2)
        ex_row3.columnconfigure(0, weight=1, uniform="exif")
        ex_row3.columnconfigure(1, weight=1, uniform="exif")

        def add_exif_field_to_grid(parent, label_text, var, show_var, col):
            container = ttk.Frame(parent)
            container.grid(row=0, column=col, sticky=EW)
            # EN: Visibility toggle / CN: 显示开关
            cb_show = ttk.Checkbutton(container, variable=show_var, command=self.on_params_changed)
            cb_show.pack(side=LEFT, padx=(2, 0))
            
            ttk.Label(container, text=label_text, width=8).pack(side=LEFT)
            entry = ttk.Entry(container, textvariable=var, width=18)
            entry.pack(side=LEFT, padx=(0, 10), fill=X, expand=YES)
            entry.bind("<Return>", lambda e: self.on_params_changed())

        add_exif_field_to_grid(ex_row1, "Make:", self.exif_make_var, self.show_make_var, 0)
        add_exif_field_to_grid(ex_row1, "Model:", self.exif_model_var, self.show_model_var, 1)
        add_exif_field_to_grid(ex_row2, "Shutter:", self.exif_shutter_var, self.show_shutter_var, 0)
        add_exif_field_to_grid(ex_row2, "Aperture:", self.exif_aperture_var, self.show_aperture_var, 1)
        add_exif_field_to_grid(ex_row3, "ISO:", self.exif_iso_var, self.show_iso_var, 0)
        add_exif_field_to_grid(ex_row3, "Lens:", self.exif_lens_var, self.show_lens_var, 1)

        # EN: Process button / CN: 处理按钮 (Pinned to left frame bottom)
        process_text = "开始处理" if self.lang == "zh" else "Start Processing"
        self.process_button = ttk.Button(self.bottom_left_frame, text=process_text, 
                                         command=self.on_process_click, bootstyle="success", width=20)
        self.process_button.pack(pady=(5, 5))
        self.stop_requested = False 
        
        self.progress = ttk.Progressbar(self.bottom_left_frame, mode="determinate", bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(0, 5))
        self.progress.pack_forget()  # Hide initially

        # EN: Preview area / CN: 预览区域 (Now in right_frame)
        preview_text = "预览（显示文件夹第一张图片）" if self.lang == "zh" else "Preview (First Image in Folder)"
        self.preview_frame = ttk.Labelframe(self.right_frame, text=preview_text, padding=10)
        self.preview_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        # EN: Responsive Canvas replacing fixed Label / CN: 响应式 Canvas 替换固定 Label
        bg_color = ttk.Style().lookup("TFrame", "background")
        self.preview_canvas = tk.Canvas(self.preview_frame, bg=bg_color, highlightthickness=0)
        self.preview_canvas.pack(fill=BOTH, expand=YES)
        self.preview_canvas.bind("<Configure>", self.on_preview_resize)

        # EN: Thumbnail Strip (Xiaohongshu Mode) / CN: 样片条（小红书模式）
        self.thumb_strip = ThumbnailStrip(self.right_frame, self.lang, 
                                         on_select=self.on_thumbnail_click,
                                         on_delete=self.on_thumbnail_delete,
                                         on_add=self.on_thumbnail_add,
                                         on_order_changed=self.notify_order_changed)
        self.thumb_strip.pack(fill=X, pady=(0, 10))

        # EN: Rotation controls (Minimalist Icons, No Background) / CN: 旋转控制 (极简图标，无背景)
        self.rotation_frame = ttk.Frame(self.preview_frame)
        self.rotation_frame.pack(side=BOTTOM, pady=(2, 0))
        
        # Pro look: Clickable Labels as buttons for zero-background look
        icon_font = ("Segoe UI", 14, "bold") if platform.system() == "Windows" else ("Helvetica", 14, "bold")
        primary_color = ttk.Style().colors.primary
        
        self.rotate_left_btn = ttk.Label(self.rotation_frame, text="↺", font=icon_font, foreground=primary_color, cursor="hand2")
        self.rotate_left_btn.pack(side=LEFT, padx=15)
        self.rotate_left_btn.bind("<Button-1>", lambda e: self.rotate_left())
        
        self.rotate_right_btn = ttk.Label(self.rotation_frame, text="↻", font=icon_font, foreground=primary_color, cursor="hand2")
        self.rotate_right_btn.pack(side=LEFT, padx=15)
        self.rotate_right_btn.bind("<Button-1>", lambda e: self.rotate_right())
        
        self._current_preview_pil = None
        self._preview_img_ref = None
        self._is_loading_preview = False
        self._preview_error_msg = None
        self._last_canvas_size = (0, 0)
        
        # EN: Log output / CN: 日志输出 (Now in right_frame)
        log_text = "处理日志" if self.lang == "zh" else "Processing Log"
        self.log_frame = ttk.Labelframe(self.right_frame, text=log_text, padding=5)
        self.log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # EN: Auto-detect photos_in / CN: 自动检测 photos_in
        self.auto_detect_photos_in()
        
        # EN: SYNC for initial folder state (Safe point: all UI set up)
        # CN: 初始文件夹状态同步（安全点：所有 UI 已就绪）
        self.refresh_thumb_strip()
    
    def redraw_preview(self):
        """EN: Redraw the preview canvas / CN: 重绘预览画布"""
        if getattr(self, 'preview_canvas', None) is None: return
        w = self.preview_canvas.winfo_width()
        h = self.preview_canvas.winfo_height()
        if w <= 10 or h <= 10: return
        
        self.preview_canvas.delete("all")
        
        if getattr(self, '_current_preview_pil', None):
            img = self._current_preview_pil.copy()
            # Fast downscale preserving aspect ratio
            img.thumbnail((w, h), Image.Resampling.LANCZOS)
            self._preview_img_ref = ImageTk.PhotoImage(img)
            self.preview_canvas.create_image(w//2, h//2, image=self._preview_img_ref, anchor="center")
        else:
            txt = "暂无预览" if self.lang == "zh" else "No preview"
            if getattr(self, '_is_loading_preview', False):
                txt = "正在生成预览..." if self.lang == "zh" else "Rendering preview..."
            elif getattr(self, '_preview_error_msg', None):
                txt = self._preview_error_msg
            self.preview_canvas.create_text(w//2, h//2, text=txt, fill="gray", anchor="center")

    def on_preview_resize(self, event):
        """EN: Handle preview area resize / CN: 处理预览区域缩放"""
        w, h = event.width, event.height
        if getattr(self, '_last_canvas_size', None) == (w, h):
            return
        self._last_canvas_size = (w, h)
        self.redraw_preview()
    
    def update_language(self, lang):
        """
        EN: Update UI language
        CN: 更新界面语言
        """
        self.lang = lang
        
        # EN: Safe check if worker thread is running / CN: 安全检查工作线程是否正在运行
        is_running = self.worker_thread is not None and self.worker_thread.is_alive()
        
        if lang == "zh":
            self.mode_frame.config(text="工作模式")
            self.film_radio.config(text="胶片项目")
            self.digital_radio.config(text="数码项目")
            self.pure_radio.config(text="纯净模式")
            self.folder_frame.config(text="输入文件夹")
            self.refresh_button.config(text="刷新")
            self.browse_button.config(text="浏览")
            self.film_selection_frame.config(text="胶片选择")
            self.auto_detect_check.config(text="自动识别胶片（从EXIF）")
            self.manual_label.config(text="手动选择:")
            self.advanced_frame.config(text="高级设置")
            self.side_label.config(text="左右边框")
            self.side_label.configure(width=12)
            self.top_label.config(text="顶部留白")
            self.top_label.configure(width=12)
            self.bottom_label.config(text="底部留白")
            self.bottom_label.configure(width=12)
            self.font_label.config(text="字体基础")
            self.font_label.configure(width=12)
            self.exif_frame.config(text="手动 EXIF 覆盖 (留空则读取原图)")
            self.global_sync_check.config(text="全局应用")
            self.preview_frame.config(text="预览（显示文件夹第一张图片）")
            self.theme_label.config(text="边框主题")
            self.theme_label.configure(width=12)
            self._update_theme_combo_values()
            self.redraw_preview()
            self.process_button.config(text="开始处理" if not is_running else "停止处理 (Stop)")
            self.log_frame.config(text="处理日志")
            self.update_film_combo_values()
        else:
            self.mode_frame.config(text="Working Mode")
            self.film_radio.config(text="Film Project")
            self.digital_radio.config(text="Digital Project")
            self.pure_radio.config(text="Pure Mode")
            self.folder_frame.config(text="Input Folder")
            self.refresh_button.config(text="Refresh")
            self.browse_button.config(text="Browse")
            self.film_selection_frame.config(text="Film Selection")
            self.auto_detect_check.config(text="Auto Detect from EXIF")
            self.manual_label.config(text="Manual Select:")
            self.advanced_frame.config(text="Advanced Settings")
            self.side_label.config(text="Side Margin")
            self.side_label.configure(width=15)
            self.top_label.config(text="Top Margin")
            self.top_label.configure(width=15)
            self.bottom_label.config(text="Bottom Margin")
            self.bottom_label.configure(width=15)
            self.font_label.config(text="Font Scale")
            self.font_label.configure(width=15)
            self.theme_label.config(text="Border Theme")
            self.theme_label.configure(width=15)
            self._update_theme_combo_values()
            self.exif_frame.config(text="Manual EXIF Overrides (Leave blank to use file EXIF)")
            self.global_sync_check.config(text="Apply to All")
            self.preview_frame.config(text="Preview (First Image in Folder)")
            self.redraw_preview()
            self.process_button.config(text="Start Processing" if not is_running else "Stop Processing (Cancel)")
            self.log_frame.config(text="Processing Log")
            self.update_film_combo_values()
        
        # EN: Update file count label / CN: 更新文件计数标签
        self.update_file_count()
        
        # EN: Refresh log with current language / CN: 使用当前语言刷新日志
        if self.film_list:
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
            self.log(self.get_asset_status_msg())
    
    def update_film_combo_values(self):
        """
        EN: Update film combo box values with current language
        CN: 使用当前语言更新胶片下拉框选项
        """
        if not self.film_list:
            return
        
        placeholder = "-- 请选择胶片 --" if self.lang == "zh" else "-- Select Film --"
        film_names = [placeholder] + [name for name, _ in self.film_list]
        current = self.film_combo.current()
        self.film_combo['values'] = film_names
        self.film_combo.current(current if current >= 0 else 0)
    
    def load_film_library(self):
        """
        EN: Load film library from config
        CN: 从配置文件加载胶片库
        """
        try:
            self.film_list = []
            meta = MetadataHandler()
            if hasattr(meta, 'films_map'):
                for brand, films in meta.films_map.items():
                    for film_name in films.keys():
                        display_name = f"[{brand}] {film_name}"
                        self.film_list.append((display_name, film_name))
            
            self.film_list.sort()
            self.update_film_combo_values()
            self.log(self.get_asset_status_msg())
            
            # EN: Force UI update / CN: 强制 UI 刷新
            self.parent.update_idletasks()
                
        except Exception as e:
            self.log(f"CN: 加载胶片库失败: {e} / EN: Failed to load film library: {e}")

    def rotate_left(self):
        """EN: Rotate preview left / CN: 向左旋转预览"""
        self.rotation_var.set((self.rotation_var.get() - 90) % 360)
        self.on_params_changed()

    def rotate_right(self):
        """EN: Rotate preview right / CN: 向右旋转预览"""
        self.rotation_var.set((self.rotation_var.get() + 90) % 360)
        self.on_params_changed()

    def get_asset_status_msg(self):
        """EN: Generate unified asset status message / CN: 生成统一的资产状态消息"""
        logo_count = 0
        try:
            logo_dir = bootstrap_logos()
            if os.path.exists(logo_dir):
                files = os.listdir(logo_dir)
                logo_count = len([f for f in files if f.lower().endswith(('.svg', '.png'))])
        except Exception:
            pass

        msg_film = f"✓ 已加载 {len(self.film_list)} 种胶片" if self.lang == "zh" else f"✓ Loaded {len(self.film_list)} films"
        msg_logo = f"✓ 已加载 {logo_count} 种相机边框" if self.lang == "zh" else f"✓ Loaded {logo_count} camera logos"
        
        return f"{msg_film}\n{msg_logo}"
    
    def auto_detect_photos_in(self):
        """
        EN: Auto-detect photos_in folder
        CN: 自动检测 photos_in 文件夹
        """
        try:
            if getattr(sys, 'frozen', False):
                working_dir = os.path.dirname(sys.executable)
            else:
                working_dir = os.getcwd()
            
            photos_in = os.path.join(working_dir, "photos_in")
            if os.path.exists(photos_in):
                self.input_folder_var.set(photos_in)
                self.update_file_count()
                # EN: Use refresh_thumb_strip for consistency / CN: 使用 refresh_thumb_strip 保持一致性
                self.refresh_thumb_strip()
                self.detect_layout_and_load_params(photos_in)
        except Exception:
            # EN: Auto-detection failed, silent fail is OK / CN: 自动检测失败，静默失败可接受
            pass

    def refresh_input_folder(self):
        """
        EN: Manually refresh file count for current input folder
        CN: 手动刷新当前输入文件夹的文件计数
        """
        folder = self.input_folder_var.get()
        if not folder or not os.path.exists(folder):
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "请先选择输入文件夹" if self.lang == "zh" else "Please select input folder first"
            messagebox.showwarning(title, msg)
            return

        self.update_file_count()
        # EN: Clear all per-image configs to allow "reshuffle" / CN: 清空所有单图配置以允许色彩重刷/重新加载
        self.image_configs = {}
        
        # EN: Standardize on refresh_thumb_strip for all state sync / CN: 统一使用 refresh_thumb_strip 进行状态同步
        self.refresh_thumb_strip()
        self.detect_layout_and_load_params(folder)
            
        # EN: Log refresh action for user feedback
        # CN: 记录刷新操作，给用户反馈
        msg = "✓ 已刷新文件夹" if self.lang == "zh" else "✓ Folder refreshed"
        self.log(msg)
    
    def detect_layout_and_load_params(self, folder):
        """
        EN: Detect layout from first image and load params from config
        CN: 从第一张图片检测布局并从配置加载参数
        """
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not files:
                return
            
            img_path = os.path.join(folder, files[0])
            meta = MetadataHandler()
            detected_format = meta.detect_batch_layout([img_path])
            
            if detected_format and detected_format in self.layout_config:
                layout_cfg = self.layout_config[detected_format]
                
                # EN: Get the image to determine portrait/landscape / CN: 获取图像以确定竖横
                from PIL import Image
                with Image.open(img_path) as img:
                    w, h = img.size
                    is_portrait = h > w
                
                # EN: Get orientation-specific or fallback params / CN: 获取方向特定或备用参数
                params = layout_cfg.get("portrait" if is_portrait else "landscape", layout_cfg.get("all"))
                
                if params:
                    # EN: Update parameter fields / CN: 更新参数字段
                    self.side_ratio_var.set(params.get('side_ratio', 0.04))
                    self.top_ratio_var.set(params.get('top_ratio', params.get('side_ratio', 0.04)))
                    self.bottom_ratio_var.set(params.get('bottom_ratio', 0.13))
                    self.font_scale_var.set(params.get('font_scale', 0.032))
        except Exception:
            # EN: Failed to detect layout, keep defaults / CN: 无法检测布局，保持默认值
            pass
    
    def select_input_folder(self):
        """
        EN: Open folder selection dialog
        CN: 打开文件夹选择对话框
        """
        folder = filedialog.askdirectory(
            title="选择输入文件夹 Select Input Folder",
            initialdir=self.input_folder_var.get() or os.path.expanduser("~")
        )
        if folder:
            self.input_folder_var.set(folder)
            self.image_configs = {} # EN: New folder = new batch / CN: 新文件夹即为新批次
            self.update_file_count()
            self.refresh_thumb_strip()
            self.detect_layout_and_load_params(folder)
    
    def update_file_count(self):
        """
        EN: Update file count display
        CN: 更新文件数量显示
        """
        folder = self.input_folder_var.get()
        if not folder or not os.path.exists(folder):
            text = "未选择文件夹" if self.lang == "zh" else "No folder selected"
            self.file_count_label.config(text=text, foreground="gray")
            return
        
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            count = len(files)
            if count > 0:
                text = f"✓ 找到 {count} 张照片" if self.lang == "zh" else f"✓ Found {count} photos"
                self.file_count_label.config(text=text, foreground="green")
            else:
                text = "⚠ 文件夹中没有图片" if self.lang == "zh" else "⚠ No images in folder"
                self.file_count_label.config(text=text, foreground="red")
        except Exception as e:
            text = f"错误: {e}" if self.lang == "zh" else f"Error: {e}"
            self.file_count_label.config(text=text, foreground="red")

    def on_thumbnail_delete(self, path):
        """EN: Delete image from the current batch / CN: 从当前批次中删除图片"""
        path_norm = os.path.normcase(os.path.normpath(path))
        if not hasattr(self, 'deleted_paths'):
            self.deleted_paths = set()
        
        self.deleted_paths.add(path_norm)
        if path_norm in self.image_configs:
            del self.image_configs[path_norm]
        
        # EN: Clean up current selection if it's the deleted one
        # CN: 如果删除的是当前选中的，清除状态
        if self.current_image_path and os.path.normcase(os.path.normpath(self.current_image_path)) == path_norm:
            self.current_image_path = None
            
        self.refresh_thumb_strip()

    def on_thumbnail_add(self):
        """EN: Add images to the batch / CN: 在批次中追加图片"""
        files = filedialog.askopenfilenames(
            title="选择图片 Select Images",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if files:
            # EN: Initialize configs for new files / CN: 为新文件初始化配置
            for f in files:
                p = os.path.normpath(f)
                if p not in self.image_configs:
                    self.image_configs[p] = {'theme': self.theme_var.get()}
            self.refresh_thumb_strip()
    def refresh_thumb_strip(self):
        """EN: Refresh the strip based on image_configs / CN: 基于配置列表刷新样片条"""
        if not hasattr(self, 'deleted_paths'):
            self.deleted_paths = set()

        # EN: Always sync with current folder if possible / CN: 如果可能，始终与当前文件夹同步
        folder = self.input_folder_var.get()
        if folder and os.path.exists(folder):
            files = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            print(f"DEBUG [RefreshScan]: scanning {folder}, found {len(files)} files")
            for f in files:
                p = os.path.normcase(os.path.normpath(os.path.join(folder, f)))
                # EN: Skip if explicitly deleted / CN: 如果已明确删除，则跳过
                if p in self.deleted_paths:
                    continue
                if p not in self.image_configs:
                    # EN: Pre-fill with defaults / CN: 预填默认配置
                    self.image_configs[p] = {'theme': self.theme_var.get()}
        
        # EN: Use current keys as definitive path list / CN: 使用配置字典中的键作为权威路径列表
        paths = sorted(list(self.image_configs.keys()))
        print(f"DEBUG [Refresh]: batch established with {len(paths)} unique paths")
        
        # EN: Normalize all paths for authoritative order / CN: 规格化所有路径以建立权威顺序
        self.current_batch_paths = [os.path.normcase(os.path.normpath(p)) for p in paths]
        
        # EN: Update width cache - Use SYNC for small batches, ASYNC for large to avoid lag
        # CN: 更新宽度缓存 - 小批次同步执行以防竞态，大批次异步执行防卡顿
        if len(self.current_batch_paths) < 50:
            self._update_batch_width_cache(self.current_batch_paths, async_mode=False)
        else:
            self._update_batch_width_cache(self.current_batch_paths, async_mode=True)
            
        self.thumb_strip.update_images(paths)
        if paths:
            # Keep active if still exists, else first
            active = self.current_image_path if self.current_image_path in paths else paths[0]
            self.on_thumbnail_click(active)

    def _update_batch_width_cache(self, paths, async_mode=True):
        """EN: Scan images to cache aspect ratios / CN: 扫描图片以缓存宽高比"""
        def scan_work():
            new_cache = {}
            for p in paths:
                normalized_p = os.path.normcase(os.path.normpath(p))
                try:
                    with Image.open(p) as img:
                        w, h = img.size
                        new_cache[normalized_p] = w / h
                except Exception:
                    new_cache[normalized_p] = 1.6 # Default
            self.batch_width_cache = new_cache
            # EN: Trigger preview refresh / CN: 触发预览刷新
            if self.current_image_path and os.path.normcase(os.path.normpath(self.current_image_path)) in self.batch_width_cache:
                self.parent.after(0, self.on_params_changed)

        if async_mode:
            threading.Thread(target=scan_work, daemon=True).start()
        else:
            scan_work()

    def on_thumbnail_click(self, path):
        """EN: Handle image selection from strip / CN: 处理从样片条选择图片"""
        if self.current_image_path == path:
            return
            
        # 1. EN: Save current UI state to old image / CN: 将当前 UI 状态保存到旧图
        if self.current_image_path:
            self._save_current_to_state(self.current_image_path)
            
        # 2. EN: Switch active path / CN: 切换当前路径
        self.current_image_path = path
        self.thumb_strip.set_active(path)
        
        # 3. EN: Load state for new image / CN: 加载新图的配置
        self._load_state_to_ui(path)

    def _save_current_to_state(self, path):
        """EN: Save UI values to per-image config / CN: 将 UI 值存入单图配置"""
        self.image_configs[path] = {
            'side_ratio': self.side_ratio_var.get(),
            'top_ratio': self.top_ratio_var.get(),
            'bottom_ratio': self.bottom_ratio_var.get(),
            'font_scale': self.font_scale_var.get(),
            'theme': self.theme_var.get(),
            'rotation': self.rotation_var.get(),
            'rainbow_index': getattr(self, 'current_rainbow_index', -1), # Persistence
            'auto_detect': self.auto_detect_var.get(),
            'film_combo': self.film_combo.get(),
            'exif': {
                'Make': self.exif_make_var.get().strip(),
                'Model': self.exif_model_var.get().strip(),
                'Lens': self.exif_lens_var.get().strip(),
                'Shutter': self.exif_shutter_var.get().strip(),
                'Aperture': self.exif_aperture_var.get().strip(),
                'ISO': self.exif_iso_var.get().strip(),
                'show_make': self.show_make_var.get(),
                'show_model': self.show_model_var.get(),
                'show_shutter': self.show_shutter_var.get(),
                'show_aperture': self.show_aperture_var.get(),
                'show_iso': self.show_iso_var.get(),
                'show_lens': self.show_lens_var.get(),
                # EN: Store global synchronization flag / CN: 存储全局同步标志位
                'global_lock': self.exif_global_var.get()
            }
        }

    def _load_state_to_ui(self, path):
        """EN: Load per-image config to UI / CN: 将单图配置加载回 UI"""
        self._loading_state = True
        try:
            if path not in self.image_configs:
                # EN: Try to initialize with auto-detected layout / CN: 尝试以自动识别的布局初始化
                self.detect_layout_and_load_params(os.path.dirname(path))
                # EN: For Macaron, generate an initial index from batch / CN: 对于马卡龙，从批次序号生成初始索引
                try:
                    idx = self.current_batch_paths.index(os.path.normcase(os.path.normpath(path)))
                    self.current_rainbow_index = idx % 9
                except (ValueError, AttributeError):
                    self.current_rainbow_index = 0
            else:
                cfg = self.image_configs[path]
                # EN: Update UI variables (Guard will prevent feedback to config)
                # CN: 更新 UI 变量（任务锁会防止反向覆盖配置）
                if 'side_ratio' in cfg: self.side_ratio_var.set(cfg['side_ratio'])
                if 'top_ratio' in cfg: self.top_ratio_var.set(cfg['top_ratio'])
                if 'bottom_ratio' in cfg: self.bottom_ratio_var.set(cfg['bottom_ratio'])
                if 'font_scale' in cfg: self.font_scale_var.set(cfg['font_scale'])
                if 'theme' in cfg: self.theme_var.set(cfg['theme'])
                if 'film_combo' in cfg: self.film_combo.set(cfg['film_combo'])
                
                self.rotation_var.set(cfg.get('rotation', 0))
                self.auto_detect_var.set(cfg.get('auto_detect', True))
                exif = cfg.get('exif', {})
                # Show flags with default=1
                self.show_make_var.set(exif.get('show_make', 1))
                self.show_model_var.set(exif.get('show_model', 1))
                self.show_shutter_var.set(exif.get('show_shutter', 1))
                self.show_aperture_var.set(exif.get('show_aperture', 1))
                self.show_iso_var.set(exif.get('show_iso', 1))
                self.show_lens_var.set(exif.get('show_lens', 1))

                # EN: Load EXIF content - ONLY if not globally locked
                # CN: 加载 EXIF 内容 - 仅在未处于“全局应用”状态时从图片配置中加载
                if not self.exif_global_var.get():
                    self.exif_make_var.set(exif.get('Make', ''))
                    self.exif_model_var.set(exif.get('Model', ''))
                    self.exif_lens_var.set(exif.get('Lens', ''))
                    self.exif_shutter_var.set(exif.get('Shutter', ''))
                    self.exif_aperture_var.set(exif.get('Aperture', ''))
                    self.exif_iso_var.set(exif.get('ISO', ''))
                
                self.on_auto_detect_changed() # Update combo state
                # EN: We no longer set mode_var here to keep it global
                # CN: 此处不再设置 mode_var，以保持全局一致性
        finally:
            self._loading_state = False
            # EN: Trigger final preview for this path / CN: 触发该路径的最终预览
            self.update_preview_for_path(path)

    def update_preview_for_path(self, img_path):
        """
        EN: Render specific image and show bordered preview (with debouncing).
        CN: 渲染指定图片并展示带边框的预览（带防抖）。
        """
        if self.preview_after_id:
            self.parent.after_cancel(self.preview_after_id)
            self.preview_after_id = None

        self.preview_after_id = self.parent.after(300, lambda: self._do_render_preview(img_path))

    def _do_render_preview(self, img_path):
        """EN: Actual render logic / CN: 实际的渲染逻辑"""
        try:
            # EN: Respect manual film when auto-detect is off / CN: 关闭自动识别时尊重手动胶片输入
            manual_film = None
            if self.mode_var.get() == "film" and not self.auto_detect_var.get():
                film_input = self.film_combo.get().strip()
                if film_input and not film_input.startswith("--"):
                    manual_film = film_input
                    for display_name, keyword in self.film_list:
                        if film_input == display_name:
                            manual_film = keyword
                            break

            is_digital = self.mode_var.get() == "digital"
            is_pure = self.mode_var.get() == "pure"

            # EN: Bump preview job id to avoid stale UI updates / CN: 提升预览任务编号以避免旧线程覆盖最新界面
            self.preview_job_id += 1
            job_id = self.preview_job_id

            self._is_loading_preview = True
            self._current_preview_pil = None
            self._preview_error_msg = None
            self.redraw_preview()

            def worker(img_path, job_mark, is_digital_mode, is_pure_mode, manual_film_keyword, manual_rotation):
                t_total_start = time.perf_counter()
                render_timings = {}
                try:
                    # EN: Check if the source image is already cached for this rotation
                    # CN: 检查该旋转角度下的源图是否已被缓存
                    cache_entry = self.preview_source_cache.get(img_path, {})
                    source_img = cache_entry.get(manual_rotation)
                    
                    if source_img is None:
                        # EN: Cache miss - load, rotate, and scale once / CN: 缓存未命中 - 仅执行一次加载、旋转和缩放
                        t_load_start = time.perf_counter()
                        with Image.open(img_path) as raw_img:
                            if raw_img.format == 'JPEG':
                                raw_img.draft(raw_img.mode, (2400, 2400)) # 2x of 1200
                            img = ImageOps.exif_transpose(raw_img)
                            if manual_rotation != 0:
                                img = img.rotate(-manual_rotation, expand=True)
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            
                            # Pre-scale to preview size (1200)
                            w, h = img.size
                            scale = 1200 / max(w, h)
                            source_img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
                        
                        render_timings['load_rotate'] = time.perf_counter() - t_load_start
                        render_timings['resize'] = 0 # Included in load_rotate for cache miss
                        # Store in cache
                        self.preview_source_cache[img_path] = {manual_rotation: source_img}
                    else:
                        render_timings['load_rotate'] = 0
                        render_timings['resize'] = 0
                    
                    t_meta_start = time.perf_counter()
                    meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
                    data = meta.get_data(img_path, is_digital_mode=is_digital_mode, manual_film=manual_film_keyword)
                    t_meta = time.perf_counter() - t_meta_start
                    
                    # EN: Apply custom layout params to preview / CN: 将自定义布局参数应用到预览
                    custom_layout = {
                        "side": self.side_ratio_var.get(),
                        "top": self.top_ratio_var.get(),
                        "bottom": self.bottom_ratio_var.get(),
                        "font_scale": self.font_scale_var.get()
                    }
                    if 'layout' in data:
                        data['layout'].update(custom_layout)
                    else:
                        data['layout'] = custom_layout
                    
                    # EN: Apply manual rotation / CN: 应用手动旋转
                    data['manual_rotation'] = self.rotation_var.get()
                    
                    # EN: Apply manual EXIF overrides / CN: 应用手动 EXIF 覆盖
                    manual_exif = {
                        'Make': self.exif_make_var.get().strip(),
                        'Model': self.exif_model_var.get().strip(),
                        'LensModel': self.exif_lens_var.get().strip(),
                        'ExposureTimeStr': self.exif_shutter_var.get().strip(),
                        'FNumber': self.exif_aperture_var.get().strip(),
                        'ISO': self.exif_iso_var.get().strip(),
                        'show_make': self.show_make_var.get(),
                        'show_model': self.show_model_var.get(),
                        'show_shutter': self.show_shutter_var.get(),
                        'show_aperture': self.show_aperture_var.get(),
                        'show_iso': self.show_iso_var.get(),
                        'show_lens': self.show_lens_var.get()
                    }
                    for k, v in manual_exif.items():
                        if v is not None and v != "":
                            data[k] = v

                    renderer = FilmRenderer()
                    # EN: Downscale target edge for faster preview while keeping shadow / CN: 降低分辨率加快预览同时保留阴影
                    # EN: Pass the selected theme / CN: 传递当前选中的主题 (light/dark/rainbow/fuji_rainbow)
                    theme_str = self.theme_var.get()
                    if self.lang == "zh":
                        # EN: Mapping for Chinese UI items / CN: 中文 UI 项映射
                        theme_map = {
                            "富士": "fuji_rainbow",
                            "马卡龙": "rainbow",
                            "深色": "dark", 
                            "浅色": "light"
                        }
                    theme_map = {
                        "sakura": "sakura", "樱花粉": "sakura", "Sakura": "sakura",
                        "macaron": "macaron", "马卡龙": "macaron", "Macaron": "macaron",
                        "rainbow": "rainbow", "彩虹": "rainbow", "Rainbow": "rainbow",
                        "dark": "dark", "深色": "dark", "Dark": "dark",
                        "light": "light", "浅色": "light", "Light": "light", "Default": "light"
                    }
                    theme_val = "light"
                    theme_str_lower = theme_str.lower()
                    for k, v in theme_map.items():
                        if k.lower() in theme_str_lower:
                            theme_val = v
                            break

                    # EN: For rainbow themes, use persistent index or calculate physical range
                    # CN: 对于彩虹主题，使用持久化的色彩索引或计算物理范围
                    r_index = 0
                    r_total = 1 
                    r_range = (0.0, 1.0)
                    
                    if theme_val in ["macaron", "sakura"]:
                        # EN: Macaron Mode is always relative to batch position to support drag updates
                        # CN: 马卡龙模式始终相对于批次位置，以支持拖拽热更新
                        try:
                            idx = self.current_batch_paths.index(os.path.normcase(os.path.normpath(img_path)))
                            r_index = idx % 9
                        except (ValueError, AttributeError):
                            r_index = 0
                    elif theme_val == "rainbow":
                        # EN: Calculate range based on cache if available
                        # CN: 基于缓存计算物理范围（实现预览与批次同步）
                        norm_img_path = os.path.normcase(os.path.normpath(img_path))
                        if self.batch_width_cache and self.current_batch_paths:
                            # EN: Calculate total width based STRICTLY on current batch
                            # CN: 严格基于当前批次计算总宽度
                            total_rel_w = sum(self.batch_width_cache.get(os.path.normcase(os.path.normpath(p)), 1.6) 
                                             for p in self.current_batch_paths)
                            curr_accum = 0.0
                            found = False
                            for p in self.current_batch_paths:
                                p_norm = os.path.normcase(os.path.normpath(p))
                                if p_norm == norm_img_path:
                                    w = self.batch_width_cache.get(p_norm, 1.6)
                                    r_range = (curr_accum / total_rel_w, (curr_accum + w) / total_rel_w)
                                    found = True
                                    # DEBUG Path info
                                    print(f"DEBUG [PreviewMatch]: match found! index={self.current_batch_paths.index(p)}, range={r_range}")
                                    break
                                curr_accum += self.batch_width_cache.get(p_norm, 1.6)
                            
                            if not found:
                                print(f"DEBUG [PreviewMatch]: NO MATCH for {norm_img_path}")
                                print(f"DEBUG [PreviewMatch]: batch_list[0]={self.current_batch_paths[0] if self.current_batch_paths else 'EMPTY'}")
                            
                            # DEBUG
                            print(f"DEBUG [Preview]: path={os.path.basename(img_path)}, found={found}, r_range={r_range}, total_rel_w={total_rel_w}")

                    # EN: Memory-based render call / CN: 基于内存的渲染调用
                    final_pil = renderer.process_image(img_path, data, None, 
                                                     target_long_edge=1200, 
                                                     manual_rotation=manual_rotation,
                                                     theme=theme_val,
                                                     is_pure=is_pure_mode,
                                                     rainbow_index=r_index,
                                                     rainbow_total=r_total,
                                                     rainbow_range=r_range,
                                                     timing_results=render_timings,
                                                     source_img=source_img)

                    # EN: Final image for display (Already flattened to RGB in renderer)
                    img_copy = final_pil.copy()

                    def apply_image():
                        if job_mark != getattr(self, 'preview_job_id', None):
                            return
                        self._is_loading_preview = False
                        self._current_preview_pil = img_copy
                        self.redraw_preview()
                        
                        # EN: Log performance report / CN: 记录性能报告
                        total_time = time.perf_counter() - t_total_start
                        log_msg = f"\n--- Performance Report ({os.path.basename(img_path)}) ---"
                        log_msg += f"\n[Step 1] Metadata: {t_meta*1000:.1f}ms"
                        log_msg += f"\n[Step 2] Render Breakdown:"
                        log_msg += f"\n  - Load & Rotate: {render_timings.get('load_rotate', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Resize: {render_timings.get('resize', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Layout: {render_timings.get('layout_calc', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Canvas: {render_timings.get('canvas_paste', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Logo Render: {render_timings.get('logo_render', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Text Main (Load/Draw): {render_timings.get('text_main_load', 0)*1000:.1f}/{render_timings.get('text_main_render', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Text Sub (Load/Draw): {render_timings.get('text_sub_load', 0)*1000:.1f}/{render_timings.get('text_sub_render', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Shadow: {render_timings.get('shadow', 0)*1000:.1f}ms"
                        log_msg += f"\n  - Save: {render_timings.get('save', 0)*1000:.1f}ms"
                        log_msg += f"\n[Step 3] Total Cycle: {total_time*1000:.1f}ms"
                        log_msg += "\n" + "-"*40
                        self.log(log_msg)

                    self.parent.after(0, apply_image)

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    error_msg = str(e)
                    def apply_error(msg=error_msg):
                        if job_mark != getattr(self, 'preview_job_id', None):
                            return
                        fallback = f"预览失败: {msg}" if self.lang == "zh" else f"Preview failed: {msg}"
                        try:
                            # EN: Fallback to raw thumbnail if render fails / CN: 渲染失败时降级为原图缩略图
                            with Image.open(img_path) as img:
                                img = img.convert("RGB")
                                img.thumbnail((2000, 2000))
                                img_copy = img.copy()
                            self._is_loading_preview = False
                            self._current_preview_pil = img_copy
                            self.redraw_preview()
                        except Exception:
                            self._is_loading_preview = False
                            self._current_preview_pil = None
                            self._preview_error_msg = fallback
                            self.redraw_preview()

                    self.parent.after(0, apply_error)

            # EN: Start thread / CN: 启动线程
            self.preview_thread = threading.Thread(
                target=worker, 
                args=(img_path, job_id, is_digital, is_pure, manual_film, self.rotation_var.get()),
                daemon=True
            )
            self.preview_thread.start()

        except Exception as e:
            fallback = f"预览失败: {e}" if self.lang == "zh" else f"Preview failed: {e}"
            self._preview_error_msg = fallback
            self.redraw_preview()
    
    def on_mode_changed(self):
        """
        EN: Handle mode change
        CN: 处理模式切换
        """
        mode = self.mode_var.get()
        is_film = mode == "film"
        is_pure = mode == "pure"

        if is_film:
            # EN: Use a stable packing order to avoid conflicts
            # CN: 使用稳定的 pack 顺序，避免布局冲突挂载
            self.film_selection_frame.pack(fill=X, pady=(0, 10), after=self.folder_frame)
        else:
            self.film_selection_frame.pack_forget()

        # EN: We keep EXIF frame visible even in Pure Mode as requested
        # CN: 应用户要求，即使在纯净模式下也保持 EXIF 覆盖面板显示
        self.exif_frame.pack(fill=X, pady=(0, 5), after=self.advanced_frame)

        self.on_params_changed()
    
    def on_auto_detect_changed(self):
        """
        EN: Handle auto-detect toggle
        CN: 处理自动检测切换
        """
        if self.auto_detect_var.get():
            self.film_combo.config(state="disabled")
        else:
            self.film_combo.config(state="normal")  # EN: Allow user input / CN: 允许用户输入
    
    def on_params_changed(self, sync_all=False):
        """EN: Triggered when any parameter field changes / CN: 参数变更时触发"""
        if self._loading_state:
            return

        # EN: If sync_all (Theme), broadcast to ALL / CN: 如果是全局同步（如主题），广播到所有图片
        if sync_all and self.current_batch_paths:
            curr_theme = self.theme_var.get().lower()
            is_macaron = "macaron" in curr_theme or "马卡龙" in curr_theme
            is_rainbow = "rainbow" in curr_theme or "彩虹" in curr_theme
            theme_str = "rainbow" if is_rainbow else ("macaron" if is_macaron else self.theme_var.get())
            
            for p in self.current_batch_paths:
                if p not in self.image_configs:
                    self.image_configs[p] = {}
                self.image_configs[p]['theme'] = theme_str
        
        # EN: Always update CURRENT image config / CN: 始终更新当前图片的配置
        if self.current_image_path:
            if self.current_image_path not in self.image_configs:
                self.image_configs[self.current_image_path] = {}
            
            self.image_configs[self.current_image_path].update({
                'side_ratio': self.side_ratio_var.get(),
                'top_ratio': self.top_ratio_var.get(),
                'bottom_ratio': self.bottom_ratio_var.get(),
                'font_scale': self.font_scale_var.get(),
                'theme': self.theme_var.get()
            })
            
            # EN: Handle EXIF Global Synchronization / CN: 处理 EXIF 全局同步逻辑
            if self.exif_global_var.get() and self.current_batch_paths:
                # EN: Map internal keys to UI variables / CN: 映射内部键名到 UI 变量
                exif_map = {
                    'Make': self.exif_make_var,
                    'Model': self.exif_model_var,
                    'Shutter': self.exif_shutter_var,
                    'Aperture': self.exif_aperture_var,
                    'ISO': self.exif_iso_var,
                    'Lens': self.exif_lens_var
                }
                
                # EN: Broadcast values to ALL image configs / CN: 将值广播到所有图片配置中
                for p in self.current_batch_paths:
                    if p not in self.image_configs:
                        self.image_configs[p] = {}
                    if 'exif' not in self.image_configs[p]:
                        self.image_configs[p]['exif'] = {}
                    
                    for field, var in exif_map.items():
                        self.image_configs[p]['exif'][field] = var.get().strip()
                    
                    # Also sync the lock state itself
                    self.image_configs[p]['exif']['global_lock'] = True

            self.update_preview_for_path(self.current_image_path)

    def notify_order_changed(self, new_paths):
        """EN: Handle reordering from ThumbnailStrip / CN: 处理来自样片条的排序变动"""
        self.current_batch_paths = [os.path.normcase(os.path.normpath(p)) for p in new_paths]
        print(f"DEBUG [Order]: new order established with {len(self.current_batch_paths)} paths")
        
        if self.current_image_path:
            self.update_preview_for_path(self.current_image_path)

    def on_process_click(self):
        """EN: Toggle between start and stop / CN: 在开始与停止之间切换"""
        if self.worker_thread and self.worker_thread.is_alive():
            # EN: Request stop / CN: 请求停止
            self.stop_requested = True
            msg = "⚡ 正在停止..." if self.lang == "zh" else "⚡ Stopping..."
            self.process_button.config(text=msg, bootstyle="danger", state="disabled")
        else:
            # EN: Start normal processing / CN: 开始正常处理
            self.start_processing()

    def start_processing(self):
        """
        EN: Start border processing
        CN: 开始边框处理
        """
        # EN: Force sync THEME only to all batch items before starting
        # CN: 开始处理前强制将当前 UI 主题同步给所有批次项目（保持彩虹连贯性）
        self.on_params_changed(sync_all=True)
        
        input_folder = self.input_folder_var.get()
        if not input_folder or not os.path.exists(input_folder):
            msg = "请先选择输入文件夹！" if self.lang == "zh" else "Please select input folder first!"
            messagebox.showwarning("警告" if self.lang == "zh" else "Warning", msg)
            return
        
        # 1. EN: Save current active config first / CN: 首先保存当前激活的图片配置
        if self.current_image_path:
            self._save_current_to_state(self.current_image_path)

        # 2. EN: Prepare UI / CN: 准备 UI
        self.stop_requested = False
        msg = "停止处理 (Stop)" if self.lang == "zh" else "Stop Processing (Cancel)"
        self.process_button.config(text=msg, bootstyle="danger-outline")
        
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress['value'] = 0

        # 3. EN: Setup output folder / CN: 设置输出文件夹
        working_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
        output_folder = os.path.join(working_dir, "photos_out")
        os.makedirs(output_folder, exist_ok=True)

        # 4. EN: Collect global fallbacks (from current UI) / CN: 收集全局兜底配置（从当前 UI）
        global_cfg = {
            'is_digital': self.mode_var.get() == "digital",
            'is_pure': self.mode_var.get() == "pure",
            'theme': self.theme_var.get(),
            'rotation': self.rotation_var.get(),
            'layout': {
                "side": self.side_ratio_var.get(),
                "top": self.top_ratio_var.get(),
                "bottom": self.bottom_ratio_var.get(),
                "font_scale": self.font_scale_var.get()
            },
            'exif': {
                'Make': self.exif_make_var.get().strip(),
                'Model': self.exif_model_var.get().strip(),
                'LensModel': self.exif_lens_var.get().strip(),
                'ExposureTimeStr': self.exif_shutter_var.get().strip(),
                'FNumber': self.exif_aperture_var.get().strip(),
                'ISO': self.exif_iso_var.get().strip(),
                'show_make': self.show_make_var.get(),
                'show_model': self.show_model_var.get(),
                'show_shutter': self.show_shutter_var.get(),
                'show_aperture': self.show_aperture_var.get(),
                'show_iso': self.show_iso_var.get(),
                'show_lens': self.show_lens_var.get()
            }
        }
        # Film specific fallback
        manual_film = None
        if not global_cfg['is_digital'] and not self.auto_detect_var.get():
            manual_film = self.film_combo.get()
        global_cfg['manual_film'] = manual_film

        # 5. EN: Start worker / CN: 启动工作线程
        self.worker_thread = threading.Thread(
            target=self.process_worker,
            args=(input_folder, output_folder, global_cfg),
            daemon=True
        )
        self.worker_thread.start()

    def process_worker(self, input_dir, output_dir, global_cfg):
        """
        EN: Worker thread for processing (Upgraded for Per-Image Config)
        CN: 处理工作线程（已升级支持多图独立配置）
        """
        try:
            # EN: Use authoritative current_batch_paths / CN: 使用权威的 current_batch_paths
            if not self.current_batch_paths:
                self.refresh_thumb_strip()
            
            files = self.current_batch_paths
            total = len(files)
            
            if total == 0:
                self.log("CN: [!] 文件夹内未找到图片" if self.lang=="zh" else "EN: [!] No images found")
                return
            
            # EN: Use cached widths or re-calculate
            relative_widths = []
            total_rel_w = 0.0
            for img_path in files:
                p_norm = os.path.normcase(os.path.normpath(img_path))
                rel_w = self.batch_width_cache.get(p_norm)
                if rel_w is None:
                    try:
                        with Image.open(img_path) as img:
                            w, h = img.size
                            rel_w = w / h
                    except:
                        rel_w = 1.6
                relative_widths.append(rel_w)
                total_rel_w += rel_w

            # DEBUG
            print(f"DEBUG [Batch]: total_rel_w={total_rel_w}, count={len(files)}")

            current_w_accum = 0.0
            
            bootstrap_logos()
            renderer = FilmRenderer()
            meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
            
            for i, img_path in enumerate(files):
                # EN: Check stop flag / CN: 检查停止标志
                if self.stop_requested:
                    self.log("\n⚡ 用户手动终止处理" if self.lang == "zh" else "\n⚡ User canceled processing")
                    break

                # EN: Calculate physical slice / CN: 计算物理切片比例
                t_start = current_w_accum / total_rel_w
                current_w_accum += relative_widths[i]
                t_end = current_w_accum / total_rel_w

                # EN: Load per-image config or fallback / CN: 读取各图专属配置或使用兜底
                cfg = self.image_configs.get(img_path)
                
                # EN: Work Mode is now strictly global / CN: 工作模式现在严格全局化
                is_digital = global_cfg['is_digital']
                is_pure = global_cfg['is_pure']
                theme_str = cfg.get('theme', global_cfg['theme']) if cfg else global_cfg['theme']
                
                # EN: Resolve manual film / CN: 解析手动胶片
                m_film = global_cfg['manual_film']
                if cfg and not cfg.get('auto_detect', True):
                    m_film = cfg.get('film_combo')
                # Resolve keyword from display name if needed
                for display_name, keyword in self.film_list:
                    if m_film == display_name:
                        m_film = keyword
                        break

                # EN: Resolve data / CN: 解析数据
                data = meta.get_data(img_path, is_digital_mode=is_digital, manual_film=m_film)
                
                # EN: Apply overrides / CN: 应用覆盖参数
                c_layout = cfg if cfg else global_cfg['layout']
                data['layout'].update({
                    "side": c_layout.get('side_ratio', 0.04),
                    "top": c_layout.get('top_ratio', 0.04),
                    "bottom": c_layout.get('bottom_ratio', 0.13),
                    "font_scale": c_layout.get('font_scale', 0.032)
                })
                
                c_exif = cfg.get('exif') if cfg else global_cfg['exif']
                if c_exif:
                    for k, v in c_exif.items():
                        if v is not None and v != "": # Make -> Make, Model -> Model etc
                            key = k if k != 'Lens' else 'LensModel'
                            key = key if key != 'Shutter' else 'ExposureTimeStr'
                            key = key if key != 'Aperture' else 'FNumber'
                            data[key] = v

                # EN: Theme mapping / CN: 主题值转换
                # EN: Theme mapping with priority (Macaron/Rainbow first)
                # CN: 带有优先级的主题映射 (马卡龙/彩虹优先匹配)
                # EN: Theme mapping (Support both localized names and internal keys)
                t_map = {
                    "sakura": "sakura", "樱花粉": "sakura", "Sakura": "sakura",
                    "macaron": "macaron", "马卡龙": "macaron", "Macaron": "macaron",
                    "rainbow": "rainbow", "彩虹": "rainbow", "Rainbow": "rainbow",
                    "dark": "dark", "深色": "dark", "Dark": "dark",
                    "light": "light", "浅色": "light", "Light": "light", "Default": "light"
                }
                theme_val = "light"
                theme_str_lower = theme_str.lower()
                for k, v in t_map.items():
                    if k.lower() in theme_str_lower:
                        theme_val = v
                        break

                # EN: UI Feedback / CN: UI 反馈
                self.parent.after(0, lambda c=i+1, t=total, fn=os.path.basename(img_path): self._process_feedback(c, t, fn))

                # EN: For both Rainbow and Macaron, use batch physical order/range.
                # CN: 彩虹与马卡龙均采用批次物理顺序/范围。
                r_range = (t_start, t_end)
                r_idx = i % 9 # Position-based indexing

                # EN: Generate 001_ prefix for Macaron/Rainbow to follow sorted order
                # CN: 为马卡龙/彩虹模式生成 001_ 前缀，以遵循调整后的排序
                out_prefix = ""
                if theme_val in ["macaron", "rainbow", "sakura"]:
                    out_prefix = f"{i+1:03d}_"

                renderer.process_image(img_path, data, output_dir, 
                                     manual_rotation=cfg.get('rotation', global_cfg['rotation']) if cfg else global_cfg['rotation'],
                                     theme=theme_val,
                                     is_pure=is_pure,
                                     rainbow_index=r_idx,
                                     rainbow_total=total,
                                     rainbow_range=r_range,
                                     output_prefix=out_prefix)

            self.parent.after(0, lambda: self.on_processing_complete({'success': True, 'processed': total}))
        except Exception as e:
            import traceback
            self.parent.after(0, lambda msg=traceback.format_exc(): self.on_processing_error(msg))

    def _process_feedback(self, current, total, filename):
        percent = int((current / total) * 100)
        self.progress.config(value=percent)
        self.log(f"[{current}/{total}] {filename}")

    def on_processing_complete(self, result):
        """
        EN: Handle processing completion
        CN: 处理完成回调
        """
        self.progress.pack_forget()
        self.process_button.config(
            text="开始处理" if self.lang == "zh" else "Start Processing",
            bootstyle="primary-solid",
            state="normal"
        )

        if result.get('success'):
            self.log("\n✓ " + "="*50)
            msg1 = "✓ 处理完成！" if self.lang == "zh" else "✓ Processing complete!"
            msg2 = f"✓ 已处理 {result.get('processed', 0)} 张照片" if self.lang == "zh" else f"✓ Processed {result.get('processed', 0)} photos"
            self.log(msg1)
            self.log(msg2)
            self.log("✓ " + "="*50)

            # EN: Show result dialog and ask to open folder / CN: 显示结果对话框并询问是否打开文件夹
            title = "完成" if self.lang == "zh" else "Complete"
            msg = f"处理完成！\n\n已处理 {result.get('processed', 0)} 张照片\n\n是否打开输出文件夹？" if self.lang == "zh" else f"Processing complete!\n\nProcessed {result.get('processed', 0)} photos\n\nOpen output folder?"
            response = messagebox.askyesno(title, msg)
            if response:
                try:
                    if getattr(sys, 'frozen', False):
                        working_dir = os.path.dirname(sys.executable)
                    else:
                        working_dir = os.getcwd()
                    output_folder = os.path.join(working_dir, "photos_out")

                    # EN: Cross-platform folder opening / CN: 跨平台打开文件夹
                    system = platform.system()
                    if system == "Windows":
                        os.startfile(output_folder)
                    elif system == "Darwin":  # macOS
                        subprocess.run(["open", output_folder])
                    else:  # Linux and others
                        subprocess.run(["xdg-open", output_folder])
                except Exception as e:
                    error_title = "错误" if self.lang == "zh" else "Error"
                    error_msg = f"无法打开文件夹:\n{e}" if self.lang == "zh" else f"Failed to open folder:\n{e}"
                    messagebox.showerror(error_title, error_msg)
        else:
            msg = "\n✗ 处理失败" if self.lang == "zh" else "\n✗ Processing failed"
            self.log(msg)
            self.log(f"✗ {result.get('message', 'Unknown error')}")
            title = "错误" if self.lang == "zh" else "Error"
            messagebox.showerror(title, result.get('message', 'Unknown error'))

    def on_processing_error(self, error_msg):
        """
        EN: Handle processing error
        CN: 处理错误回调
        """
        self.progress.pack_forget()
        self.process_button.config(state="normal")

        msg = f"\n✗ 发生错误\n{error_msg}" if self.lang == "zh" else f"\n✗ Error occurred\n{error_msg}"
        self.log(msg)
        title = "错误" if self.lang == "zh" else "Error"
        msg = (f"处理过程中发生错误：\n\n{error_msg[:200]}...\n\n如需帮助请联系：xjames007@gmail.com") if self.lang == "zh" else \
              (f"Error during processing:\n\n{error_msg[:200]}...\n\nFor help contact: xjames007@gmail.com")
        messagebox.showerror(title, msg)

    def log(self, message):
        """
        EN: Append message to log
        CN: 添加消息到日志
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _update_theme_combo_values(self):
        """
        EN: Update theme combo box values with current language
        CN: 使用当前语言更新主题下拉框选项
        """
        if self.lang == "zh":
            themes = ["浅色", "深色", "马卡龙", "彩虹", "樱花粉"]
        else:
            themes = ["Default", "Dark Mode", "Macaron", "Rainbow", "Sakura"]

        current = self.theme_var.get()
        self.theme_combo['values'] = themes

        # EN: Try to maintain selection
        # CN: 尝试保持之前的选择
        selected = False
        if current:
            for i, theme in enumerate(themes):
                # EN: Search by keyword / CN: 通过关键词搜索进行对齐
                for kw in ["Light", "Default", "Dark", "Macaron", "Rainbow", "浅色", "深色", "马卡龙", "彩虹"]:
                    if kw in current and kw in theme:
                        # EN: Rainbow vs Macaron disambiguation / CN: 区分彩虹与马卡龙
                        if "Rainbow" in current and "Rainbow" not in theme: continue
                        if "彩虹" in current and "彩虹" not in theme: continue
                        self.theme_combo.current(i)
                        selected = True
                        break
                if selected: break

        if not selected and themes:
            self.theme_combo.current(0)
