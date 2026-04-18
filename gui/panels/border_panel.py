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
import threading
import time
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFilter



from gui.components import ThumbnailStrip, ExifGroup, SettingsGroup
from gui.controllers.border_controller import BorderController


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
        
        # EN: Variables for EXIF overrides / CN: 手动 EXIF 覆盖变量
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
        
        # EN: Controller for decoupled logic / CN: 用于逻辑解耦的控制器
        self.controller = BorderController(
            lang=self.lang,
            log_callback=self.log,
            progress_callback=self._process_feedback,
            complete_callback=self.on_processing_complete,
            error_callback=self.on_processing_error
        )
        
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
        self.font_scale_var = tk.DoubleVar(value=0.032)
        self.theme_var = tk.StringVar(value="light")
        self.use_lens_branding_var = tk.BooleanVar(value=True) # EN: Global lens branding toggle / CN: 镜头专属标识全局开关

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
        settings_vars = {
            "side": self.side_ratio_var, "top": self.top_ratio_var,
            "bottom": self.bottom_ratio_var, "font": self.font_scale_var,
            "theme": self.theme_var, "branding": self.use_lens_branding_var
        }
        self.settings_group = SettingsGroup(self.left_frame, lang=self.lang, 
                                           on_change=self.on_params_changed,
                                           vars=settings_vars)
        self.settings_group.pack(fill=X, pady=(0, 10))

        # EN: Manual EXIF Overrides / CN: 手动 EXIF 覆盖
        exif_vars = {
            "make": self.exif_make_var, "model": self.exif_model_var,
            "shutter": self.exif_shutter_var, "aperture": self.exif_aperture_var,
            "iso": self.exif_iso_var, "lens": self.exif_lens_var
        }
        show_vars = {
            "make": self.show_make_var, "model": self.show_model_var,
            "shutter": self.show_shutter_var, "aperture": self.show_aperture_var,
            "iso": self.show_iso_var, "lens": self.show_lens_var
        }
        from gui.components import ExifGroup
        self.exif_group = ExifGroup(self.left_frame, lang=self.lang, 
                                   on_change=self.on_params_changed,
                                   exif_vars=exif_vars, 
                                   show_vars=show_vars,
                                   global_sync_var=self.exif_global_var)
        self.exif_group.pack(fill=X, pady=(0, 5))

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
            self.settings_group.update_language(lang)
            self.exif_group.update_language(lang)
            self.thumb_strip.update_language(lang)
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
            self.settings_group.update_language(lang)
            self.exif_group.update_language(lang)
            self.thumb_strip.update_language(lang)
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
            # EN: Use safe getters to avoid TclError when entry boxes are temporarily empty during typing
            # CN: 使用安全获取方法，避免用户在输入时输入框临时为空导致的 TclError
            'side_ratio': self._get_float_safe(self.side_ratio_var),
            'top_ratio': self._get_float_safe(self.top_ratio_var),
            'bottom_ratio': self._get_float_safe(self.bottom_ratio_var),
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

            def worker(img_path, job_mark, is_digital_mode, is_pure_mode, film_keyword, rotation):
                try:
                    # EN: Call controller to do the heavy lifting
                    final_pil, report = self.controller.get_preview_image(
                        img_path=img_path,
                        is_digital=is_digital_mode,
                        is_pure=is_pure_mode,
                        manual_film=film_keyword,
                        rotation=rotation,
                        image_configs=self.image_configs,
                        batch_width_cache=self.batch_width_cache,
                        current_batch_paths=self.current_batch_paths,
                        use_branding=self.use_lens_branding_var.get()
                    )

                    if final_pil and hasattr(final_pil, 'copy'):
                        img_copy = final_pil.copy()
                    else:
                        raise Exception("Render returned empty image")

                    def apply_image():
                        if job_mark != getattr(self, 'preview_job_id', None): return
                        self._is_loading_preview = False
                        self._current_preview_pil = img_copy
                        self.redraw_preview()
                        
                        # EN: Log performance / CN: 记录性能
                        log_msg = f"\n--- Performance Report ({os.path.basename(img_path)}) ---"
                        log_msg += f"\n[Step 1] Metadata: {report['metadata']*1000:.1f}ms"
                        log_msg += f"\n[Step 2] Render Breakdown:"
                        for step, t in report['render_breakdown'].items():
                            log_msg += f"\n  - {step}: {t*1000:.1f}ms"
                        log_msg += f"\n[Step 3] Total Cycle: {report['total']*1000:.1f}ms\n"
                        self.log(log_msg)

                    self.parent.after(0, apply_image)

                except Exception as e:
                    def apply_error(msg=str(e)):
                        if job_mark != getattr(self, 'preview_job_id', None): return
                        fallback = f"预览失败: {msg}" if self.lang == "zh" else f"Preview failed: {msg}"
                        try:
                            with Image.open(img_path) as img:
                                img = img.convert("RGB")
                                img.thumbnail((2000, 2000))
                                img_copy = img.copy()
                            self._is_loading_preview = False
                            self._current_preview_pil = img_copy
                            self.redraw_preview()
                        except:
                            self._is_loading_preview = False
                            self._current_preview_pil = None
                            self._preview_error_msg = fallback
                            self.redraw_preview()
                    self.parent.after(0, apply_error)

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
            is_frosted = "frosted" in curr_theme or "磨砂" in curr_theme or "glass" in curr_theme
            
            theme_str = "rainbow" if is_rainbow else ("macaron" if is_macaron else ("frosted" if is_frosted else self.theme_var.get()))
            
            for p in self.current_batch_paths:
                if p not in self.image_configs:
                    self.image_configs[p] = {}
                self.image_configs[p]['theme'] = theme_str
        
        # EN: Always update CURRENT image config / CN: 始终更新当前图片的配置
        if self.current_image_path:
            if self.current_image_path not in self.image_configs:
                self.image_configs[self.current_image_path] = {}
            
            self.image_configs[self.current_image_path].update({
                'side_ratio': self._get_float_safe(self.side_ratio_var),
                'top_ratio': self._get_float_safe(self.top_ratio_var),
                'bottom_ratio': self._get_float_safe(self.bottom_ratio_var),
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
            # EN: Request stop via controller / CN: 通过控制器请求停止
            self.controller.request_stop()
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
        try:
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
                },
                'use_branding': self.use_lens_branding_var.get()
            }
            # Film specific fallback
            manual_film = None
            if not global_cfg['is_digital'] and not self.auto_detect_var.get():
                manual_film = self.film_combo.get()
            global_cfg['manual_film'] = manual_film

            # 5. EN: Start worker via controller / CN: 通过控制器启动工作线程
            def run_work():
                self.controller.run_batch(
                    files=self.current_batch_paths,
                    output_dir=output_folder,
                    global_cfg=global_cfg,
                    image_configs=self.image_configs,
                    batch_width_cache=self.batch_width_cache,
                    film_list=self.film_list
                )

            self.worker_thread = threading.Thread(
                target=run_work,
                daemon=True
            )
            self.worker_thread.start()

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


    def _get_float_safe(self, var, default=0.0):
        """EN: Safe get for Tkinter DoubleVar / CN: 安全获取 Tkinter DoubleVar 内容"""
        try:
            val = var.get()
            return float(val) if val is not None else default
        except:
            return default
