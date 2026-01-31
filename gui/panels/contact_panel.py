import os
import sys
import json
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk

from gui.panels.base_panel import BasePanel
from utils.paths import get_asset_path, get_working_dir
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer

class ContactPanel(BasePanel):
    """
    EN: Contact Sheet GUI panel
    CN: 底片索引图形界面面板
    """
    
    def __init__(self, parent, lang="en"):
        """
        Args:
            parent: Parent widget / 父部件
            lang: UI language ("zh" or "en") / 界面语言（\"zh\" 或 \"en\"）
        """
        super().__init__(parent, lang)
        self.worker_thread = None
        self.meta = MetadataHandler()
        
        # EN: Initialize Tk variables / CN: 初始化 Tk 变量
        self.format_var = ttk.StringVar(value="")
        self.orientation_var = ttk.StringVar(value="L")
        self.auto_detect_var = ttk.BooleanVar(value=True)
        self.show_date_var = ttk.BooleanVar(value=True)
        self.show_exif_var = ttk.BooleanVar(value=True)
        self.roll_id_var = ttk.StringVar(value="")

        self.setup_ui()
        self.load_film_library()
    
    def setup_ui(self):
        """
        EN: Setup user interface with two-column layout
        CN: 设置双栏布局的用户界面
        """
        # EN: Create PanedWindow for flexible split / CN: 创建水平分割窗格
        self.paned = ttk.Panedwindow(self.parent, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES)
        
        self.left_panel = ttk.Frame(self.paned)
        self.right_panel = ttk.Frame(self.paned, width=350)
        
        self.paned.add(self.left_panel, weight=1)
        self.paned.add(self.right_panel, weight=0)

        # --- LEFT PANEL: Settings ---
        
        # EN: Create a container for format and orientation side-by-side / CN: 创建格式和方向的并排容器
        top_container = ttk.Frame(self.left_panel)
        top_container.pack(fill=X, pady=(0, 10))
        
        # EN: Format display / CN: 画幅显示
        self.format_row = ttk.Frame(top_container)
        self.format_row.pack(side=LEFT, fill=BOTH, expand=YES)
        
        from utils.i18n import get_string
        
        self.format_title_label = ttk.Label(self.format_row, text=get_string("format", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        format_label = ttk.Label(self.format_row, textvariable=self.format_var, font=("Segoe UI", 14, "bold"), foreground="#F58223")
        format_label.pack(anchor=W, pady=(2, 0))
        
        # EN: Store the actual format value separately / CN: 单独存储实际的画幅值
        self.detected_format = ""
        
        # EN: 645 orientation selection (show only when 645 is detected) / CN: 645方向选择（仅在检测到645时显示）
        orient_text = "645 方向" if self.lang == "zh" else "645 Orientation"
        self.orientation_frame = ttk.Labelframe(top_container, text=orient_text, padding=10)
        self.orientation_frame.pack_forget()  # Hide initially / 初始隐藏
        
        self.orientation_var = ttk.StringVar(value="L")
        self.orientations = [
            ("L", "垂直条(L) - 照片横向", "Vertical strip (L) - horizontal photo"),
            ("P", "水平条(P) - 照片竖向", "Horizontal strip (P) - vertical photo")
        ]
        
        self.orientation_radios = []
        for value, text_zh, text_en in self.orientations:
            radio = ttk.Radiobutton(self.orientation_frame, text="", variable=self.orientation_var, 
                          value=value, bootstyle="primary")
            radio.pack(anchor=W, pady=2)
            self.orientation_radios.append(radio)
        
        # EN: Input folder / CN: 输入文件夹
        self.folder_section = ttk.Frame(self.left_panel, padding=(0, 10))
        self.folder_section.pack(fill=X)
        
        self.folder_title_label = ttk.Label(self.folder_section, text=get_string("input_folder", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        self.folder_title_label.pack(anchor=W, pady=(0, 5))
        
        input_row = ttk.Frame(self.folder_section)
        input_row.pack(fill=X)
        
        self.input_folder_var = ttk.StringVar()
        ttk.Entry(input_row, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        
        # EN: Refresh button / CN: 刷新按钮
        self.refresh_button = ttk.Button(input_row, text=get_string("refresh", self.lang), command=self.refresh_format, width=10)
        self.refresh_button.pack(side=RIGHT, padx=(5, 0))
        
        self.browse_button = ttk.Button(input_row, text=get_string("browse", self.lang), command=self.select_input_folder, width=10)
        self.browse_button.pack(side=RIGHT)
        
        self.file_count_label = ttk.Label(self.folder_section, text="", font=("Segoe UI", 8), foreground="#444")
        self.file_count_label.pack(anchor=W, pady=(5, 0))
        
        # EN: Separator / CN: 分割线
        ttk.Separator(self.left_panel, orient=HORIZONTAL).pack(fill=X, pady=15)

        # EN: Film selection / CN: 胶片选择
        self.film_section = ttk.Frame(self.left_panel)
        self.film_section.pack(fill=X)
        
        self.film_title_label = ttk.Label(self.film_section, text=get_string("film_info", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        self.film_title_label.pack(anchor=W, pady=(0, 10))
        
        self.auto_detect_check = ttk.Checkbutton(self.film_section, text=get_string("auto_detect", self.lang), 
                       variable=self.auto_detect_var, command=self.on_auto_detect_changed, 
                       bootstyle="secondary-round-toggle")
        self.auto_detect_check.pack(anchor=W, pady=(0, 10))
        
        film_row = ttk.Frame(self.film_section)
        film_row.pack(fill=X, pady=5)
        self.manual_label = ttk.Label(film_row, text=get_string("manual_select", self.lang), width=15)
        self.manual_label.pack(side=LEFT)
        
        self.film_combo = ttk.Combobox(film_row, state="disabled")
        self.film_combo.pack(side=LEFT, fill=X, expand=YES)
        
        # EN: Emulsion and Options Grid / CN: 乳剂号与选项网格排列
        grid_frame = ttk.Frame(self.film_section)
        grid_frame.pack(fill=X, pady=5)
        
        self.emulsion_label = ttk.Label(grid_frame, text=get_string("emulsion", self.lang))
        self.emulsion_label.grid(row=0, column=0, sticky=W, padx=(0, 10), pady=5)
        ttk.Entry(grid_frame, textvariable=self.roll_id_var, width=25).grid(row=0, column=1, sticky=W)
        
        options_frame = ttk.Frame(self.film_section)
        options_frame.pack(fill=X, pady=10)
        self.show_date_check = ttk.Checkbutton(options_frame, text=get_string("show_date", self.lang), variable=self.show_date_var, bootstyle="secondary-round-toggle")
        self.show_date_check.pack(side=LEFT, padx=(0, 20))
        self.show_exif_check = ttk.Checkbutton(options_frame, text=get_string("show_exif", self.lang), variable=self.show_exif_var, bootstyle="secondary-round-toggle")
        self.show_exif_check.pack(side=LEFT)
        
        # EN: Separator / CN: 分割线
        ttk.Separator(self.left_panel, orient=HORIZONTAL).pack(fill=X, pady=15)

        # EN: Generate button / CN: 生成按钮
        btn_frame = ttk.Frame(self.left_panel)
        btn_frame.pack(fill=X, pady=30)
        btn_text = "生成全卷缩略图" if self.lang == "zh" else "Generate Contact Sheet"
        self.generate_button = ttk.Button(btn_frame, text=btn_text, 
                                         command=self.start_generation, style="Action.TButton")
        self.generate_button.pack(expand=YES)
        
        self.progress = ttk.Progressbar(self.left_panel, mode="indeterminate", bootstyle="success-striped")
        self.progress.pack(fill=X, pady=(0, 10), padx=50)
        self.progress.pack_forget()  # Hide initially
        
        # --- RIGHT PANEL: Logs ---
        
        # EN: Log output / CN: 日志输出
        self.log_section = ttk.Frame(self.right_panel, padding=(15, 10, 0, 10))
        self.log_section.pack(fill=BOTH, expand=YES)
        
        self.log_title_label = ttk.Label(self.log_section, text="任务日志" if self.lang == "zh" else "Log", font=("Segoe UI", 8, "bold"), foreground="#666")
        self.log_title_label.pack(anchor=W, pady=(0, 5))
        
        # EN: Set minimum height for log area / CN: 设置日志区域最小高度
        self.log_text = scrolledtext.ScrolledText(self.log_section, wrap=tk.WORD, state="disabled", width=35,
                                                 font=("Consolas", 10), background="#101010", foreground="#A0A0A0",
                                                 insertbackground="white", borderwidth=0)
        self.log_text.pack(fill=BOTH, expand=YES)
    
    def on_folder_selected(self, folder):
        """
        EN: Handle folder selection.
        CN: 处理文件夹选择。
        """
        self.update_file_count()
        self.detect_and_set_format(folder)
    
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
                    if detected_format == "645_6x8_43":
                        self.orientation_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0), after=self.format_frame)
                    else:
                        self.orientation_frame.pack_forget()
        except Exception:
            # EN: Format detection failed, silent fail is OK / CN: 画幅检测失败，静默失败可接受
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
        EN: Update file count using base class.
        CN: 使用基类更新文件数量。
        """
        return self.update_file_count_label(self.file_count_label)
    
    def update_language(self, lang):
        """
        EN: Update UI language
        CN: 更新界面语言
        """
        self.lang = lang
        from utils.i18n import get_string
        
        self.format_title_label.config(text=get_string("format", lang))
        self.folder_title_label.config(text=get_string("input_folder", lang))
        self.refresh_button.config(text=get_string("refresh", lang))
        self.browse_button.config(text=get_string("browse", lang))
        self.film_title_label.config(text=get_string("film_info", lang))
        self.auto_detect_check.config(text=get_string("auto_detect", lang))
        self.manual_label.config(text=get_string("manual_select", lang))
        self.emulsion_label.config(text=get_string("emulsion", lang))
        self.show_date_check.config(text=get_string("show_date", lang))
        self.show_exif_check.config(text=get_string("show_exif", lang))
        self.generate_button.config(text=get_string("generate_contact", lang))
        # Note: log_section is a Frame, not a Label, so it doesn't have a text attribute

        self.update_file_count()
        
        # EN: Update orientation radios / CN: 更新方向选项按钮
        for i, radio in enumerate(self.orientation_radios):
            _, text_zh, text_en = self.orientations[i]
            radio.config(text=text_zh if lang == "zh" else text_en)
        
        # Clear and refresh log
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    
    # Removed redundant load_film_library and log_ready_status
    
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
        EN: Start contact sheet generation with thread safety check
        CN: 开始生成全卷缩略图（带线程安全检查）
        """
        # EN: Check if worker thread is already running / CN: 检查工作线程是否已在运行
        if self.worker_thread is not None and self.worker_thread.is_alive():
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "生成任务正在运行中，请等待..." if self.lang == "zh" else "Generation task is already running, please wait..."
            messagebox.showwarning(title, msg)
            return
        
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
        orientation = self.orientation_var.get() if selected_format == "645_6x8_43" else None
        
        params = {
            'format': selected_format,
            'manual_film': manual_film,
            'emulsion_number': self.roll_id_var.get().strip() or "",  # EN: Use empty string instead of None / CN: 使用空字符串而非None
            'orientation': orientation,  # EN: Add orientation parameter / CN: 添加方向参数
            'show_date': self.show_date_var.get(),
            'show_exif': self.show_exif_var.get(),
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
            
            # EN: Create contact sheet instance / CN: 创建缩略图生成器实例
            contact = ContactSheetPro()
            
            # EN: Generate using the generate() method / CN: 使用generate()方法生成
            result = contact.generate(
                input_dir=params['input_folder'],
                orientation=params['orientation'],  # EN: Pass orientation parameter / CN: 传递方向参数
                output_dir=params['output_folder'],
                format=params['format'],
                manual_film=params['manual_film'],
                emulsion_number=params['emulsion_number'],
                show_date=params['show_date'],
                show_exif=params['show_exif'],
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
                "全卷缩略图生成完成！\n\n"
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
                # EN: Cross-platform folder opening / CN: 跨平台打开文件夹
                output_dir = os.path.dirname(result_path)
                system = platform.system()
                if system == "Windows":
                    os.startfile(output_dir)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", output_dir])
                else:  # Linux and others
                    subprocess.run(["xdg-open", output_dir])
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
    
    # Removed redundant log() implementation
