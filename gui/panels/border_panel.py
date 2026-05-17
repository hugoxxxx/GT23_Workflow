# gui/panels/border_panel.py
import os
import sys
import platform
import subprocess
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

from gui.components import ThumbnailStrip, ExifGroup, SettingsGroup, AestheticGroup
from gui.controllers.border_controller import BorderController
from core.layout.calculator import LayoutCalculator
from tkinter import simpledialog
import concurrent.futures

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
        self.preview_after_id = None # EN: Debounce timer ID / CN: 防抖计时器 ID
        self.film_list = []
        self.lang = lang
        
        # EN: Concurrency management (#20) / CN: 并发管理
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        # EN: Controller for decoupled logic / CN: 用于逻辑解耦的控制器
        self.controller = BorderController(
            lang=self.lang,
            log_callback=self.log,
            progress_callback=self._process_feedback,
            complete_callback=self.on_processing_complete,
            error_callback=self.on_processing_error
        )
        
        defaults = self.controller.get_default_layout_paddings()
        
        # --- State Variables Consolidation ---
        self.mode_var = tk.StringVar(value="film")
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        
        self.left_px_var = tk.StringVar(value=str(defaults["left_px"]))
        self.right_px_var = tk.StringVar(value=str(defaults["right_px"]))
        self.top_px_var = tk.StringVar(value=str(defaults["top_px"]))
        self.bottom_px_var = tk.StringVar(value=str(defaults["bottom_px"]))
        
        self.font_scale_var = tk.StringVar(value=str(defaults["font_scale"]))
        self.font_sub_px_var = tk.StringVar(value=str(defaults["font_sub_px"]))
        self.font_offset_px_var = tk.StringVar(value="0")
        self.font_main_path_var = tk.StringVar(value="Default")
        self.font_sub_path_var = tk.StringVar(value="Default")
        self.font_spacing_var = tk.StringVar(value=str(defaults["font_spacing"]))
        
        self.v_offset_var = tk.IntVar(value=0)
        self.h_offset_var = tk.IntVar(value=0)
        self._prev_v_offset = 0
        self._prev_h_offset = 0
        
        self.target_ratio_var = tk.StringVar(value="Original")
        self.theme_var = tk.StringVar(value="light")
        self.auto_detect_var = tk.BooleanVar(value=True)
        self.rotation_var = tk.IntVar(value=0)
        self.sync_lr_var = tk.BooleanVar(value=True)
        self.use_lens_branding_var = tk.BooleanVar(value=True)
        
        self.v_offset_var.trace_add("write", lambda *a: self._force_int(self.v_offset_var))
        self.h_offset_var.trace_add("write", lambda *a: self._force_int(self.h_offset_var))
        
        self.exif_global_var = tk.BooleanVar(value=False)
        self.exif_make_var = tk.StringVar()
        self.exif_model_var = tk.StringVar()
        self.exif_lens_var = tk.StringVar()
        self.exif_shutter_var = tk.StringVar()
        self.exif_aperture_var = tk.StringVar()
        self.exif_iso_var = tk.StringVar()
        
        self.show_make_var = tk.IntVar(value=1)
        self.show_model_var = tk.IntVar(value=1)
        self.show_shutter_var = tk.IntVar(value=1)
        self.show_aperture_var = tk.IntVar(value=1)
        self.show_iso_var = tk.IntVar(value=1)
        self.show_lens_var = tk.IntVar(value=1)
        
        self._is_syncing_lr = False
        self._param_shadow = {
            "left": str(defaults["left_px"]), 
            "right": str(defaults["right_px"]), 
            "top": str(defaults["top_px"]), 
            "bottom": str(defaults["bottom_px"])
        }
        # EN: Baseline defaults for "Original" mode (Never modified)
        # CN: “原图”模式的基准默认值（初始化后不再修改）
        self._baseline_params = dict(self._param_shadow)
        # --------------------------------------
        
        self.layout_config = self.controller.load_layout_config()
        self.setup_ui()
        self.load_film_library()
        self.load_font_library()

        # EN: Auto-load photos_in if exists / CN: 自动加载 photos_in 文件夹（如果存在）
        default_in = os.path.join(os.getcwd(), "photos_in")
        if os.path.exists(default_in):
            self.input_folder_var.set(default_in)
            self.refresh_input_folder()
            
        # EN: Initial load of preset lists / CN: 初始加载预设列表
        self.refresh_preset_lists()

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
        
        self.mode_var.set("film")
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
        
        # self.input_folder_var initialized at top
        ttk.Entry(input_row, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        refresh_text = "刷新" if self.lang == "zh" else "Refresh"
        self.refresh_button = ttk.Button(input_row, text=refresh_text, command=self.refresh_input_folder, bootstyle="outline-primary", width=8)
        self.refresh_button.pack(side=RIGHT, padx=(2, 5))
        browse_text = "浏览" if self.lang == "zh" else "Browse"
        self.browse_button = ttk.Button(input_row, text=browse_text, command=self.select_input_folder, bootstyle="outline-primary")
        self.browse_button.pack(side=RIGHT)
        
        no_folder_text = "未选择文件夹" if self.lang == "zh" else "No folder selected"
        self.file_count_label = ttk.Label(self.folder_frame, text=no_folder_text, foreground="gray")
        self.file_count_label.pack(anchor=W)

        # EN: Output folder / CN: 输出文件夹
        out_text = "输出文件夹" if self.lang == "zh" else "Output Folder"
        self.out_frame = ttk.Labelframe(self.left_frame, text=out_text, padding=10)
        self.out_frame.pack(fill=X, pady=(0, 10))
        
        out_row = ttk.Frame(self.out_frame)
        out_row.pack(fill=X)
        
        ttk.Entry(out_row, textvariable=self.output_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        self.out_browse_btn = ttk.Button(out_row, text=browse_text, command=self.select_output_folder, bootstyle="outline-primary")
        self.out_browse_btn.pack(side=RIGHT)

        # EN: Initialize default output / CN: 初始化默认输出路径
        working_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
        self.output_folder_var.set(os.path.join(working_dir, "photos_out"))

        self.left_px_var.trace_add('write', lambda *args: self._sync_lr(self.left_px_var, self.right_px_var))
        self.right_px_var.trace_add('write', lambda *args: self._sync_lr(self.right_px_var, self.left_px_var))
        
        # EN: Only dropdowns and Booleans trigger immediate redraw
        # CN: 仅下拉框与布尔开关触发立即重绘，输入框改为失焦/回车重绘
        self.theme_var.trace('w', lambda *args: self.on_params_changed(sync_all=True))
        self.target_ratio_var.trace('w', self._on_ratio_changed_aesthetic)
        self.use_lens_branding_var.trace('w', lambda *args: self.on_params_changed(sync_all=True))
        self.auto_detect_var.trace('w', lambda *args: self.on_params_changed(sync_all=True))
        
        # EN: Film selection / CN: 胶片选择
        film_selection_text = "胶片选择" if self.lang == "zh" else "Film Selection"
        self.film_selection_frame = ttk.Labelframe(self.left_frame, text=film_selection_text, padding=10)
        self.film_selection_frame.pack(fill=X, pady=(0, 10))
        
        # self.auto_detect_var initialized earlier to prevent trace crash
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
        self.film_combo.bind("<<ComboboxSelected>>", lambda e: self.on_params_changed())
        self.film_combo.bind("<Return>", lambda e: self.on_params_changed())

        # EN: Composition & Style / CN: 构图与风格
        aesthetic_vars = {
            "target_ratio": self.target_ratio_var,
            "theme": self.theme_var
        }
        self.aesthetic_group = AestheticGroup(self.left_frame, lang=self.lang,
                                             on_change=self.on_params_changed,
                                             vars=aesthetic_vars,
                                             on_save_preset=self.on_save_border_preset,
                                             on_delete_preset=self.on_delete_border_preset,
                                             on_apply_preset=self.on_apply_border_preset)
        self.aesthetic_group.pack(fill=X, pady=(0, 10))

        # EN: Advanced settings (border parameters) / CN: 高级设置（边框参数）
        settings_vars = {
            "left": self.left_px_var, "right": self.right_px_var,
            "top": self.top_px_var, "bottom": self.bottom_px_var,
            "font": self.font_scale_var, "font_sub": self.font_sub_px_var,
            "font_offset": self.font_offset_px_var,
            "theme": self.theme_var,
            "branding": self.use_lens_branding_var,
            "sync_lr": self.sync_lr_var,
            "target_ratio": self.target_ratio_var,
            "v_offset": self.v_offset_var,
            "h_offset": self.h_offset_var,
            "font_main_path": self.font_main_path_var,
            "font_sub_path": self.font_sub_path_var,
            "font_spacing": self.font_spacing_var,
        }
        self.settings_group = SettingsGroup(self.left_frame, lang=self.lang, 
                                           on_change=self.on_params_changed,
                                           on_sync_similar=self.on_sync_similar_click,
                                           vars=settings_vars)
        self.settings_group.pack(fill=X, pady=(0, 10))
        
        # EN: Overflow warning label / CN: 溢出提醒标签
        self.overflow_warning_label = ttk.Label(self.left_frame, text="", bootstyle="danger")
        self.overflow_warning_label.pack(fill=X, pady=(0, 5))

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
        self.exif_group = ExifGroup(self.left_frame, lang=self.lang, 
                                   on_change=self.on_params_changed,
                                   exif_vars=exif_vars, 
                                   show_vars=show_vars,
                                   global_sync_var=self.exif_global_var,
                                   on_save_favorite=self.on_save_metadata_preset,
                                   on_apply_favorite=self.on_apply_metadata_preset)
        self.exif_group.pack(fill=X, pady=(0, 10))

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
        
        # EN: Pixel info label / CN: 像素规格标签
        self.preview_info_label = ttk.Label(self.preview_frame, text="", bootstyle="secondary")
        self.preview_info_label.pack(anchor=NW, padx=2, pady=(0, 5))
        
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
        log_label_text = "处理日志" if self.lang == "zh" else "Processing Log"
        self.log_frame = ttk.Labelframe(self.right_frame, text=log_label_text, padding=5)
        self.log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=8, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # EN: Auto-detect / CN: 自动检测
        self.auto_detect_photos_in()
        self.refresh_thumb_strip()
        
        # EN: Force initial mode sync / CN: 强制初始模式同步
        self.on_mode_changed()
    
    def redraw_preview(self):
        """EN: Redraw the preview canvas / CN: 重绘预览画布"""
        if getattr(self, 'preview_canvas', None) is None: return
        w = self.preview_canvas.winfo_width()
        h = self.preview_canvas.winfo_height()
        if w <= 10 or h <= 10: return
        
        self.preview_canvas.delete("all")
        
        if getattr(self, '_current_preview_pil', None):
            img = self._current_preview_pil.copy()
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
        """EN: Update UI language / CN: 更新界面语言"""
        self.lang = lang
        is_running = self.worker_thread is not None and self.worker_thread.is_alive()
        
        texts = {
            "zh": {
                "mode_frame": "工作模式", "film_radio": "胶片项目", "digital_radio": "数码项目", "pure_radio": "纯净模式",
                "folder_frame": "输入文件夹", "refresh_button": "刷新", "browse_button": "浏览", "film_selection_frame": "胶片选择",
                "auto_detect_check": "自动识别胶片（从EXIF）", "manual_label": "手动选择:",
                "process_button": "开始处理" if not is_running else "停止处理 (Stop)",
                "log_frame": "处理日志", "preview_frame": "预览（显示文件夹第一张图片）"
            },
            "en": {
                "mode_frame": "Working Mode", "film_radio": "Film Project", "digital_radio": "Digital Project", "pure_radio": "Pure Mode",
                "folder_frame": "Input Folder", "refresh_button": "Refresh", "browse_button": "Browse", "film_selection_frame": "Film Selection",
                "auto_detect_check": "Auto Detect from EXIF", "manual_label": "Manual Select:",
                "process_button": "Start Processing" if not is_running else "Stop Processing (Cancel)",
                "log_frame": "Processing Log", "preview_frame": "Preview (First Image in Folder)"
            }
        }[lang]
        
        self.mode_frame.config(text=texts["mode_frame"])
        self.film_radio.config(text=texts["film_radio"])
        self.digital_radio.config(text=texts["digital_radio"])
        self.pure_radio.config(text=texts["pure_radio"])
        self.folder_frame.config(text=texts["folder_frame"])
        self.refresh_button.config(text=texts["refresh_button"])
        self.browse_button.config(text=texts["browse_button"])
        self.film_selection_frame.config(text=texts["film_selection_frame"])
        self.auto_detect_check.config(text=texts["auto_detect_check"])
        self.manual_label.config(text=texts["manual_label"])
        self.process_button.config(text=texts["process_button"])
        self.log_frame.config(text=texts["log_frame"])
        self.preview_frame.config(text=texts["preview_frame"])
        
        self.settings_group.update_language(lang)
        self.aesthetic_group.update_language(lang)
        self.exif_group.update_language(lang)
        self.thumb_strip.update_language(lang)
        self.redraw_preview()
        self.update_film_combo_values()
        
        self.update_file_count()
        if self.film_list:
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
            self.log(self.controller.get_asset_status_msg(len(self.film_list)))
    
    def update_film_combo_values(self):
        """EN: Update film combo / CN: 更新胶片下拉框选项"""
        if not self.film_list: return
        placeholder = "-- 请选择胶片 --" if self.lang == "zh" else "-- Select Film --"
        film_names = [placeholder] + [name for name, _ in self.film_list]
        current = self.film_combo.current()
        self.film_combo['values'] = film_names
        self.film_combo.current(current if current >= 0 else 0)
    
    def load_film_library(self):
        """EN: Load film library via controller / CN: 通过控制器加载胶片库"""
        self.film_list = self.controller.load_film_library()
        self.update_film_combo_values()
        self.log(self.controller.get_asset_status_msg(len(self.film_list)))
        self.parent.update_idletasks()

    def load_font_library(self):
        """EN: Load font library via controller / CN: 通过控制器加载字体库"""
        fonts = self.controller.load_font_library()
        self.settings_group.set_font_list(fonts)
        self.log(f"CN: 已加载 {len(fonts)} 个外部字体 / EN: Loaded {len(fonts)} external fonts")

    def rotate_left(self):
        self.rotation_var.set((self.rotation_var.get() - 90) % 360)
        self.on_params_changed()

    def rotate_right(self):
        self.rotation_var.set((self.rotation_var.get() + 90) % 360)
        self.on_params_changed()

    def auto_detect_photos_in(self):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        default_photos_in = os.path.join(script_dir, "photos_in")
        if os.path.exists(default_photos_in):
            count = self.controller.scan_folder(default_photos_in)
            if count > 0:
                all_paths = self.controller.state.get_paths()
                self._update_batch_width_cache(all_paths)
                self.refresh_thumb_strip()
                self.update_file_count()
                self.log(f"CN: 已自动检测到 photos_in 文件夹，共 {count} 张图片 / EN: Auto-detected photos_in folder with {count} images")

    def refresh_input_folder(self):
        folder = self.controller.input_folder
        if not folder: return
        
        # EN: Reset compositional offsets to default / CN: 重置构图平移参数为默认值
        self.v_offset_var.set(0)
        self.h_offset_var.set(0)
        self.sync_lr_var.set(True)
        self.font_offset_px_var.set("0")
        
        count = self.controller.scan_folder(folder)
        all_paths = self.controller.state.get_paths()
        self._update_batch_width_cache(all_paths)
        self.controller.clear_all_configs()
        self.refresh_thumb_strip()
        self.update_file_count()
        self.log(f"CN: 已刷新输入文件夹并恢复默认参数，共 {count} 张图片 / EN: Refreshed folder and restored defaults, total {count} images")
        
        # EN: Force redraw and sync to apply resets
        # CN: 强制重绘并同步，以应用重置后的构图
        self.on_params_changed(sync_all=True)
        self.detect_layout_and_load_params(folder)

    def detect_layout_and_load_params(self, folder):
        layout = self.controller.detect_layout_from_folder_as_dict(folder)
        if layout:
            self._apply_config_to_ui(layout)
    
    def select_input_folder(self):
        folder = filedialog.askdirectory(
            title="选择输入文件夹 Select Input Folder",
            initialdir=self.input_folder_var.get() or os.path.expanduser("~")
        )
        if folder:
            self.input_folder_var.set(folder)
            self.controller.scan_folder(folder) # EN: Mandatory scan / CN: 必须调用扫描逻辑
            self.controller.clear_all_configs()
            all_paths = self.controller.state.get_paths()
            self._update_batch_width_cache(all_paths) # EN: Sync cache / CN: 同步缓存
            self.update_file_count()
            self.refresh_thumb_strip()
            self.detect_layout_and_load_params(folder)
    
    def update_file_count(self):
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
        path_norm = os.path.normcase(os.path.normpath(path))
        self.controller.remove_from_batch(path_norm)
        if getattr(self, 'current_image_path', None) == path:
            self.current_image_path = None
            self._current_preview_pil = None
            self.redraw_preview()
        self.refresh_thumb_strip()
        self.update_file_count()

    def on_thumbnail_add(self):
        paths = filedialog.askopenfilenames(
            title="Select Images", filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.tiff")]
        )
        if paths:
            self.controller.add_to_batch(paths)
            self._update_batch_width_cache(paths)
            self.refresh_thumb_strip()
            self.update_file_count()

    def refresh_thumb_strip(self):
        all_paths = self.controller.state.get_paths()
        self.thumb_strip.update_images(all_paths)
        active = getattr(self, 'current_image_path', None)
        if active in all_paths:
            self.thumb_strip.set_active(active)
        elif all_paths:
            self.on_thumbnail_click(all_paths[0])

    def _update_batch_width_cache(self, paths, async_mode=True):
        def scan_one(p):
            try:
                p_norm = os.path.normcase(os.path.normpath(p))
                if self.controller.state.get_width(p_norm) is None:
                    # EN: Protect image open with semaphore (#5)
                    with self.controller.state.image_limit:
                        with Image.open(p) as img:
                            w, h = img.size
                            self.controller.update_aspect_ratio_cache(p, w/h)
            except: pass

        if async_mode:
            for p in paths:
                self.executor.submit(scan_one, p)
        else:
            for p in paths:
                scan_one(p)

    def on_thumbnail_click(self, path):
        if getattr(self, 'current_image_path', None) == path: return
        if getattr(self, 'current_image_path', None):
            self._save_current_to_state(self.current_image_path)
        self.current_image_path = path
        self.thumb_strip.set_active(path)
        self._load_state_to_ui(path)
        # EN: Reset shadow state to current image's values to avoid false deltas
        # CN: 切换预览图时同步更新影子状态，避免产生误报的差异检测
        self._param_shadow = {
            "left": self.left_px_var.get(), "right": self.right_px_var.get(),
            "top": self.top_px_var.get(), "bottom": self.bottom_px_var.get()
        }

    def _get_config_from_ui(self):
        """EN: Retrieve standard Python DTO dictionary from Tkinter widgets / CN: 从 UI 变量中提取标准的纯 Python 字典配置"""
        return {
            'mode': self.mode_var.get(),
            'left_px': self._get_int_safe(self.left_px_var, 180),
            'right_px': self._get_int_safe(self.right_px_var, 180),
            'top_px': self._get_int_safe(self.top_px_var, 180),
            'bottom_px': self._get_int_safe(self.bottom_px_var, 585),
            'font_scale': self._get_int_safe(self.font_scale_var, 144),
            'font_sub_px': self._get_int_safe(self.font_sub_px_var, 112),
            'font_v_offset': self._get_int_safe(self.font_offset_px_var, 0),
            'font_main_path': self.font_main_path_var.get(),
            'font_sub_path': self.font_sub_path_var.get(),
            'v_offset': self._get_int_safe(self.v_offset_var, 0),
            'h_offset': self._get_int_safe(self.h_offset_var, 0),
            'theme': self.theme_var.get(),
            'rotation': self._get_int_safe(self.rotation_var, 0),
            'auto_detect': bool(self.auto_detect_var.get()),
            'film_combo': self.film_combo.get(),
            'sync_lr': bool(self.sync_lr_var.get()),
            'target_ratio': self.target_ratio_var.get(),
            'font_spacing': self._get_int_safe(self.font_spacing_var, 0),
            'exif_global': bool(self.exif_global_var.get()),
            'branding': bool(self.use_lens_branding_var.get()),
            'exif': {
                'Make': self.exif_make_var.get().strip(),
                'Model': self.exif_model_var.get().strip(),
                'Lens': self.exif_lens_var.get().strip(),
                'Shutter': self.exif_shutter_var.get().strip(),
                'Aperture': self.exif_aperture_var.get().strip(),
                'ISO': self.exif_iso_var.get().strip(),
                'show_make': self._get_int_safe(self.show_make_var, 1),
                'show_model': self._get_int_safe(self.show_model_var, 1),
                'show_shutter': self._get_int_safe(self.show_shutter_var, 1),
                'show_aperture': self._get_int_safe(self.show_aperture_var, 1),
                'show_iso': self._get_int_safe(self.show_iso_var, 1),
                'show_lens': self._get_int_safe(self.show_lens_var, 1)
            }
        }

    def _apply_config_to_ui(self, cfg):
        """EN: Set Tkinter variables from standard Python DTO / CN: 从标准的纯 Python 字典配置中设置 UI 变量"""
        if not cfg: return
        self._loading_state = True
        try:
            def set_val(var, val):
                if var and hasattr(var, 'set'): var.set(val)
                
            if 'mode' in cfg: set_val(self.mode_var, cfg['mode'])
            if 'left_px' in cfg: set_val(self.left_px_var, cfg['left_px'])
            if 'right_px' in cfg: set_val(self.right_px_var, cfg['right_px'])
            if 'top_px' in cfg: set_val(self.top_px_var, cfg['top_px'])
            if 'bottom_px' in cfg: set_val(self.bottom_px_var, cfg['bottom_px'])
            if 'font_scale' in cfg: set_val(self.font_scale_var, cfg['font_scale'])
            if 'font_sub_px' in cfg: set_val(self.font_sub_px_var, cfg['font_sub_px'])
            if 'font_v_offset' in cfg: set_val(self.font_offset_px_var, cfg['font_v_offset'])
            if 'font_main_path' in cfg: set_val(self.font_main_path_var, cfg['font_main_path'])
            if 'font_sub_path' in cfg: set_val(self.font_sub_path_var, cfg['font_sub_path'])
            if 'v_offset' in cfg: set_val(self.v_offset_var, cfg['v_offset'])
            if 'h_offset' in cfg: set_val(self.h_offset_var, cfg['h_offset'])
            if 'theme' in cfg: set_val(self.theme_var, cfg['theme'])
            if 'rotation' in cfg: set_val(self.rotation_var, cfg['rotation'])
            if 'auto_detect' in cfg: set_val(self.auto_detect_var, cfg['auto_detect'])
            if 'film_combo' in cfg: set_val(self.film_combo, cfg['film_combo'])
            if 'sync_lr' in cfg: set_val(self.sync_lr_var, cfg['sync_lr'])
            if 'target_ratio' in cfg: set_val(self.target_ratio_var, cfg['target_ratio'])
            if 'font_spacing' in cfg: set_val(self.font_spacing_var, cfg['font_spacing'])
            if 'branding' in cfg: set_val(self.use_lens_branding_var, cfg['branding'])
            
            exif = cfg.get('exif')
            if exif:
                set_val(self.show_make_var, exif.get('show_make', 1))
                set_val(self.show_model_var, exif.get('show_model', 1))
                set_val(self.show_shutter_var, exif.get('show_shutter', 1))
                set_val(self.show_aperture_var, exif.get('show_aperture', 1))
                set_val(self.show_iso_var, exif.get('show_iso', 1))
                set_val(self.show_lens_var, exif.get('show_lens', 1))
                
                # Check for exif global configuration override
                is_global = self.exif_global_var.get()
                if not is_global:
                    set_val(self.exif_make_var, exif.get('Make', exif.get('make', '')))
                    set_val(self.exif_model_var, exif.get('Model', exif.get('model', '')))
                    set_val(self.exif_lens_var, exif.get('Lens', exif.get('lens', '')))
                    set_val(self.exif_shutter_var, exif.get('Shutter', exif.get('shutter', '')))
                    set_val(self.exif_aperture_var, exif.get('Aperture', exif.get('aperture', '')))
                    set_val(self.exif_iso_var, exif.get('ISO', exif.get('iso', '')))
        finally:
            self._loading_state = False

    def _save_current_to_state(self, path):
        if not path: return
        self.controller.save_ui_state(path, self._get_config_from_ui())

    def _load_state_to_ui(self, path):
        self._loading_state = True
        try:
            cfg = self.controller.load_ui_state(path)
            if not cfg:
                self.detect_layout_and_load_params(os.path.dirname(path))
            else:
                self._apply_config_to_ui(cfg)
                self.on_auto_detect_changed()
        finally:
            self._loading_state = False
            self.update_preview_for_path(path)

    def update_preview_for_path(self, img_path):
        if getattr(self, 'preview_after_id', None):
            self.parent.after_cancel(self.preview_after_id)
        self.preview_after_id = self.parent.after(300, lambda: self._do_render_preview(img_path))

    def _do_render_preview(self, img_path):
        try:
            # EN: CRITICAL - Sync current UI values to state before rendering (#3, #4)
            # CN: 关键 - 在渲染前先将当前 UI 的数值同步到状态机，确保渲染器能拿到最新参数
            self._save_current_to_state(img_path)
            
            manual_film = None
            if self.mode_var.get() == "film" and not self.auto_detect_var.get():
                manual_film = self.film_combo.get().strip()
                for display_name, keyword in self.film_list:
                    if manual_film == display_name: manual_film = keyword; break
            
            self._is_loading_preview, self._current_preview_pil = True, None
            self.redraw_preview()
            
            # EN: Delegate preview thread and job scheduling to Controller
            # CN: 将预览线程和任务调度全面委托给控制器
            self.controller.request_preview(
                img_path=img_path,
                is_digital=(self.mode_var.get() == "digital"),
                is_pure=(self.mode_var.get() == "pure"),
                manual_film=manual_film,
                rotation=self.rotation_var.get(),
                use_branding=self.use_lens_branding_var.get(),
                success_callback=self._on_preview_success,
                error_callback=self._on_preview_error
            )
        except Exception as e:
            self.log(f"CN: [!] 无法请求预览: {e}")

    def _on_preview_success(self, final_pil, report, job_id):
        # EN: Thread-safe UI update
        # CN: 线程安全的 UI 更新
        img_copy = final_pil.copy()
        def apply():
            # EN: Final safety check for job ID alignment
            # CN: 最终 Job ID 校验，确保界面不闪烁
            if not self.controller.state.is_job_current(job_id): return
            self._is_loading_preview, self._current_preview_pil = False, img_copy
            self._update_preview_info(img_copy.width, img_copy.height)
            self.redraw_preview()
            self.log(f"Render: {report['total']*1000:.0f}ms")
            self._check_font_overflow(report)
        self.parent.after(0, apply)

    def _on_preview_error(self, err_msg, job_id):
        # EN: Thread-safe UI fallback
        # CN: 线程安全的 UI 错误降级处理
        def apply():
            if not self.controller.state.is_job_current(job_id): return
            self._is_loading_preview = False
            try:
                with Image.open(self.current_image_path) as img:
                    img = img.convert("RGB")
                    img.thumbnail((2000, 2000))
                    self._current_preview_pil = img.copy()
            except: 
                self._current_preview_pil = None
            self._preview_error_msg = f"Preview error: {err_msg}"
            self.redraw_preview()
        self.parent.after(0, apply)

    def _check_font_overflow(self, report):
        warning_text = self.controller.format_font_overflow_warnings(report, self.lang == "zh")
        self.overflow_warning_label.config(text=warning_text)
    
    def on_mode_changed(self):
        mode = self.mode_var.get()
        # EN: Always show film selection but disable in digital mode
        # CN: 始终显示胶片选择分组，但在数码模式下禁用
        self.film_selection_frame.pack(fill=X, pady=(0, 10), after=self.folder_frame)
        self._set_frame_enabled(self.film_selection_frame, mode == "film")
            
        # EN: Disable ISO in film mode / CN: 胶片模式下禁用 ISO 覆盖
        self.exif_group.set_field_state('iso', "normal" if mode == "digital" else "disabled")
        
        self.on_params_changed()
    
    def on_auto_detect_changed(self):
        if self.auto_detect_var.get(): self.film_combo.config(state="disabled")
        else: self.film_combo.config(state="normal")

    def on_sync_similar_click(self):
        if not getattr(self, 'current_image_path', None): 
            msg = "CN: 请先选择一张图片进行设置 / EN: Please select an image first"
            self.log(msg)
            return
        
        # EN: Save current UI state to the current image config
        # CN: 首先将当前 UI 状态保存到当前图片的配置中
        self._save_current_to_state(self.current_image_path)
        
        # EN: Get current params
        # CN: 获取当前图片配置
        current_cfg = self.controller.get_image_config(self.current_image_path)
        
        # EN: Sync via controller
        # CN: 通过控制器进行同步
        count = self.controller.sync_config_to_similar(self.current_image_path, current_cfg)
        
        if count > 0:
            msg = f"CN: 已成功将当前设置应用至 {count} 张具有相同画幅和旋转角度的图片 / EN: Successfully applied settings to {count} images with matching format and rotation"
            self.log(msg)
        else:
            msg = f"CN: 未找到其他具有相同画幅和旋转角度的图片 / EN: No other images found with matching format and rotation"
            self.log(msg)
    
    def _on_ratio_changed_aesthetic(self, *args):
        """
        EN: Apply premium aesthetic defaults based on selected ratio
        CN: 根据选择的比例应用“高级美学”默认边距
        """
        if getattr(self, '_loading_state', False): return
        
        # EN: Mark that the ratio changed to trigger offset re-distribution
        # CN: 标记比例已更改，以触发偏移量的重新分配
        self._ratio_just_changed = True
        
        ratio_str = self.target_ratio_var.get()
        # EN: Premium margin presets (loaded from Controller)
        # CN: 高级美学预设值（从控制器加载）
        presets = self.controller.get_aesthetic_presets()
        
        # EN: Extract ratio key (e.g., "4:5 (LRB)" -> "4:5")
        import re
        match = re.search(r'(\d+):(\d+)', ratio_str)
        if match:
            key = f"{match.group(1)}:{match.group(2)}"
            if key in presets:
                p = presets[key]
                self._loading_state = True # EN: Prevents individual trace triggers / CN: 防止触发单个更新
                try:
                    self.left_px_var.set(p["left"])
                    self.right_px_var.set(p["right"])
                    self.top_px_var.set(p["top"])
                    self.bottom_px_var.set(p["bottom"])
                    if "font" in p: self.font_scale_var.set(str(p["font"]))
                    if "sub" in p: self.font_sub_px_var.set(str(p["sub"]))
                finally:
                    self._loading_state = False
        else:
            # EN: Reset to baseline defaults for 'Original' / CN: “原图”模式强制重置回基准默认值
            is_original = not ratio_str or "Original" in ratio_str or "原图" in ratio_str
            if is_original:
                self._loading_state = True
                try:
                    self._reset_to_json_layout()
                    # EN: Zero out offsets / CN: 平移归零
                    self.v_offset_var.set(0)
                    self.h_offset_var.set(0)
                finally:
                    self._loading_state = False
        
        # EN: Final update to preview
        # CN: 最终触发全量预览更新
        self.on_params_changed(sync_all=True)

    def _reset_to_json_layout(self):
        """
        EN: Dynamically detect and apply the best layout from JSON based on image aspect ratio.
        CN: 根据图片宽高比，动态从 JSON 中检测并应用最佳布局预设。
        """
        if not getattr(self, 'current_image_path', None):
            # EN: Fallback to baseline if no image / CN: 如果没图片，退回到初始影子值
            self.left_px_var.set(self._baseline_params.get("left"))
            self.right_px_var.set(self._baseline_params.get("right"))
            self.top_px_var.set(self._baseline_params.get("top"))
            self.bottom_px_var.set(self._baseline_params.get("bottom"))
            return

        layout = self.controller.get_layout_from_aspect(self.current_image_path)
        if layout:
            self._apply_config_to_ui(layout)

    def on_params_changed(self, sync_all=False):
        if getattr(self, '_loading_state', False): return
        
        # EN: Proportional Adaptive Logic / CN: 比例锁定联动逻辑
        ratio_str = self.target_ratio_var.get().split(' (')[0]
        if getattr(self, 'current_image_path', None):
            # EN: Detect if sliders or ratio changed / CN: 检测滑块或比例是否变动
            is_offset = False
            cur_v = self.v_offset_var.get()
            cur_h = self.h_offset_var.get()
            
            # EN: If sliders moved OR ratio just changed, we enforce the offset distribution
            # CN: 如果滑块动了，或者比例刚刚发生变化，我们强制执行偏移量分布
            if cur_v != self._prev_v_offset or cur_h != self._prev_h_offset or getattr(self, '_ratio_just_changed', False):
                is_offset = True
                self._prev_v_offset = cur_v
                self._prev_h_offset = cur_h
                self._ratio_just_changed = False # Reset flag
                
                # EN: Disable sync_lr automatically when moving horizontally
                if cur_h != 0 and self.sync_lr_var.get():
                    self.sync_lr_var.set(False)

            # EN: Handle Sync L/R Borders / CN: 处理左右边框同步
            if self.sync_lr_var.get() and not is_offset:
                try:
                    left_val = self.left_px_var.get()
                    if left_val and self.right_px_var.get() != left_val:
                        self.right_px_var.set(left_val)
                except: pass

            self._handle_ratio_locked_sync(ratio_str, is_offset=is_offset)

        # EN: Update shadow state / CN: 更新影子状态
        self._param_shadow = {
            "left": self.left_px_var.get(), "right": self.right_px_var.get(),
            "top": self.top_px_var.get(), "bottom": self.bottom_px_var.get()
        }

        if getattr(self, 'current_image_path', None):
            self._save_current_to_state(self.current_image_path)
            if sync_all:
                cfg = self.controller.get_image_config(self.current_image_path)
                for p in self.controller.state.get_paths():
                    if p != self.current_image_path: self.controller.update_image_config(p, cfg)
            self.update_preview_for_path(self.current_image_path)

    def _handle_ratio_locked_sync(self, ratio_str, is_offset=False):
        """
        EN: Auto-calculate paddings via centralized LayoutCalculator to maintain target ratio.
        CN: 比例锁定联动逻辑：调用统一解算器自动计算并补齐其余边际。
        """
        if not getattr(self, 'current_image_path', None): return
        
        cfg = self.controller.resolve_ratio_locked_sync(
            img_path=self.current_image_path,
            ratio_str=ratio_str,
            current_cfg=self._get_config_from_ui(),
            param_shadow=self._param_shadow,
            is_offset=is_offset,
            sync_lr=self.sync_lr_var.get()
        )
        if cfg:
            self._loading_state = True
            try:
                self.left_px_var.set(cfg["left_px"])
                self.right_px_var.set(cfg["right_px"])
                self.top_px_var.set(cfg["top_px"])
                self.bottom_px_var.set(cfg["bottom_px"])
            finally:
                self._loading_state = False

    def _set_frame_enabled(self, frame, enabled):
        """EN: Recursively set state for all widgets in a frame / CN: 递归设置框架内所有组件的启用状态"""
        state = "normal" if enabled else "disabled"
        for child in frame.winfo_children():
            try:
                # Some widgets like Labelframe might not have 'state' but their children do
                child.configure(state=state)
            except:
                pass
            # Also recurse into sub-frames
            if child.winfo_children():
                self._set_frame_enabled(child, enabled)

    def notify_order_changed(self, new_paths):
        self.controller.update_batch_order([os.path.normcase(os.path.normpath(p)) for p in new_paths])
        if getattr(self, 'current_image_path', None):
            self.update_preview_for_path(self.current_image_path)

    def on_process_click(self):
        if self.controller.is_processing():
            self.controller.request_stop()
            msg = "⚡ 正在停止..." if self.lang == "zh" else "⚡ Stopping..."
            self.process_button.config(text=msg, bootstyle="danger", state="disabled")
        else: self.start_processing()

    def select_output_folder(self):
        path = filedialog.askdirectory()
        if path: self.output_folder_var.set(path)

    def start_processing(self):
        try:
            self.on_params_changed(sync_all=True)
            images = self.thumb_strip.get_all_images()
            if not images:
                msg = "请先添加图片！" if self.lang == "zh" else "Please add images first!"
                messagebox.showwarning("警告" if self.lang == "zh" else "Warning", msg)
                return
            if self.current_image_path: self._save_current_to_state(self.current_image_path)
            self.stop_requested = False
            msg = "停止处理 (Stop)" if self.lang == "zh" else "Stop Processing (Cancel)"
            self.process_button.config(text=msg, bootstyle="danger-outline")
            self.progress.pack(fill=X, pady=(0, 10))
            self.progress['value'] = 0
            output_folder = self.output_folder_var.get()
            if not output_folder:
                working_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
                output_folder = os.path.join(working_dir, "photos_out")
            os.makedirs(output_folder, exist_ok=True)
            self.controller.start_batch_processing_from_dict(output_folder, self._get_config_from_ui(), self.film_list)
        except Exception as e:
            import traceback
            self.parent.after(0, lambda msg=traceback.format_exc(): self.on_processing_error(msg))

    def _process_feedback(self, current, total, filename):
        percent = int((current / total) * 100)
        self.progress.config(value=percent)
        self.log(f"[{current}/{total}] {filename}")

    def on_processing_complete(self, result):
        self.progress.pack_forget()
        self.process_button.config(
            text="开始处理" if self.lang == "zh" else "Start Processing", bootstyle="primary-solid", state="normal"
        )
        if result.get('success'):
            self.log("\n✓ " + "="*50)
            self.log("✓ 处理完成！" if self.lang == "zh" else "✓ Processing complete!")
            self.log(f"✓ 已处理 {result.get('processed', 0)} 张照片")
            self.log("✓ " + "="*50)
            title = "完成" if self.lang=="zh" else "Complete"
            msg = f"处理完成！\n\n已处理 {result.get('processed', 0)} 张照片\n\n是否打开输出文件夹？"
            if messagebox.askyesno(title, msg):
                try:
                    wd = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
                    of = os.path.join(wd, "photos_out")
                    if platform.system() == "Windows": os.startfile(of)
                    elif platform.system() == "Darwin": subprocess.run(["open", of])
                    else: subprocess.run(["xdg-open", of])
                except: pass
        else:
            self.log("\n✗ 处理失败")
            self.log(f"✗ {result.get('message', 'Unknown error')}")
            messagebox.showerror("错误", result.get('message', 'Unknown error'))

    def on_processing_error(self, error_msg):
        self.progress.pack_forget()
        self.process_button.config(state="normal")
        self.log(f"\n✗ 发生错误\n{error_msg}")
        msg = f"处理过程中发生错误：\n\n{error_msg[:200]}...\n\n如需帮助请联系：xjames007@gmail.com"
        messagebox.showerror("错误", msg)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _update_preview_info(self, preview_w, preview_h):
        """EN: Update pixel and ratio info / CN: 更新像素与比例信息"""
        specs_text = self.controller.format_preview_specs(preview_w, preview_h, self.lang == "zh")
        self.preview_info_label.config(text=specs_text)

    def _get_float_safe(self, var, default=0.0):
        try:
            val = var.get()
            return float(val) if val is not None else default
        except: return default

    def _get_int_safe(self, var, default=0):
        try:
            val = var.get()
            return int(float(val)) if val is not None and str(val).strip() != "" else default
        except:
            return default

    # --- Persistence Logic / 持久化逻辑 ---
    
    def refresh_preset_lists(self):
        """EN: Update UI dropdowns with latest presets / CN: 更新界面下拉菜单中的预设列表"""
        border_names = self.controller.get_border_presets().keys()
        self.aesthetic_group.set_preset_list(border_names)
        
        metadata_names = self.controller.get_metadata_presets().keys()
        self.exif_group.set_favorite_list(metadata_names)

    def on_save_border_preset(self):
        title = "保存预设" if self.lang == "zh" else "Save Preset"
        prompt = "请输入预设名称 / Enter preset name:"
        name = simpledialog.askstring(title, prompt, parent=self.parent)
        
        if name:
            self.controller.save_border_preset(name, self._get_config_from_ui())
            self.refresh_preset_lists()
            self.aesthetic_group.preset_combo.set(name)

    def on_apply_border_preset(self, name):
        cfg = self.controller.load_border_preset(name)
        if cfg:
            self._apply_config_to_ui(cfg)
        self.on_params_changed(sync_all=True)

    def on_delete_border_preset(self, name):
        confirm = messagebox.askyesno("Confirm", f"Delete preset '{name}'?" if self.lang == "en" else f"确定删除预设 '{name}'?")
        if confirm:
            self.controller.delete_border_preset(name)
            self.refresh_preset_lists()

    def on_save_metadata_preset(self):
        title = "收藏机型" if self.lang == "zh" else "Favorite Model"
        prompt = "请输入保存名称 (如: Leica M6) / Enter favorite name:"
        name = simpledialog.askstring(title, prompt, parent=self.parent)
        
        if name:
            self.controller.save_metadata_preset(name, self._get_config_from_ui())
            self.refresh_preset_lists()
            self.exif_group.fav_combo.set(name)

    def on_apply_metadata_preset(self, name):
        data = self.controller.load_metadata_preset(name)
        if data:
            self._apply_config_to_ui({"exif": data})
        self.on_params_changed()

    def _force_int(self, var):
        try:
            val = var.get()
            if isinstance(val, (float, str)):
                var.set(int(float(val)))
        except:
            pass

    def _sync_lr(self, source_var, target_var, *args):
        if getattr(self, '_is_syncing_lr', False) or not self.sync_lr_var.get(): return
        if getattr(self, '_loading_state', False): return
        self._is_syncing_lr = True
        try:
            s_val = source_var.get()
            if s_val != target_var.get():
                target_var.set(s_val)
        finally:
            self._is_syncing_lr = False
