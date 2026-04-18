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
        
        self.layout_config = self.controller.load_layout_config()
        self.setup_ui()
        self.load_film_library()
    
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

        # EN: Parameter variables (Pixels based on 4500px ref) / CN: 参数变量（基于 4500px 基准的像素值）
        self.left_px_var = ttk.IntVar(value=180)
        self.right_px_var = ttk.IntVar(value=180)
        self.top_px_var = ttk.IntVar(value=180)
        self.bottom_px_var = ttk.IntVar(value=585)
        self.font_scale_var = ttk.IntVar(value=144)
        self.font_sub_px_var = ttk.IntVar(value=112)
        self.font_offset_px_var = ttk.IntVar(value=0)
        self.theme_var = tk.StringVar(value="light")
        self.use_lens_branding_var = tk.BooleanVar(value=True) # EN: Global lens branding toggle / CN: 镜头专属标识全局开关

        # EN: Setup traces for sync / CN: 设置同步监听
        self.left_px_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.right_px_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.top_px_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.bottom_px_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.font_scale_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.font_sub_px_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
        self.font_offset_px_var.trace('w', lambda *args: self.on_params_changed(sync_all=False))
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
        self.film_combo.bind("<<ComboboxSelected>>", lambda e: self.on_params_changed())
        self.film_combo.bind("<Return>", lambda e: self.on_params_changed())

        # EN: Advanced settings (border parameters) / CN: 高级设置（边框参数）
        settings_vars = {
            "left": self.left_px_var, "right": self.right_px_var,
            "top": self.top_px_var, "bottom": self.bottom_px_var,
            "font": self.font_scale_var, "font_sub": self.font_sub_px_var,
            "font_offset": self.font_offset_px_var,
            "theme": self.theme_var,
            "branding": self.use_lens_branding_var
        }
        self.settings_group = SettingsGroup(self.left_frame, lang=self.lang, 
                                           on_change=self.on_params_changed,
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
                self._update_batch_width_cache(self.controller.current_batch_paths)
                self.refresh_thumb_strip()
                self.update_file_count()
                self.log(f"CN: 已自动检测到 photos_in 文件夹，共 {count} 张图片 / EN: Auto-detected photos_in folder with {count} images")

    def refresh_input_folder(self):
        folder = self.controller.input_folder
        if not folder: return
        count = self.controller.scan_folder(folder)
        self._update_batch_width_cache(self.controller.current_batch_paths)
        self.controller.clear_all_configs()
        self.refresh_thumb_strip()
        self.update_file_count()
        self.log(f"CN: 已刷新输入文件夹，当前共 {count} 张图片 / EN: Refreshed input folder, current {count} images")
        self.detect_layout_and_load_params(folder)

    def detect_layout_and_load_params(self, folder):
        layout_cfg = self.controller.detect_layout_from_folder(folder)
        if layout_cfg:
            self._loading_state = True
            try:
                # EN: Convert ratios to pixels for UI (ref=4500)
                ref = 4500.0
                side = layout_cfg.get('side_ratio', 0.04)
                self.left_px_var.set(int(layout_cfg.get('left_ratio', side) * ref))
                self.right_px_var.set(int(layout_cfg.get('right_ratio', side) * ref))
                self.top_px_var.set(int(layout_cfg.get('top_ratio', 0.04) * ref))
                self.bottom_px_var.set(int(layout_cfg.get('bottom_ratio', 0.13) * ref))
                self.font_scale_var.set(int(layout_cfg.get('font_scale', 0.032) * ref))
            finally:
                self._loading_state = False
    
    def select_input_folder(self):
        folder = filedialog.askdirectory(
            title="选择输入文件夹 Select Input Folder",
            initialdir=self.input_folder_var.get() or os.path.expanduser("~")
        )
        if folder:
            self.input_folder_var.set(folder)
            self.controller.clear_all_configs()
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
        self.thumb_strip.update_images(self.controller.current_batch_paths)
        active = getattr(self, 'current_image_path', None)
        if active in self.controller.current_batch_paths:
            self.thumb_strip.set_active(active)
        elif self.controller.current_batch_paths:
            self.on_thumbnail_click(self.controller.current_batch_paths[0])

    def _update_batch_width_cache(self, paths, async_mode=True):
        def scan_work():
            for p in paths:
                try:
                    p_norm = os.path.normcase(os.path.normpath(p))
                    if p_norm not in self.controller.batch_width_cache:
                        with Image.open(p) as img:
                            w, h = img.size
                            self.controller.update_aspect_ratio_cache(p, w/h)
                except: pass
        if async_mode: threading.Thread(target=scan_work, daemon=True).start()
        else: scan_work()

    def on_thumbnail_click(self, path):
        if getattr(self, 'current_image_path', None) == path: return
        if getattr(self, 'current_image_path', None):
            self._save_current_to_state(self.current_image_path)
        self.current_image_path = path
        self.thumb_strip.set_active(path)
        self._load_state_to_ui(path)

    def _save_current_to_state(self, path):
        if not path: return
        params = {
            'left_px': self._get_int_safe(self.left_px_var, 180),
            'right_px': self._get_int_safe(self.right_px_var, 180),
            'top_px': self._get_int_safe(self.top_px_var, 180),
            'bottom_px': self._get_int_safe(self.bottom_px_var, 585),
            'font_scale': self._get_int_safe(self.font_scale_var, 144),
            'font_sub_px': self._get_int_safe(self.font_sub_px_var, 112),
            'font_v_offset': self._get_int_safe(self.font_offset_px_var, 0),
            'theme': self.theme_var.get(),
            'rotation': self.rotation_var.get(),
            'auto_detect': self.auto_detect_var.get(),
            'film_combo': self.film_combo.get(),
            'exif': {
                'Make': self.exif_make_var.get().strip(), 'Model': self.exif_model_var.get().strip(),
                'Lens': self.exif_lens_var.get().strip(), 'Shutter': self.exif_shutter_var.get().strip(),
                'Aperture': self.exif_aperture_var.get().strip(), 'ISO': self.exif_iso_var.get().strip(),
                'show_make': self.show_make_var.get(), 'show_model': self.show_model_var.get(),
                'show_shutter': self.show_shutter_var.get(), 'show_aperture': self.show_aperture_var.get(),
                'show_iso': self.show_iso_var.get(), 'show_lens': self.show_lens_var.get()
            }
        }
        self.controller.update_image_config(path, params)

    def _load_state_to_ui(self, path):
        cfg = self.controller.get_image_config(path)
        self._loading_state = True
        try:
            if not cfg:
                self.detect_layout_and_load_params(os.path.dirname(path))
            else:
                if 'left_px' in cfg: self.left_px_var.set(cfg['left_px'])
                if 'right_px' in cfg: self.right_px_var.set(cfg['right_px'])
                if 'top_px' in cfg: self.top_px_var.set(cfg['top_px'])
                if 'bottom_px' in cfg: self.bottom_px_var.set(cfg['bottom_px'])
                if 'font_scale' in cfg:
                    val = cfg['font_scale']
                    if val < 1.0: val = int(val * 4500) # Migration
                    self.font_scale_var.set(int(val))
                if 'font_sub_px' in cfg: 
                    self.font_sub_px_var.set(cfg['font_sub_px'])
                elif 'font_scale' in cfg:
                    # EN: Dynamic fallback for old configs (CN: 为旧配置提供动态回退)
                    self.font_sub_px_var.set(int(self.font_scale_var.get() * 0.78))
                
                if 'theme' in cfg: self.theme_var.set(cfg['theme'])
                if 'film_combo' in cfg: self.film_combo.set(cfg['film_combo'])
                if 'font_v_offset' in cfg: self.font_offset_px_var.set(cfg['font_v_offset'])
                self.rotation_var.set(cfg.get('rotation', 0))
                self.auto_detect_var.set(cfg.get('auto_detect', True))
                exif = cfg.get('exif', {})
                self.show_make_var.set(exif.get('show_make', 1))
                self.show_model_var.set(exif.get('show_model', 1))
                self.show_shutter_var.set(exif.get('show_shutter', 1))
                self.show_aperture_var.set(exif.get('show_aperture', 1))
                self.show_iso_var.set(exif.get('show_iso', 1))
                self.show_lens_var.set(exif.get('show_lens', 1))
                if not self.exif_global_var.get():
                    self.exif_make_var.set(exif.get('Make', ''))
                    self.exif_model_var.set(exif.get('Model', ''))
                    self.exif_lens_var.set(exif.get('Lens', ''))
                    self.exif_shutter_var.set(exif.get('Shutter', ''))
                    self.exif_aperture_var.set(exif.get('Aperture', ''))
                    self.exif_iso_var.set(exif.get('ISO', ''))
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
            manual_film = None
            if self.mode_var.get() == "film" and not self.auto_detect_var.get():
                manual_film = self.film_combo.get().strip()
                for display_name, keyword in self.film_list:
                    if manual_film == display_name: manual_film = keyword; break
            self.preview_job_id += 1
            job_id = self.preview_job_id
            self._is_loading_preview, self._current_preview_pil = True, None
            self.redraw_preview()
            def worker():
                try:
                    final_pil, report = self.controller.get_preview_image(
                        img_path=img_path, is_digital=(self.mode_var.get()=="digital"),
                        is_pure=(self.mode_var.get()=="pure"), manual_film=manual_film,
                        rotation=self.rotation_var.get(), use_branding=self.use_lens_branding_var.get()
                    )
                    if not final_pil: raise Exception("Render failed")
                    img_copy = final_pil.copy()
                    def apply():
                        if job_id != self.preview_job_id: return
                        self._is_loading_preview, self._current_preview_pil = False, img_copy
                        self._update_preview_info(img_copy.width, img_copy.height)
                        self.redraw_preview()
                        self.log(f"Render: {report['total']*1000:.0f}ms")
                        self._check_font_overflow(report)
                    self.parent.after(0, apply)
                except Exception as e:
                    err_msg = str(e)
                    self.parent.after(0, lambda: self._handle_preview_error(img_path, err_msg, job_id))
            threading.Thread(target=worker, daemon=True).start()
        except: pass

    def _handle_preview_error(self, path, msg, job_id):
        if job_id != self.preview_job_id: return
        self._is_loading_preview = False
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img.thumbnail((2000, 2000))
                self._current_preview_pil = img.copy()
        except: self._current_preview_pil = None
        self._preview_error_msg = f"Preview error: {msg}"
        self.redraw_preview()

    def _check_font_overflow(self, report):
        if 'render_breakdown' in report and 'max_font_px' in report['render_breakdown']:
            max_info = report['render_breakdown']['max_font_px']
            main_max = max_info.get('main', 0)
            sub_max = max_info.get('sub', 0)
            
            main_overflow = max_info.get('main_overflow', False)
            sub_overflow = max_info.get('sub_overflow', False)
            v_overflow = max_info.get('v_overflow', False)
            
            warnings = []
            if main_overflow or v_overflow:
                if v_overflow:
                    msg = f"⚠️ 型号压图！建议 ≤{main_max}px" if self.lang == "zh" else f"⚠️ Model on photo! Max ≤{main_max}px"
                else:
                    msg = f"⚠️ 型号溢出，建议 ≤{main_max}px" if self.lang == "zh" else f"⚠️ Model overflow, suggest ≤{main_max}px"
                warnings.append(msg)

            if sub_overflow:
                warnings.append(f"⚠️ 参数溢出，建议 ≤{sub_max}px" if self.lang == "zh" else f"⚠️ Param overflow, suggest ≤{sub_max}px")
            
            if warnings:
                self.overflow_warning_label.config(text=" | ".join(warnings))
            else:
                self.overflow_warning_label.config(text="")
    
    def on_mode_changed(self):
        mode = self.mode_var.get()
        if mode == "film":
            self.film_selection_frame.pack(fill=X, pady=(0, 10), after=self.folder_frame)
        else:
            self.film_selection_frame.pack_forget()
        self.on_params_changed()
    
    def on_auto_detect_changed(self):
        if self.auto_detect_var.get(): self.film_combo.config(state="disabled")
        else: self.film_combo.config(state="normal")
    
    def on_params_changed(self, sync_all=False):
        if getattr(self, '_loading_state', False): return
        if getattr(self, 'current_image_path', None):
            self._save_current_to_state(self.current_image_path)
            if sync_all:
                cfg = self.controller.get_image_config(self.current_image_path)
                for p in self.controller.current_batch_paths:
                    if p != self.current_image_path: self.controller.update_image_config(p, cfg)
            self.update_preview_for_path(self.current_image_path)

    def notify_order_changed(self, new_paths):
        self.controller.update_batch_order([os.path.normcase(os.path.normpath(p)) for p in new_paths])
        if getattr(self, 'current_image_path', None):
            self.update_preview_for_path(self.current_image_path)

    def on_process_click(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.controller.request_stop()
            msg = "⚡ 正在停止..." if self.lang == "zh" else "⚡ Stopping..."
            self.process_button.config(text=msg, bootstyle="danger", state="disabled")
        else: self.start_processing()

    def start_processing(self):
        try:
            self.on_params_changed(sync_all=True)
            input_folder = self.input_folder_var.get()
            if not input_folder or not os.path.exists(input_folder):
                msg = "请先选择输入文件夹！" if self.lang == "zh" else "Please select input folder first!"
                messagebox.showwarning("警告" if self.lang == "zh" else "Warning", msg)
                return
            if self.current_image_path: self._save_current_to_state(self.current_image_path)
            self.stop_requested = False
            msg = "停止处理 (Stop)" if self.lang == "zh" else "Stop Processing (Cancel)"
            self.process_button.config(text=msg, bootstyle="danger-outline")
            self.progress.pack(fill=X, pady=(0, 10))
            self.progress['value'] = 0
            working_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
            output_folder = os.path.join(working_dir, "photos_out")
            os.makedirs(output_folder, exist_ok=True)
            global_cfg = {
                'is_digital': self.mode_var.get() == "digital", 'is_pure': self.mode_var.get() == "pure",
                'theme': self.theme_var.get(), 'rotation': self.rotation_var.get(),
                'layout': {
                    "left_px": self._get_int_safe(self.left_px_var, 180),
                    "right_px": self._get_int_safe(self.right_px_var, 180),
                    "top_px": self._get_int_safe(self.top_px_var, 180),
                    "bottom_px": self._get_int_safe(self.bottom_px_var, 585),
                    "font_sub_px": self._get_int_safe(self.font_sub_px_var, 112),
                    "font_v_offset": self._get_int_safe(self.font_offset_px_var, 0)
                },
                'exif': {
                    'Make': self.exif_make_var.get().strip(), 'Model': self.exif_model_var.get().strip(),
                    'LensModel': self.exif_lens_var.get().strip(), 'ExposureTimeStr': self.exif_shutter_var.get().strip(),
                    'FNumber': self.exif_aperture_var.get().strip(), 'ISO': self.exif_iso_var.get().strip(),
                    'show_make': self.show_make_var.get(), 'show_model': self.show_model_var.get(),
                    'show_shutter': self.show_shutter_var.get(), 'show_aperture': self.show_aperture_var.get(),
                    'show_iso': self.show_iso_var.get(), 'show_lens': self.show_lens_var.get()
                },
                'use_branding': self.use_lens_branding_var.get()
            }
            manual_film = None
            if not global_cfg['is_digital'] and not self.auto_detect_var.get(): manual_film = self.film_combo.get()
            global_cfg['manual_film'] = manual_film
            def run_work():
                self.controller.run_batch(output_dir=output_folder, global_cfg=global_cfg, film_list=self.film_list)
            self.worker_thread = threading.Thread(target=run_work, daemon=True)
            self.worker_thread.start()
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
        # EN: Convert preview size (1200 edge) back to target size (4500 edge)
        # CN: 将预览尺寸（1200 基准）换算回目标输出尺寸（4500 基准）
        scale = 4500.0 / 1200.0
        final_w = int(preview_w * scale)
        final_h = int(preview_h * scale)
        
        # EN: Calculate aspect ratio / CN: 计算宽高比
        actual_ratio = final_w / final_h
        ratio_str = None
        
        # EN: Check for common photography ratios first for cleaner display
        # CN: 优先检查常见的摄影比例以获得更整洁的显示
        for r_name, r_val in [("3:2", 3/2), ("2:3", 2/3), ("4:3", 4/3), ("3:4", 3/4), 
                             ("16:9", 16/9), ("9:16", 9/16), ("1:1", 1.0), ("4:5", 4/5), ("5:4", 5/4)]:
            if abs(actual_ratio - r_val) < 0.02:
                ratio_str = r_name
                break
        
        # EN: Fallback to decimal format for non-standard ratios (e.g. 1.22:1)
        # CN: 非标准画幅降级为十进制展示，更直观
        if not ratio_str:
            if actual_ratio >= 1:
                ratio_str = f"{actual_ratio:.2f}:1"
            else:
                ratio_str = f"1:{1/actual_ratio:.2f}"
        
        prefix = "规格: " if self.lang == "zh" else "Specs: "
        self.preview_info_label.config(text=f"{prefix}{final_w} x {final_h} px ({ratio_str})")

    def _get_float_safe(self, var, default=0.0):
        try:
            val = var.get()
            return float(val) if val is not None else default
        except: return default

    def _get_int_safe(self, var, default=0):
        try:
            val = var.get()
            return int(val) if val is not None else default
        except:
            return default
