# gui/panels/border_panel.py
"""
EN: Border Tool panel for GUI (tkinter version)
CN: 边框工具 GUI 面板（tkinter版本）
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


class BorderPanel:
    """
    EN: Border Tool GUI panel
    CN: 边框工具图形界面面板
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.worker_thread = None
        self.film_list = []
        self.lang = "zh"  # EN: Default language / CN: 默认语言
        self.setup_ui()
        self.load_film_library()
    
    def setup_ui(self):
        """
        EN: Setup user interface
        CN: 设置用户界面
        """
        # EN: Mode selection / CN: 模式选择
        self.mode_frame = ttk.Labelframe(self.parent, text="工作模式", padding=10)
        self.mode_frame.pack(fill=X, pady=(0, 10))
        
        self.mode_var = ttk.StringVar(value="film")
        self.film_radio = ttk.Radiobutton(self.mode_frame, text="胶片项目", variable=self.mode_var, 
                       value="film", command=self.on_mode_changed, bootstyle="primary")
        self.film_radio.pack(side=LEFT, padx=10)
        self.digital_radio = ttk.Radiobutton(self.mode_frame, text="数码项目", variable=self.mode_var, 
                       value="digital", command=self.on_mode_changed, bootstyle="primary")
        self.digital_radio.pack(side=LEFT)
        
        # EN: Input folder / CN: 输入文件夹
        self.folder_frame = ttk.Labelframe(self.parent, text="输入文件夹", padding=10)
        self.folder_frame.pack(fill=X, pady=(0, 10))
        
        input_row = ttk.Frame(self.folder_frame)
        input_row.pack(fill=X, pady=(0, 5))
        
        self.input_folder_var = ttk.StringVar()
        ttk.Entry(input_row, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        self.browse_button = ttk.Button(input_row, text="浏览", command=self.select_input_folder, bootstyle="info-outline")
        self.browse_button.pack(side=RIGHT)
        
        self.file_count_label = ttk.Label(self.folder_frame, text="未选择文件夹", foreground="gray")
        self.file_count_label.pack(anchor=W)
        
        # EN: Film selection / CN: 胶片选择
        self.film_selection_frame = ttk.Labelframe(self.parent, text="胶片选择", padding=10)
        self.film_selection_frame.pack(fill=X, pady=(0, 10))
        
        self.auto_detect_var = ttk.BooleanVar(value=True)
        self.auto_detect_check = ttk.Checkbutton(self.film_selection_frame, text="自动识别胶片（从EXIF）", 
                       variable=self.auto_detect_var, command=self.on_auto_detect_changed, 
                       bootstyle="round-toggle")
        self.auto_detect_check.pack(anchor=W, pady=(0, 5))
        
        film_row = ttk.Frame(self.film_selection_frame)
        film_row.pack(fill=X)
        self.manual_label = ttk.Label(film_row, text="手动选择:")
        self.manual_label.pack(side=LEFT, padx=(0, 10))
        
        self.film_combo = ttk.Combobox(film_row, state="disabled")
        self.film_combo.pack(side=LEFT, fill=X, expand=YES)
        
        # EN: Process button / CN: 处理按钮
        self.process_button = ttk.Button(self.parent, text="开始处理", 
                                         command=self.start_processing, bootstyle="success", width=20)
        self.process_button.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.parent, mode="determinate", bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress.pack_forget()  # Hide initially
        
        # EN: Log output / CN: 日志输出
        self.log_frame = ttk.Labelframe(self.parent, text="处理日志", padding=5)
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
            self.browse_button.config(text="浏览")
            self.film_selection_frame.config(text="胶片选择")
            self.auto_detect_check.config(text="自动识别胶片（从EXIF）")
            self.manual_label.config(text="手动选择:")
            self.process_button.config(text="开始处理")
            self.log_frame.config(text="处理日志")
            self.update_film_combo_values()
        else:
            self.mode_frame.config(text="Working Mode")
            self.film_radio.config(text="Film Project")
            self.digital_radio.config(text="Digital Project")
            self.folder_frame.config(text="Input Folder")
            self.browse_button.config(text="Browse")
            self.film_selection_frame.config(text="Film Selection")
            self.auto_detect_check.config(text="Auto Detect from EXIF")
            self.manual_label.config(text="Manual Select:")
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
        except Exception:
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
        self.worker_thread = threading.Thread(
            target=self.process_worker,
            args=(input_folder, output_folder, is_digital, manual_film),
            daemon=True
        )
        self.worker_thread.start()
    
    def process_worker(self, input_dir, output_dir, is_digital, manual_film):
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
            
            result = process_border_batch(input_dir, output_dir, is_digital, manual_film, progress_callback, lang=self.lang)
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
                    os.startfile(output_folder)
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
