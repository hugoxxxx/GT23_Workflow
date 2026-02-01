import os
import sys
import json
import threading
import platform
import subprocess
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
        self.load_film_library(on_success_callback=self.update_film_combo_values)
    
    def setup_ui(self):
        """
        EN: Setup user interface with two-column layout using Place geometry
        CN: 使用 Place 几何管理器设置双栏布局
        """
        from utils.i18n import get_string
        
        # ========== LEFT PANEL - 38% width ==========
        self.left_panel = ttk.Frame(self.parent)
        self.left_panel.place(relx=0, rely=0, relwidth=0.38, relheight=1.0)
        
        # EN: Settings Area / CN: 设置区域
        self.settings_frame = ttk.Frame(self.left_panel, padding=(10, 10, 5, 0))
        self.settings_frame.pack(fill=X)
        
        # 1. Folder Selection (Flat style like Border Tool)
        # CN: 文件夹选择（扁平化风格）
        f_row = ttk.Frame(self.settings_frame)
        f_row.pack(fill=X, pady=2)
        ttk.Entry(f_row, textvariable=self.input_folder_var, state="readonly", width=15).pack(side=LEFT, fill=X, expand=YES)
        self.browse_button = ttk.Button(f_row, text=get_string("browse", self.lang), command=self.select_input_folder)
        self.browse_button.pack(side=LEFT, padx=2)
        self.refresh_button = ttk.Button(f_row, text=get_string("refresh", self.lang), command=self.refresh_format)
        self.refresh_button.pack(side=LEFT)
        
        self.file_count_label = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 8), foreground="#444")
        self.file_count_label.pack(anchor=W, pady=(2, 10))

        # 2. Layout & Format (Header-based)
        # CN: 画幅与布局（标题标示）
        self.layout_title_label = ttk.Label(self.settings_frame, text="画幅与布局" if self.lang == "zh" else "Layout & Format", font=("Segoe UI", 8, "bold"), foreground="#666")
        self.layout_title_label.pack(anchor=W, pady=(10, 5))
        
        l_row = ttk.Frame(self.settings_frame)
        l_row.pack(fill=X, pady=2)
        
        self.format_title_label = ttk.Label(l_row, text=get_string("format", self.lang) + ":")
        self.format_title_label.pack(side=LEFT)
        self.format_label_val = ttk.Label(l_row, textvariable=self.format_var, font=("Segoe UI", 12, "bold"), foreground="#F58223")
        self.format_label_val.pack(side=LEFT, padx=5)
        
        # EN: 645 orientation selection / CN: 645方向选择
        orient_text = "645 方向" if self.lang == "zh" else "645 Orientation"
        self.orientation_frame = ttk.Labelframe(self.settings_frame, text=orient_text, padding=5)
        self.orientations = [
            ("L", "垂直条(L) - 照片横向", "Vertical strip (L) - horizontal photo"),
            ("P", "水平条(P) - 照片竖向", "Horizontal strip (P) - vertical photo")
        ]
        self.orientation_radios = []
        for value, text_zh, text_en in self.orientations:
            radio = ttk.Radiobutton(self.orientation_frame, text=text_zh if self.lang == "zh" else text_en, 
                                   variable=self.orientation_var, value=value)
            radio.pack(anchor=W, pady=1)
            self.orientation_radios.append(radio)

        # 3. Film Settings (Ref. Border tool)
        # CN: 胶片参数（参照边框工具风格）
        self.film_title_label = ttk.Label(self.settings_frame, text=get_string("film_info", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        self.film_title_label.pack(anchor=W, pady=(15, 5))
        
        # Row: Film Selection
        r2 = ttk.Frame(self.settings_frame)
        r2.pack(fill=X, pady=2)
        self.film_select_label = ttk.Label(r2, text="胶片:" if self.lang == "zh" else "Film:")
        self.film_select_label.pack(side=LEFT)
        self.auto_detect_check = ttk.Checkbutton(r2, text="自动" if self.lang == "zh" else "Auto Detect", 
                                               variable=self.auto_detect_var, command=self.on_auto_detect_changed, 
                                               bootstyle="secondary-round-toggle")
        self.auto_detect_check.pack(side=LEFT, padx=5)
        self.film_combo = ttk.Combobox(r2, state="readonly", width=18)
        self.film_combo.pack(side=LEFT, padx=5, fill=X, expand=YES)
        
        # Row: Emulsion Number (Specific to ContactSheet)
        r3 = ttk.Frame(self.settings_frame)
        r3.pack(fill=X, pady=2)
        self.emulsion_label = ttk.Label(r3, text=(get_string("emulsion", self.lang) + ":"))
        self.emulsion_label.pack(side=LEFT)
        ttk.Entry(r3, textvariable=self.roll_id_var).pack(side=LEFT, padx=5, fill=X, expand=YES)
        
        # 4. Features/Options
        self.option_title_label = ttk.Label(self.settings_frame, text=get_string("features", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        self.option_title_label.pack(anchor=W, pady=(15, 5))
        
        r4 = ttk.Frame(self.settings_frame)
        r4.pack(fill=X, pady=2)
        self.show_date_check = ttk.Checkbutton(r4, text=get_string("show_date", self.lang), variable=self.show_date_var, bootstyle="secondary-round-toggle")
        self.show_date_check.pack(side=LEFT, padx=(0, 20))
        self.show_exif_check = ttk.Checkbutton(r4, text=get_string("show_exif", self.lang), variable=self.show_exif_var, bootstyle="secondary-round-toggle")
        self.show_exif_check.pack(side=LEFT)
        
        # 3. Action Buttons (Bottom - Fixed)
        self.btn_frame = ttk.Frame(self.left_panel, padding=(10, 10, 5, 10))
        self.btn_frame.pack(side=BOTTOM, fill=X)
        self.generate_button = ttk.Button(self.btn_frame, text=get_string("generate_contact", self.lang), 
                                         command=self.start_generation, bootstyle="primary", padding=10)
        self.generate_button.pack(fill=X, pady=(0, 5))
        
        self.progress = ttk.Progressbar(self.btn_frame, mode="indeterminate", bootstyle="success-striped")
        self.progress.pack(fill=X)
        self.progress.pack_forget()

        # 4. Log Area (Middle - Expanding)
        self.log_section = ttk.Frame(self.left_panel, padding=(10, 10, 5, 0))
        self.log_section.pack(fill=BOTH, expand=YES)
        
        self.log_title_label = ttk.Label(self.log_section, text=get_string("log_title", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        self.log_title_label.pack(anchor=W, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(self.log_section, wrap=tk.WORD, state="disabled",
                                                 font=("Consolas", 10), background="#101010", foreground="#A0A0A0",
                                                 borderwidth=0)
        self.log_text.pack(fill=BOTH, expand=YES)

        # ========== RIGHT PANEL - 62% width ==========
        self.right_panel = ttk.Frame(self.parent)
        self.right_panel.place(relx=0.38, rely=0, relwidth=0.62, relheight=1.0)
        
        # EN: Preview area / CN: 预览区域
        self.preview_section = ttk.Frame(self.right_panel, padding=(15, 10, 10, 10))
        self.preview_section.pack(fill=BOTH, expand=YES)
        
        self.preview_title_label = ttk.Label(self.preview_section, text=get_string("preview", self.lang), font=("Segoe UI", 8, "bold"), foreground="#666")
        self.preview_title_label.pack(anchor=W, pady=(0, 5))
        
        no_p_text = get_string("no_preview", self.lang)
        self.preview_label = ttk.Label(self.preview_section, text=no_p_text, anchor="center")
        self.preview_label.pack(fill=BOTH, expand=YES)
        
        # EN: Initial updates / CN: 初始更新
        self.auto_detect_photos_in()
        self.on_auto_detect_changed()
        self.parent.after(200, self.update_film_combo_values)

    def update_film_combo_values(self):
        """
        EN: Update film combo box values
        CN: 更新胶片下拉框选项
        """
        if not self.film_list:
            return
            
        placeholder = "-- 请选择胶片 --" if self.lang == "zh" else "-- Select Film --"
        film_names = [placeholder] + [name for name, _ in self.film_list]
        
        # Force refresh display
        old_state = str(self.film_combo.cget('state'))
        self.film_combo.config(state='normal')
        self.film_combo['values'] = film_names
        
        current_idx = self.film_combo.current()
        if current_idx < 0:
            self.film_combo.current(0)
            self.film_combo.set(placeholder)
        else:
            self.film_combo.current(current_idx)
            val = film_names[current_idx] if current_idx < len(film_names) else placeholder
            self.film_combo.set(val)
        
        self.film_combo.config(state=old_state)

    def on_auto_detect_changed(self):
        """
        EN: Handle auto-detect toggle
        CN: 处理自动检测切换
        """
        if self.auto_detect_var.get():
            self.film_combo.config(state="disabled")
        else:
            self.film_combo.config(state="readonly")

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
                        self.orientation_frame.pack(anchor=W, fill=X, padx=10, pady=5)
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
        
        # Titles
        self.layout_title_label.config(text="画幅与布局" if lang == "zh" else "Layout & Format")
        self.film_title_label.config(text=get_string("film_info", lang))
        self.option_title_label.config(text=get_string("features", lang))
        self.log_title_label.config(text=get_string("log_title", lang))
        self.preview_title_label.config(text=get_string("preview", lang))
        
        # Labels
        self.format_title_label.config(text=get_string("format", lang) + ":")
        self.refresh_button.config(text=get_string("refresh", lang))
        self.browse_button.config(text=get_string("browse", lang))
        
        self.film_select_label.config(text="胶片:" if lang == "zh" else "Film:")
        self.auto_detect_check.config(text="自动" if lang == "zh" else "Auto Detect")
        self.emulsion_label.config(text=(get_string("emulsion", lang) + ":"))
        
        self.show_date_check.config(text=get_string("show_date", lang))
        self.show_exif_check.config(text=get_string("show_exif", lang))
        self.generate_button.config(text=get_string("generate_contact", lang))
        self.preview_label.config(text=get_string("no_preview", lang))

        self.update_file_count()
        
        # EN: Update orientation radios / CN: 更新方向选项按钮
        for i, radio in enumerate(self.orientation_radios):
            _, text_zh, text_en = self.orientations[i]
            radio.config(text=text_zh if lang == "zh" else text_en)
        
        # Clear and refresh log
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
        self.update_film_combo_values()

    def start_generation(self):
        """
        EN: Start contact sheet generation with thread safety check
        CN: 开始生成全卷缩略图（带线程安全检查）
        """
        if self.worker_thread is not None and self.worker_thread.is_alive():
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "生成任务正在运行中，请等待..." if self.lang == "zh" else "Generation task is already running, please wait..."
            messagebox.showwarning(title, msg)
            return
        
        input_folder = self.input_folder_var.get()
        if not input_folder or not os.path.exists(input_folder):
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "请先选择输入文件夹" if self.lang == "zh" else "Please select input folder first"
            messagebox.showwarning(title, msg)
            return
        
        files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            title = "警告" if self.lang == "zh" else "Warning"
            msg = "输入文件夹中没有图片" if self.lang == "zh" else "No images in input folder"
            messagebox.showwarning(title, msg)
            return
        
        manual_film = None
        if not self.auto_detect_var.get():
            film_input = self.film_combo.get().strip()
            if not film_input or film_input.startswith("--"):
                title = "警告" if self.lang == "zh" else "Warning"
                msg = "请选择或输入胶片类型" if self.lang == "zh" else "Please select or enter film type"
                messagebox.showwarning(title, msg)
                return
            manual_film = film_input
            for display_name, keyword in self.film_list:
                if film_input == display_name:
                    manual_film = keyword
                    break
        
        if getattr(sys, 'frozen', False):
            working_dir = os.path.dirname(sys.executable)
        else:
            working_dir = os.getcwd()
        output_folder = os.path.join(working_dir, "photos_out")
        os.makedirs(output_folder, exist_ok=True)
        
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        
        self.progress.pack(fill=X, pady=(0, 10))
        self.progress.start(10)
        self.generate_button.config(state="disabled")
        
        params = {
            'format': self.detected_format,
            'manual_film': manual_film,
            'emulsion_number': self.roll_id_var.get().strip() or "",
            'orientation': self.orientation_var.get() if self.detected_format == "645_6x8_43" else None,
            'show_date': self.show_date_var.get(),
            'show_exif': self.show_exif_var.get(),
            'input_folder': input_folder,
            'output_folder': output_folder
        }
        
        self.worker_thread = threading.Thread(
            target=self.generation_worker,
            args=(params,),
            daemon=True
        )
        self.worker_thread.start()
    
    def generation_worker(self, params):
        try:
            from apps.contact_sheet import ContactSheetPro
            def progress_update(message):
                self.parent.after(0, lambda msg=message: self.log(msg))
            contact = ContactSheetPro()
            result = contact.generate(
                input_dir=params['input_folder'],
                orientation=params['orientation'],
                output_dir=params['output_folder'],
                format=params['format'],
                manual_film=params['manual_film'],
                emulsion_number=params['emulsion_number'],
                show_date=params['show_date'],
                show_exif=params['show_exif'],
                lang=self.lang,
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
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_button.config(state="normal")
        self.log("\n✓ " + "="*50)
        self.log("✓ 生成完成！" if self.lang == "zh" else "✓ Generation complete!")
        self.log(f"✓ 输出文件：{os.path.basename(result_path)}" if self.lang == "zh" else f"✓ Output: {os.path.basename(result_path)}")
        self.log("✓ " + "="*50)
        
        title = "完成" if self.lang == "zh" else "Complete"
        if self.lang == "zh":
            dialog_msg = f"全卷缩略图生成完成！\n\n{os.path.basename(result_path)}\n\n是否打开输出文件夹？"
        else:
            dialog_msg = f"Contact sheet generated!\n\n{os.path.basename(result_path)}\n\nOpen output folder?"
        if messagebox.askyesno(title, dialog_msg):
            try:
                output_dir = os.path.dirname(result_path)
                system = platform.system()
                if system == "Windows": os.startfile(output_dir)
                elif system == "Darwin": subprocess.run(["open", output_dir])
                else: subprocess.run(["xdg-open", output_dir])
            except Exception as e:
                messagebox.showerror("错误" if self.lang == "zh" else "Error", str(e))
    
    def on_generation_error(self, error_msg):
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_button.config(state="normal")
        self.log(f"\n✗ 发生错误\n{error_msg}")
        messagebox.showerror("错误" if self.lang == "zh" else "Error", error_msg[:300])
