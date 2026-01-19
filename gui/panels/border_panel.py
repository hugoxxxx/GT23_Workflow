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
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from PIL import Image, ImageTk
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer


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
        self.film_list = []
        self.lang = lang  # EN: Use provided language / CN: 使用传入的语言
        
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
        EN: Setup user interface
        CN: 设置用户界面
        """
        # EN: Mode selection / CN: 模式选择
        mode_text = "工作模式" if self.lang == "zh" else "Working Mode"
        self.mode_frame = ttk.Labelframe(self.parent, text=mode_text, padding=10)
        self.mode_frame.pack(fill=X, pady=(0, 10))
        
        self.mode_var = ttk.StringVar(value="film")
        film_text = "胶片项目" if self.lang == "zh" else "Film Project"
        digital_text = "数码项目" if self.lang == "zh" else "Digital Project"
        self.film_radio = ttk.Radiobutton(self.mode_frame, text=film_text, variable=self.mode_var, 
                       value="film", command=self.on_mode_changed, bootstyle="primary")
        self.film_radio.pack(side=LEFT, padx=10)
        self.digital_radio = ttk.Radiobutton(self.mode_frame, text=digital_text, variable=self.mode_var, 
                       value="digital", command=self.on_mode_changed, bootstyle="primary")
        self.digital_radio.pack(side=LEFT)
        
        # EN: Input folder / CN: 输入文件夹
        folder_text = "输入文件夹" if self.lang == "zh" else "Input Folder"
        self.folder_frame = ttk.Labelframe(self.parent, text=folder_text, padding=10)
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
        
        # EN: Film selection / CN: 胶片选择
        film_selection_text = "胶片选择" if self.lang == "zh" else "Film Selection"
        self.film_selection_frame = ttk.Labelframe(self.parent, text=film_selection_text, padding=10)
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

        # EN: Advanced settings (border parameters) / CN: 高级设置（边框参数）
        advanced_text = "高级设置" if self.lang == "zh" else "Advanced Settings"
        self.advanced_frame = ttk.Labelframe(self.parent, text=advanced_text, padding=10)
        self.advanced_frame.pack(fill=X, pady=(0, 10))
        
        # EN: Side/Left-Right ratio / CN: 左右边框比例
        lr_row = ttk.Frame(self.advanced_frame)
        lr_row.pack(fill=X, pady=5)
        side_text = "左右边框" if self.lang == "zh" else "Side Margin"
        side_width = 12 if self.lang == "zh" else 15
        self.side_label = ttk.Label(lr_row, text=side_text, width=side_width)
        self.side_label.pack(side=LEFT)
        self.side_ratio_var = ttk.DoubleVar(value=0.04)
        side_entry = ttk.Entry(lr_row, textvariable=self.side_ratio_var, width=10)
        side_entry.pack(side=LEFT, padx=(0, 10))
        # EN: Bind to preview refresh / CN: 绑定预览刷新
        self.side_ratio_var.trace('w', lambda *args: self.on_params_changed())
        
        top_text = "顶部留白" if self.lang == "zh" else "Top Margin"
        self.top_label = ttk.Label(lr_row, text=top_text, width=side_width)
        self.top_label.pack(side=LEFT)
        self.top_ratio_var = ttk.DoubleVar(value=0.04)
        top_entry = ttk.Entry(lr_row, textvariable=self.top_ratio_var, width=10)
        top_entry.pack(side=LEFT)
        self.top_ratio_var.trace('w', lambda *args: self.on_params_changed())
        
        # EN: Bottom ratio / CN: 底部留白比例
        bottom_row = ttk.Frame(self.advanced_frame)
        bottom_row.pack(fill=X, pady=5)
        bottom_text = "底部留白" if self.lang == "zh" else "Bottom Margin"
        self.bottom_label = ttk.Label(bottom_row, text=bottom_text, width=side_width)
        self.bottom_label.pack(side=LEFT)
        self.bottom_ratio_var = ttk.DoubleVar(value=0.13)
        bottom_entry = ttk.Entry(bottom_row, textvariable=self.bottom_ratio_var, width=10)
        bottom_entry.pack(side=LEFT, padx=(0, 10))
        self.bottom_ratio_var.trace('w', lambda *args: self.on_params_changed())
        
        font_text = "字体基础" if self.lang == "zh" else "Font Scale"
        self.font_label = ttk.Label(bottom_row, text=font_text, width=side_width)
        self.font_label.pack(side=LEFT)
        self.font_scale_var = ttk.DoubleVar(value=0.032)
        font_entry = ttk.Entry(bottom_row, textvariable=self.font_scale_var, width=10)
        font_entry.pack(side=LEFT)
        self.font_scale_var.trace('w', lambda *args: self.on_params_changed())

        # EN: Preview area / CN: 预览区域
        preview_text = "预览（显示文件夹第一张图片）" if self.lang == "zh" else "Preview (First Image in Folder)"
        self.preview_frame = ttk.Labelframe(self.parent, text=preview_text, padding=10)
        self.preview_frame.pack(fill=BOTH, pady=(0, 10))
        no_preview_text = "暂无预览" if self.lang == "zh" else "No preview"
        self.preview_label = ttk.Label(self.preview_frame, text=no_preview_text, anchor="center")
        self.preview_label.pack(fill=BOTH, expand=YES)
        self._preview_img_ref = None  # EN: hold reference to avoid GC / CN: 保存引用防止被回收
        
        # EN: Process button / CN: 处理按钮
        process_text = "开始处理" if self.lang == "zh" else "Start Processing"
        self.process_button = ttk.Button(self.parent, text=process_text, 
                                         command=self.start_processing, bootstyle="success", width=20)
        self.process_button.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.parent, mode="determinate", bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress.pack_forget()  # Hide initially
        
        # EN: Log output / CN: 日志输出
        log_text = "处理日志" if self.lang == "zh" else "Processing Log"
        self.log_frame = ttk.Labelframe(self.parent, text=log_text, padding=5)
        self.log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=15, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=BOTH, expand=YES)
        
        # EN: Auto-detect photos_in / CN: 自动检测 photos_in
        self.auto_detect_photos_in()
    
    def update_language(self, lang):
        """
        EN: Update UI language
        CN: 更新界面语言
        """
        self.lang = lang
        
        if lang == "zh":
            self.mode_frame.config(text="工作模式")
            self.film_radio.config(text="胶片项目")
            self.digital_radio.config(text="数码项目")
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
            self.preview_frame.config(text="预览（显示文件夹第一张图片）")
            if not self._preview_img_ref:
                self.preview_label.config(text="暂无预览")
            self.process_button.config(text="开始处理")
            self.log_frame.config(text="处理日志")
            self.update_film_combo_values()
        else:
            self.mode_frame.config(text="Working Mode")
            self.film_radio.config(text="Film Project")
            self.digital_radio.config(text="Digital Project")
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
            self.preview_frame.config(text="Preview (First Image in Folder)")
            if not self._preview_img_ref:
                self.preview_label.config(text="No preview")
            self.process_button.config(text="Start Processing")
            self.log_frame.config(text="Processing Log")
            self.update_film_combo_values()
        
        # EN: Update file count label / CN: 更新文件计数标签
        self.update_file_count()
        
        # EN: Refresh log with current language / CN: 使用当前语言刷新日志
        if self.film_list:
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
            msg = f"✓ 已加载 {len(self.film_list)} 种胶片" if lang == "zh" else f"✓ Loaded {len(self.film_list)} films"
            self.log(msg)
    
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
            # EN: Use MetadataHandler resolver to locate films.json in dev/onefile/_MEIPASS
            # CN: 通过 MetadataHandler 的路径解析器定位 films.json（开发/单文件/_MEIPASS 均可）
            config_path = MetadataHandler._resolve_config_path('films.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                films_data = json.load(f)
            
            self.film_list = []
            for brand, films in films_data.items():
                for film_name in films.keys():
                    display_name = f"{brand} {film_name}"
                    self.film_list.append((display_name, film_name))
            
            self.film_list.sort()
            self.update_film_combo_values()
            
            msg = f"✓ 已加载 {len(self.film_list)} 种胶片" if self.lang == "zh" else f"✓ Loaded {len(self.film_list)} films"
            self.log(msg)
        except Exception as e:
            msg = f"✗ 胶片库加载失败: {e}" if self.lang == "zh" else f"✗ Film library load failed: {e}"
            self.log(msg)
    
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
                self.detect_layout_and_load_params(photos_in)
                self.update_preview(photos_in)
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
            self.update_file_count()
            self.detect_layout_and_load_params(folder)
            self.update_preview(folder)
    
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
                        img.thumbnail((800, 600))
                        tk_img = ImageTk.PhotoImage(img)

                    def apply_image():
                        if job_mark != getattr(self, 'preview_job_id', None):
                            return
                        self.preview_label.config(image=tk_img, text="")
                        self._preview_img_ref = tk_img

                    self.parent.after(0, apply_image)

                except Exception as e:
                    def apply_error():
                        if job_mark != getattr(self, 'preview_job_id', None):
                            return
                        fallback = f"预览失败: {e}" if self.lang == "zh" else f"Preview failed: {e}"
                        try:
                            # EN: Fallback to raw thumbnail if render fails / CN: 渲染失败时降级为原图缩略图
                            with Image.open(img_path) as img:
                                img = img.convert("RGB")
                                img.thumbnail((800, 600))
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
        is_film = self.mode_var.get() == "film"
        if is_film:
            self.film_selection_frame.pack(before=self.process_button, fill=X, pady=(0, 10))
        else:
            self.film_selection_frame.pack_forget()
    
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
    
    def log(self, message):
        """
        EN: Append message to log
        CN: 添加消息到日志
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
