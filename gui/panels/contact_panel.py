# gui/panels/contact_panel.py
"""
EN: Contact Sheet panel for GUI (tkinter version)
CN: 底片索引 GUI 面板（tkinter版本）
"""

import os
import sys
import json
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from tkinter import scrolledtext
from core.metadata import MetadataHandler


class ContactPanel:
    """
    EN: Contact Sheet GUI panel
    CN: 底片索引图形界面面板
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.worker_thread = None
        self.film_list = []
        self.lang = "zh"  # EN: Default language / CN: 默认语言
        self.meta = MetadataHandler()  # EN: Initialize metadata handler / CN: 初始化元数据处理器
        self.setup_ui()
        self.load_film_library()
    
    def setup_ui(self):
        """
        EN: Setup user interface
        CN: 设置用户界面
        """
        # EN: Create a container for format and orientation side-by-side / CN: 创建格式和方向的并排容器
        top_container = ttk.Frame(self.parent)
        top_container.pack(fill=X, pady=(0, 10))
        
        # EN: Format display (auto-detected, read-only) / CN: 画幅显示（自动检测，只读）
        self.format_frame = ttk.Labelframe(top_container, text="画幅", padding=10)
        self.format_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 5))
        
        self.format_var = ttk.StringVar(value="")
        format_label = ttk.Label(self.format_frame, textvariable=self.format_var, font=("Microsoft YaHei UI", 11, "bold"), foreground="#2780e3")
        format_label.pack(anchor=W, pady=5)
        
        # EN: Store the actual format value separately / CN: 单独存储实际的画幅值
        self.detected_format = ""
        
        # EN: 645 orientation selection (show only when 645 is detected) / CN: 645方向选择（仅在检测到645时显示）
        self.orientation_frame = ttk.Labelframe(top_container, text="645 方向", padding=10)
        self.orientation_frame.pack_forget()  # Hide initially / 初始隐藏
        
        self.orientation_var = ttk.StringVar(value="L")
        self.orientations = [
            ("L", "垂直条(L) - 照片横向", "Vertical strip (L) - horizontal photo"),
            ("P", "水平条(P) - 照片竖向", "Horizontal strip (P) - vertical photo")
        ]
        
        self.orientation_radios = []
        for value, text_zh, text_en in self.orientations:
            radio = ttk.Radiobutton(self.orientation_frame, text=text_zh, variable=self.orientation_var, 
                          value=value, bootstyle="primary")
            radio.pack(anchor=W, pady=2)
            self.orientation_radios.append(radio)
        
        # EN: Input folder / CN: 输入文件夹
        self.folder_frame = ttk.Labelframe(self.parent, text="输入文件夹", padding=10)
        self.folder_frame.pack(fill=X, pady=(0, 10))
        
        input_row = ttk.Frame(self.folder_frame)
        input_row.pack(fill=X, pady=(0, 5))
        
        self.input_folder_var = ttk.StringVar()
        ttk.Entry(input_row, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        
        # EN: Refresh button / CN: 刷新按钮
        self.refresh_button = ttk.Button(input_row, text="刷新", command=self.refresh_format, bootstyle="info-outline", width=8)
        self.refresh_button.pack(side=RIGHT, padx=(2, 5))
        
        self.browse_button = ttk.Button(input_row, text="浏览", command=self.select_input_folder, bootstyle="info-outline")
        self.browse_button.pack(side=RIGHT)
        
        self.file_count_label = ttk.Label(self.folder_frame, text="未选择文件夹", foreground="gray")
        self.file_count_label.pack(anchor=W)
        
        # EN: Auto-detect photos_in / CN: 自动检测 photos_in
        self.auto_detect_photos_in()
        
        # EN: Film selection / CN: 胶片选择
        self.film_info_frame = ttk.Labelframe(self.parent, text="胶片信息", padding=10)
        self.film_info_frame.pack(fill=X, pady=(0, 10))
        
        self.auto_detect_var = ttk.BooleanVar(value=True)
        self.auto_detect_check = ttk.Checkbutton(self.film_info_frame, text="自动识别胶片（从EXIF）", 
                       variable=self.auto_detect_var, command=self.on_auto_detect_changed, 
                       bootstyle="round-toggle")
        self.auto_detect_check.pack(anchor=W, pady=(0, 5))
        
        film_row = ttk.Frame(self.film_info_frame)
        film_row.pack(fill=X, pady=5)
        self.manual_label = ttk.Label(film_row, text="手动选择:", width=20)
        self.manual_label.pack(side=LEFT)
        
        self.film_combo = ttk.Combobox(film_row, state="disabled")
        self.film_combo.pack(side=LEFT, fill=X, expand=YES)
        
        # EN: Emulsion number / CN: 乳剂号（可选）
        row3 = ttk.Frame(self.film_info_frame)
        row3.pack(fill=X, pady=5)
        self.emulsion_label = ttk.Label(row3, text="乳剂号 (可选):", width=20)
        self.emulsion_label.pack(side=LEFT)
        self.roll_id_var = ttk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.roll_id_var).pack(side=LEFT, fill=X, expand=YES)
        
        # EN: Generate button / CN: 生成按钮
        self.generate_button = ttk.Button(self.parent, text="生成接触印样", 
                                         command=self.start_generation, bootstyle="success", width=30)
        self.generate_button.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.parent, mode="indeterminate", bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress.pack_forget()  # Hide initially
        
        # EN: Log output / CN: 日志输出
        self.log_frame = ttk.Labelframe(self.parent, text="生成日志", padding=5)
        self.log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=15, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=BOTH, expand=YES)
    
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
            # EN: Auto-detect format from first image / CN: 从第一张照片自动检测画幅
            self.detect_and_set_format(folder)
    
    def auto_detect_photos_in(self):
        """
        EN: Auto-detect photos_in folder and detect format from first image
        CN: 自动检测 photos_in 文件夹并从第一张照片检测画幅
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
                
                # EN: Auto-detect format from first image / CN: 从第一张照片自动检测画幅
                self.detect_and_set_format(photos_in)
        except Exception:
            pass
    
    def detect_and_set_format(self, folder):
        """
        EN: Detect format from first image in folder
        CN: 从文件夹中的第一张照片检测画幅
        """
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if files:
                img_path = os.path.join(folder, files[0])
                detected_format = self.meta.detect_batch_layout([img_path])
                if detected_format:
                    self.detected_format = detected_format
                    # EN: Display only format code / CN: 只显示画幅代码
                    self.format_var.set(detected_format)
                    
                    # EN: Show/hide orientation frame based on format / CN: 根据画幅显示/隐藏方向选择
                    if detected_format == "645":
                        self.orientation_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0), after=self.format_frame)
                    else:
                        self.orientation_frame.pack_forget()
        except Exception:
            pass
    
    def refresh_format(self):
        """
        EN: Manually refresh format detection and file count from current input folder
        CN: 手动刷新当前输入文件夹的画幅检测和文件数量
        """
        folder = self.input_folder_var.get()
        if not folder or not os.path.exists(folder):
            msg = "请先选择输入文件夹" if self.lang == "zh" else "Please select input folder first"
            messagebox.showwarning("警告" if self.lang == "zh" else "Warning", msg)
            return
        
        # EN: Update file count / CN: 更新文件数量
        self.update_file_count()
        
        # EN: Detect format / CN: 检测画幅
        self.detect_and_set_format(folder)
        
        # EN: Show success message / CN: 显示成功消息
        if self.detected_format:
            msg = f"已刷新画幅: {self.detected_format}" if self.lang == "zh" else f"Format refreshed: {self.detected_format}"
            self.log(f"✓ {msg}")
        else:
            msg = "未能检测到画幅" if self.lang == "zh" else "Could not detect format"
            self.log(f"⚠ {msg}")
    
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
    
    def update_language(self, lang):
        """
        EN: Update UI language
        CN: 更新界面语言
        """
        self.lang = lang
        
        if lang == "zh":
            self.format_frame.config(text="画幅")
            self.orientation_frame.config(text="645 方向")
            for i, radio in enumerate(self.orientation_radios):
                _, text_zh, _ = self.orientations[i]
                radio.config(text=text_zh)
            
            self.folder_frame.config(text="输入文件夹")
            self.refresh_button.config(text="刷新")
            self.browse_button.config(text="浏览")
            self.film_info_frame.config(text="胶片信息")
            self.auto_detect_check.config(text="自动识别胶片（从EXIF）")
            self.manual_label.config(text="手动选择:")
            self.emulsion_label.config(text="乳剂号 (可选):")
            self.generate_button.config(text="生成接触印样")
            self.log_frame.config(text="生成日志")
            self.update_film_combo_values()
        else:
            self.format_frame.config(text="Format")
            self.orientation_frame.config(text="645 Orientation")
            for i, radio in enumerate(self.orientation_radios):
                _, _, text_en = self.orientations[i]
                radio.config(text=text_en)
            
            self.folder_frame.config(text="Input Folder")
            self.refresh_button.config(text="Refresh")
            self.browse_button.config(text="Browse")
            self.film_info_frame.config(text="Film Information")
            self.auto_detect_check.config(text="Auto Detect from EXIF")
            self.manual_label.config(text="Manual Select:")
            self.emulsion_label.config(text="Emulsion # (optional):")
            self.generate_button.config(text="Generate Contact Sheet")
            self.log_frame.config(text="Generation Log")
            self.update_film_combo_values()
        
        # EN: Refresh log with current language / CN: 使用当前语言刷新日志
        if self.film_list:
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
            msg = f"✓ 已加载 {len(self.film_list)} 种胶片" if lang == "zh" else f"✓ Loaded {len(self.film_list)} films"
            self.log(msg)
        
        # EN: Update file count display / CN: 更新文件数量显示
        self.update_file_count()
    
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
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.getcwd()
            
            config_path = os.path.join(base_path, 'config', 'films.json')
            
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
    
    def on_auto_detect_changed(self):
        """
        EN: Handle auto-detect toggle
        CN: 处理自动检测切换
        """
        if self.auto_detect_var.get():
            self.film_combo.config(state="disabled")
        else:
            self.film_combo.config(state="normal")  # EN: Allow user input / CN: 允许用户输入
    
    def start_generation(self):
        """
        EN: Start contact sheet generation
        CN: 开始生成接触印样
        """
        # EN: Get input folder / CN: 获取输入文件夹
        input_folder = self.input_folder_var.get()
        if not input_folder or not os.path.exists(input_folder):
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "请先选择输入文件夹\nPlease select input folder" if self.lang == "zh" else "Please select input folder first"
            messagebox.showwarning(title, msg)
            return
        
        files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "输入文件夹中没有图片\nNo images in input folder" if self.lang == "zh" else "No images in input folder"
            messagebox.showwarning(title, msg)
            return
        
        # EN: Get manual film / CN: 获取手动胶片
        manual_film = None
        if not self.auto_detect_var.get():
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
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress.start(10)
        self.generate_button.config(state="disabled")
        
        # EN: Collect parameters / CN: 收集参数
        # EN: Use detected format instead of ComboBox / CN: 使用检测到的画幅而非下拉框
        selected_format = self.detected_format
        orientation = self.orientation_var.get() if selected_format == "645" else None
        
        params = {
            'format': selected_format,
            'manual_film': manual_film,
            'emulsion_number': self.roll_id_var.get().strip() or "",  # EN: Use empty string instead of None / CN: 使用空字符串而非None
            'orientation': orientation,  # EN: Add orientation parameter / CN: 添加方向参数
            'input_folder': input_folder,
            'output_folder': output_folder
        }
        
        # EN: Start worker thread / CN: 启动工作线程
        self.worker_thread = threading.Thread(
            target=self.generation_worker,
            args=(params,),
            daemon=True
        )
        self.worker_thread.start()
    
    def generation_worker(self, params):
        """
        EN: Worker thread for generation
        CN: 生成工作线程
        """
        try:
            from apps.contact_sheet import ContactSheetPro
            
            # EN: Progress callback / CN: 进度回调
            def progress_update(message):
                self.parent.after(0, lambda msg=message: self.log(msg))
            
            # EN: Create contact sheet instance / CN: 创建接触印样实例
            contact = ContactSheetPro()
            
            # EN: Generate using the generate() method / CN: 使用generate()方法生成
            result = contact.generate(
                input_dir=params['input_folder'],
                orientation=params['orientation'],  # EN: Pass orientation parameter / CN: 传递方向参数
                output_dir=params['output_folder'],
                format=params['format'],
                manual_film=params['manual_film'],
                emulsion_number=params['emulsion_number'],
                lang=self.lang,  # EN: Localize messages / CN: 按当前语言输出
                progress_callback=progress_update
            )
            
            if result['success']:
                self.parent.after(0, lambda path=result['output_path']: self.on_generation_complete(path))
            else:
                self.parent.after(0, lambda msg=result['message']: self.on_generation_error(msg))
                
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.parent.after(0, lambda msg=error_msg: self.on_generation_error(msg))
    
    def on_generation_complete(self, result_path):
        """
        EN: Handle generation completion
        CN: 生成完成回调
        """
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_button.config(state="normal")
        
        self.log("\n✓ " + "="*50)
        msg1 = "✓ 生成完成！" if self.lang == "zh" else "✓ Generation complete!"
        msg2 = f"✓ 输出文件：{os.path.basename(result_path)}" if self.lang == "zh" else f"✓ Output: {os.path.basename(result_path)}"
        self.log(msg1)
        self.log(msg2)
        self.log("✓ " + "="*50)
        
        # EN: Show result dialog / CN: 显示结果对话框
        title = "完成" if self.lang == "zh" else "Complete"
        if self.lang == "zh":
            dialog_msg = (
                "接触印样生成完成！\n\n"
                f"{os.path.basename(result_path)}\n\n"
                "是否打开输出文件夹？"
            )
        else:
            dialog_msg = (
                "Contact sheet generated!\n\n"
                f"{os.path.basename(result_path)}\n\n"
                "Open output folder?"
            )
        response = messagebox.askyesno(title, dialog_msg)
        if response:
            try:
                os.startfile(os.path.dirname(result_path))
            except Exception as e:
                err_title = "错误" if self.lang == "zh" else "Error"
                err_msg = f"无法打开文件夹:\n{e}" if self.lang == "zh" else f"Failed to open folder:\n{e}"
                messagebox.showerror(err_title, err_msg)
    
    def on_generation_error(self, error_msg):
        """
        EN: Handle generation error
        CN: 生成错误回调
        """
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_button.config(state="normal")
        
        msg = f"\n✗ 发生错误\n{error_msg}" if self.lang == "zh" else f"\n✗ Error occurred\n{error_msg}"
        self.log(msg)
        err_title = "错误" if self.lang == "zh" else "Error"
        if self.lang == "zh":
            dialog_msg = (
                "生成过程中发生错误：\n\n"
                f"{error_msg[:200]}...\n\n"
                "如需帮助请联系：xjames007@gmail.com"
            )
        else:
            dialog_msg = (
                "Error during generation:\n\n"
                f"{error_msg[:200]}...\n\n"
                "For help contact: xjames007@gmail.com"
            )
        messagebox.showerror(err_title, dialog_msg)
    
    def log(self, message):
        """
        EN: Append message to log
        CN: 添加消息到日志
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
