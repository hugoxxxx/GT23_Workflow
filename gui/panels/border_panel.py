# gui/panels/border_panel.py
"""
EN: Border Tool panel for GUI (tkinter version)
CN: 边框工具 GUI 面板（tkinter版本）
"""

import os
import sys
import json
import threading
import tempfile
import shutil
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

from gui.panels.base_panel import BasePanel
from utils.paths import get_asset_path, get_working_dir
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer

class BorderPanel(BasePanel):
    """
    EN: Border Tool GUI panel
    CN: 边框工具图形界面面板
    """
    def __init__(self, parent, lang="en"):
        """
        Args:
            parent: Parent widget / 父部件
            lang: UI language ("zh") / 界面语言（"zh"）
        """
        super().__init__(parent, lang)
        
        # EN: Initialize Tk variables / CN: 初始化 Tk 变量
        self.mode_var = ttk.StringVar(value="film")
        self.side_ratio_var = ttk.DoubleVar(value=0.04)
        self.top_ratio_var = ttk.DoubleVar(value=0.04)
        self.bottom_ratio_var = ttk.DoubleVar(value=0.13)
        self.font_scale_var = ttk.DoubleVar(value=0.032)
        self.auto_detect_var = ttk.BooleanVar(value=True)
        self.show_date_var = ttk.BooleanVar(value=True)
        self.roll_id_var = ttk.StringVar(value="")
        
        # Internal state
        self.layout_config = {}
        self._full_preview_img = None
        self._preview_img_ref = None
        self._resize_job = None
        self.preview_job_id = 0  # For debounced preview updates
        self.worker_thread = None
        self.renderer = FilmRenderer()
        self.meta = MetadataHandler()

        self.setup_ui()
        self.load_film_library()
    
    def load_layout_config(self):
        """
        EN: Load layout config from JSON
        CN: 从JSON加载布局配置
        """
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                base_path = os.path.dirname(os.path.dirname(current_dir))
            
            config_path = os.path.join(base_path, 'config', 'layouts.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.layout_config = json.load(f)
        except Exception as e:
            # EN: Failed to load, use defaults / CN: 加载失败，使用默认值
            self.layout_config = {}
    
    def setup_ui(self):
        """
        EN: Setup user interface with two-column layout
        CN: 设置双栏布局的用户界面
        """
        # EN: Create PanedWindow for flexible split / CN: 创建水平分割窗格
        self.paned = ttk.Panedwindow(self.parent, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES)
        
        self.left_panel = ttk.Frame(self.paned)
        self.right_panel = ttk.Frame(self.paned, width=300) # Slightly reduced width
        
        self.paned.add(self.left_panel, weight=1)  # Main area expands
        self.paned.add(self.right_panel, weight=0) # Sidebar stays fixed width initially

        # EN: Dense Settings Container / CN: 高密度设置容器
        self.settings_frame = ttk.Frame(self.left_panel, padding=(0, 2))
        self.settings_frame.pack(fill=X)
        
        from utils.i18n import get_string
        
        # Row 0: Mode & Film Selection
        r0 = ttk.Frame(self.settings_frame)
        r0.pack(fill=X, pady=2)
        self.mode_label = ttk.Label(r0, text=get_string("mode", self.lang))
        self.mode_label.pack(side=LEFT)
        self.film_radio = ttk.Radiobutton(r0, text=get_string("film", self.lang), variable=self.mode_var, value="film", command=self.on_mode_changed)
        self.film_radio.pack(side=LEFT, padx=(5, 2))
        self.digital_radio = ttk.Radiobutton(r0, text=get_string("digital", self.lang), variable=self.mode_var, value="digital", command=self.on_mode_changed)
        self.digital_radio.pack(side=LEFT, padx=(5, 2))
        
        self.film_select_label = ttk.Label(r0, text=" | 胶片:" if self.lang == "zh" else " | Film:")
        self.film_select_label.pack(side=LEFT, padx=(5, 2))
        self.auto_detect_check = ttk.Checkbutton(r0, text="自动" if self.lang == "zh" else "Auto Detect", variable=self.auto_detect_var, command=self.on_auto_detect_changed, bootstyle="secondary-round-toggle")
        self.auto_detect_check.pack(side=LEFT)
        self.film_combo = ttk.Combobox(r0, state="disabled", width=20)
        self.film_combo.pack(side=LEFT, padx=5, fill=X, expand=YES)

        # Row 1: Folder Selection
        r1 = ttk.Frame(self.settings_frame)
        r1.pack(fill=X, pady=2)
        ttk.Entry(r1, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES)
        self.browse_button = ttk.Button(r1, text="浏览" if self.lang == "zh" else "Browse", command=self.select_input_folder, width=6)
        self.browse_button.pack(side=LEFT, padx=2)
        self.refresh_button = ttk.Button(r1, text="刷新" if self.lang == "zh" else "Refresh", command=self.refresh_input_folder, width=6)
        self.refresh_button.pack(side=LEFT)

        # Row 2: Border Settings (Grid)
        r2 = ttk.Frame(self.settings_frame)
        r2.pack(fill=X, pady=5)
        
        self.param_labels = []
        labels_zh = ["左右:", "顶部:", "底部:", "字体:"]
        labels_en = ["Sides:", "Top:", "Bottom:", "Font:"]
        vars = [self.side_ratio_var, self.top_ratio_var, self.bottom_ratio_var, self.font_scale_var]
        for i, (lab_zh, lab_en, var) in enumerate(zip(labels_zh, labels_en, vars)):
            lbl = ttk.Label(r2, text=lab_zh if self.lang == "zh" else lab_en)
            lbl.pack(side=LEFT, padx=(5 if i==0 else 15, 2))
            self.param_labels.append(lbl)
            ttk.Entry(r2, textvariable=var, width=8).pack(side=LEFT)
            var.trace_add('write', lambda *args: self.on_params_changed())

        # EN: File count label / CN: 文件计数标签
        self.file_count_label = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 8), foreground="#444")
        self.file_count_label.pack(anchor=W, pady=(2, 0))
        
        from utils.i18n import get_string
        
        # Row 1: Border Settings (Grid)

        # EN: Process button / CN: 处理按钮
        self.btn_frame = ttk.Frame(self.left_panel)
        self.btn_frame.pack(side=BOTTOM, fill=X, pady=10)
        self.process_button = ttk.Button(self.left_panel, text=get_string("generate", self.lang), command=self.start_processing, bootstyle="primary", padding=10)
        self.process_button.pack(fill=X, pady=10)
        
        self.progress = ttk.Progressbar(self.left_panel, mode="determinate", bootstyle="primary-striped")
        self.progress.pack(side=BOTTOM, fill=X, pady=(0, 5), padx=50)
        self.progress.pack_forget()  # Hide initially

        # EN: Preview area (Expands to fill middle) / CN: 预览区域（填充中间）
        self.preview_section = ttk.Frame(self.left_panel, padding=(0, 5))
        self.preview_section.pack(fill=BOTH, expand=YES)
        
        self.preview_title_label = ttk.Label(self.preview_section, text="", font=("Segoe UI", 8, "bold"), foreground="#666")
        self.preview_title_label.pack(anchor=W, pady=(0, 5))
        no_preview_text = "暂无预览" if self.lang == "zh" else "No preview"
        self.preview_label = ttk.Label(self.preview_section, text=no_preview_text, anchor="center")
        self.preview_label.pack(fill=BOTH, expand=YES)
        
        # EN: Bind resize event / CN: 绑定缩放事件
        self.preview_label.bind("<Configure>", self.on_preview_resize)

        # --- RIGHT PANEL: Logs ---
        
        # EN: Log output / CN: 日志输出
        self.log_section = ttk.Frame(self.right_panel, padding=(15, 10, 0, 10))
        self.log_section.pack(fill=BOTH, expand=YES)
        
        self.log_title_label = ttk.Label(self.log_section, text="", font=("Segoe UI", 8, "bold"), foreground="#666")
        self.log_title_label.pack(anchor=W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(self.log_section, wrap=tk.WORD, state="disabled", width=35,
                                                 font=("Consolas", 10), background="#101010", foreground="#A0A0A0",
                                                 insertbackground="white", borderwidth=0)
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # EN: Auto-detect photos_in / CN: 自动检测 photos_in
        self.auto_detect_photos_in()
    
    def on_preview_resize(self, event):
        """
        EN: Handle preview resize event with debouncing.
        CN: 带防抖效果的预览图缩放处理。
        """
        if not self._full_preview_img:
            return
            
        if self._resize_job:
            self.parent.after_cancel(self._resize_job)
            
        self._resize_job = self.parent.after(100, self._perform_resize)
        
    def _perform_resize(self):
        """
        EN: Actually perform the resizing using the stored full preview image.
        CN: 使用存储的全尺寸图实际执行缩放更新。
        """
        if not self._full_preview_img:
            return
            
        try:
            # EN: Get available space (minus some margin) / CN: 获取可用空间（减去边距）
            w = self.preview_label.winfo_width() - 10
            h = self.preview_label.winfo_height() - 10
            
            if w < 50 or h < 50:
                return
                
            img = self._full_preview_img.copy()
            img.thumbnail((w, h))
            tk_img = ImageTk.PhotoImage(img)
            
            self.preview_label.config(image=tk_img, text="")
            self._preview_img_ref = tk_img
        except Exception:
            pass
        finally:
            self._resize_job = None

    def update_language(self, lang):
        """
        EN: Update UI language
        CN: 更新界面语言
        """
        self.lang = lang
        from utils.i18n import get_string
        
        self.mode_label.config(text=get_string("mode", lang))
        self.film_radio.config(text=get_string("film", lang))
        self.digital_radio.config(text=get_string("digital", lang))
        self.film_select_label.config(text=get_string("film_colon", lang))
        self.auto_detect_check.config(text=get_string("auto_detect", lang))
        self.browse_button.config(text=get_string("browse", lang))
        self.refresh_button.config(text=get_string("refresh", lang))
        self.process_button.config(text=get_string("generate", lang))
        self.preview_title_label.config(text=get_string("preview", lang))
        self.log_title_label.config(text=get_string("log_title", lang))

        labels_keys = ["sides_colon", "top_colon", "bottom_colon", "font_colon"]
        for lbl, key in zip(self.param_labels, labels_keys):
            lbl.config(text=get_string(key, lang))

        # EN: Update placeholders
        self.update_film_combo_values()
        self.update_file_count_label(self.file_count_label)
        
        # EN: Update current preview text if empty
        if not self._full_preview_img:
            no_preview_text = get_string("no_preview", self.lang)
            self.preview_label.config(text=no_preview_text)
            
        # EN: Clear log and re-log initial status to match new language
        # CN: 清空日志并重新记录初始状态以匹配新语言
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        self.log_ready_status()
    
    def log_ready_status(self):
        """
        EN: Log current status (film count, photos found)
        CN: 记录当前状态（胶片数量、发现的照片）
        """
        if self.film_list:
            msg = f"✓ 已加载 {len(self.film_list)} 种胶片" if self.lang == "zh" else f"✓ Loaded {len(self.film_list)} films"
            self.log(msg)
        
        folder = self.input_folder_var.get()
        if folder and os.path.exists(folder):
            try:
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if files:
                    msg = f"✓ 文件夹中找到 {len(files)} 张照片" if self.lang == "zh" else f"✓ Found {len(files)} photos in folder"
                    self.log(msg)
            except Exception:
                pass

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
    
    def on_folder_selected(self, folder):
        """
        EN: Handle folder selection.
        CN: 处理文件夹选择。
        """
        self.update_file_count()
        self.detect_layout_and_load_params(folder)
        self.update_preview(folder)

    def update_file_count(self):
        """
        EN: Update file count display using base class.
        CN: 使用基类更新文件数量显示。
        """
        return self.update_file_count_label(self.file_count_label)

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
        self.detect_layout_and_load_params(folder)
        self.update_preview(folder)
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
    
    # Removed select_input_folder and update_file_count (now in BasePanel / hook)

    def update_preview(self, folder):
        """
        EN: Render first image in folder and show bordered preview.
        CN: 渲染文件夹中第一张图片并展示带边框的预览。
        """
        try:
            images = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            if not images:
                self.preview_label.config(text="暂无预览 / No preview", image="")
                self._preview_img_ref = None
                self._full_preview_img = None
                return

            first_img = os.path.join(folder, images[0])

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

            # EN: Bump preview job id to avoid stale UI updates / CN: 提升预览任务编号以避免旧线程覆盖最新界面
            self.preview_job_id += 1
            job_id = self.preview_job_id

            loading_text = "正在生成预览..." if self.lang == "zh" else "Rendering preview..."
            self.preview_label.config(text=loading_text, image="")
            self._preview_img_ref = None
            self._full_preview_img = None

            def worker(img_path, job_mark, is_digital_mode, manual_film_keyword):
                temp_dir = None
                try:
                    temp_dir = tempfile.mkdtemp(prefix="gt23_preview_")
                    meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
                    data = meta.get_data(img_path, is_digital_mode=is_digital_mode, manual_film=manual_film_keyword)
                    
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
                    
                    renderer = FilmRenderer()
                    # EN: Downscale target edge for faster preview while keeping shadow / CN: 降低分辨率加快预览同时保留阴影
                    renderer.process_image(img_path, data, temp_dir, target_long_edge=1200)

                    out_name = f"GT23_{os.path.splitext(os.path.basename(img_path))[0]}.png"
                    out_path = os.path.join(temp_dir, out_name)
                    if not os.path.exists(out_path):
                        raise FileNotFoundError(out_name)

                    with Image.open(out_path) as img:
                        img = img.convert("RGB")
                        self._full_preview_img = img.copy() # Store full size

                    def apply_image():
                        if job_mark != getattr(self, 'preview_job_id', None):
                            return
                        self._perform_resize() # Use resize logic to set initial image

                    self.parent.after(0, apply_image)

                except Exception as e:
                    error_msg = str(e)  # Capture the error message
                    def apply_error():
                        if job_mark != getattr(self, 'preview_job_id', None):
                            return
                        fallback = f"预览失败: {error_msg}" if self.lang == "zh" else f"Preview failed: {error_msg}"
                        try:
                            # EN: Fallback to raw thumbnail if render fails / CN: 渲染失败时降级为原图缩略图
                            with Image.open(img_path) as img:
                                img = img.convert("RGB")
                                img.thumbnail((650, 400))
                                tk_img = ImageTk.PhotoImage(img)
                            self.preview_label.config(image=tk_img, text="")
                            self._preview_img_ref = tk_img
                        except Exception:
                            self.preview_label.config(text=fallback, image="")
                            self._preview_img_ref = None

                    self.parent.after(0, apply_error)

                finally:
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)

            self.preview_thread = threading.Thread(
                target=worker,
                args=(first_img, job_id, is_digital, manual_film),
                daemon=True
            )
            self.preview_thread.start()

        except Exception as e:
            fallback = f"预览失败: {e}" if self.lang == "zh" else f"Preview failed: {e}"
            self.preview_label.config(text=fallback, image="")
            self._preview_img_ref = None
    
    def on_mode_changed(self):
        """
        EN: Handle mode change
        CN: 处理模式切换
        """
        folder = self.input_folder_var.get()
        if folder and os.path.exists(folder):
            self.update_preview(folder)
    
    def on_auto_detect_changed(self):
        """
        EN: Handle auto-detect toggle
        CN: 处理自动检测切换
        """
        if self.auto_detect_var.get():
            self.film_combo.config(state="disabled")
        else:
            self.film_combo.config(state="normal")  # EN: Allow user input / CN: 允许用户输入
    
    def on_params_changed(self):
        """
        EN: Handle parameter changes - refresh preview
        CN: 处理参数变化 - 刷新预览
        """
        folder = self.input_folder_var.get()
        if folder and os.path.exists(folder):
            self.update_preview(folder)
    
    def start_processing(self):
        """
        EN: Start border processing
        CN: 开始边框处理
        """
        # EN: Validate inputs / CN: 验证输入
        input_folder = self.input_folder_var.get()
        if not input_folder or not os.path.exists(input_folder):
            messagebox.showwarning("警告 Warning", "请先选择输入文件夹\nPlease select input folder")
            return
        
        files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            messagebox.showwarning("警告 Warning", "输入文件夹中没有图片\nNo images in input folder")
            return
        
        # EN: Get manual film / CN: 获取手动胶片
        manual_film = None
        if self.mode_var.get() == "film" and not self.auto_detect_var.get():
            # EN: Get either selected or manually typed film name / CN: 获取选中或手动输入的胶片名
            film_input = self.film_combo.get().strip()
            if not film_input or film_input.startswith("--"):
                title = "警告" if self.lang == "zh" else "Warning"
                msg = "请选择或输入胶片类型" if self.lang == "zh" else "Please select or enter film type"
                messagebox.showwarning(title, msg)
                return
            # EN: If it's from the list, extract the keyword / CN: 如果是列表中的，提取关键字
            manual_film = film_input
            for display_name, keyword in self.film_list:
                if film_input == display_name:
                    manual_film = keyword
                    break
        
        # EN: Setup output / CN: 设置输出
        if getattr(sys, 'frozen', False):
            working_dir = os.path.dirname(sys.executable)
        else:
            working_dir = os.getcwd()
        output_folder = os.path.join(working_dir, "photos_out")
        os.makedirs(output_folder, exist_ok=True)
        
        # EN: UI state / CN: UI状态
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        msg = "开始处理..." if self.lang == "zh" else "Starting processing..."
        self.log(msg)
        self.log_text.config(state="disabled")
        
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress['value'] = 0
        self.process_button.config(state="disabled")
        
        # EN: Start worker thread / CN: 启动工作线程
        is_digital = self.mode_var.get() == "digital"
        
        # EN: Collect custom layout params / CN: 收集自定义布局参数
        custom_layout = {
            "side": self.side_ratio_var.get(),
            "top": self.top_ratio_var.get(),
            "bottom": self.bottom_ratio_var.get(),
            "font_scale": self.font_scale_var.get()
        }
        
        self.worker_thread = threading.Thread(
            target=self.process_worker,
            args=(input_folder, output_folder, is_digital, manual_film, custom_layout),
            daemon=True
        )
        self.worker_thread.start()
    
    def process_worker(self, input_dir, output_dir, is_digital, manual_film, custom_layout=None):
        """
        EN: Worker thread for processing
        CN: 处理工作线程
        """
        try:
            from apps.border_tool import process_border_batch
            
            def progress_callback(current, total, filename):
                percent = int((current / total) * 100)
                self.parent.after(0, lambda p=percent: self.progress.config(value=p))
                self.parent.after(0, lambda c=current, t=total, f=filename: self.log(f"[{c}/{t}] {f}"))
            
            result = process_border_batch(input_dir, output_dir, is_digital, manual_film, progress_callback, lang=self.lang, custom_layout=custom_layout)
            self.parent.after(0, lambda r=result: self.on_processing_complete(r))
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.parent.after(0, lambda msg=error_msg: self.on_processing_error(msg))
    
    def on_processing_complete(self, result):
        """
        EN: Handle processing completion
        CN: 处理完成回调
        """
        self.progress.pack_forget()
        self.process_button.config(state="normal")
        
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
            messagebox.showerror("错误 Error", result.get('message', 'Unknown error'))
    
    def on_processing_error(self, error_msg):
        """
        EN: Handle processing error
        CN: 处理错误回调
        """
        self.progress.pack_forget()
        self.process_button.config(state="normal")
        
        msg = f"\n✗ 发生错误\n{error_msg}" if self.lang == "zh" else f"\n✗ Error occurred\n{error_msg}"
        self.log(msg)
        messagebox.showerror("错误 Error", 
                           f"处理过程中发生错误 Error during processing:\n\n{error_msg[:200]}...\n\n如需帮助请联系\nFor help contact: xjames007@gmail.com")
    
    # Removed redundant log() implementation
