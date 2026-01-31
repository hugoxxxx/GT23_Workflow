# gui/panels/matin_panel.py
"""
EN: Matin Slide Mode panel for GUI
CN: Matin 幻灯片模式 GUI 面板
"""

import os
import sys
import threading
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.panels.base_panel import BasePanel
from utils.i18n import get_string
from core.metadata import MetadataHandler
from apps.contact_sheet import ContactSheetPro

class MatinPanel(BasePanel):
    def __init__(self, parent, lang="en"):
        super().__init__(parent, lang)
        self.meta = MetadataHandler()

        
        # EN: Variables / CN: 变量
        self.matin_format_var = ttk.StringVar(value="MATIN_135")
        self.show_date_var = tk.BooleanVar(value=True)
        self.show_exif_var = tk.BooleanVar(value=True)
        
        self.setup_ui()
        self.auto_detect_photos_in()


    def setup_ui(self):
        # EN: Main container - using self.parent to attach to the notebook frame
        # CN: 主容器 - 使用 self.parent 挂载到 notebook 框架
        self.paned = ttk.Panedwindow(self.parent, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES)



        
        # EN: Left part: Settings / CN: 左侧：设置
        self.left_panel = ttk.Frame(self.paned, padding=(0, 0, 10, 0))
        self.paned.add(self.left_panel, weight=1)
        
        # 1. Folder Selection
        folder_frame = ttk.Frame(self.left_panel)
        folder_frame.pack(fill=X, pady=5)
        
        ttk.Entry(folder_frame, textvariable=self.input_folder_var, state="readonly").pack(side=LEFT, fill=X, expand=YES)
        self.browse_button = ttk.Button(folder_frame, text=get_string("browse", self.lang), command=self.select_input_folder, width=6)
        self.browse_button.pack(side=LEFT, padx=2)
        
        self.file_count_label = ttk.Label(self.left_panel, text="", font=("Segoe UI", 8))
        self.file_count_label.pack(anchor=W)

        
        # 2. Slide Settings
        self.settings_labelframe = ttk.Labelframe(self.left_panel, text=get_string("matin_style", self.lang), padding=15)
        self.settings_labelframe.pack(fill=X, pady=10)
        
        # Format Selection
        r1 = ttk.Frame(self.settings_labelframe)
        r1.pack(fill=X, pady=5)
        self.format_label = ttk.Label(r1, text=get_string("format", self.lang) + ":")
        self.format_label.pack(side=LEFT)
        
        self.rb135 = ttk.Radiobutton(r1, text="135 (4x5, 5x5cm)", variable=self.matin_format_var, value="MATIN_135")
        self.rb135.pack(side=LEFT, padx=10)
        self.rb120 = ttk.Radiobutton(r1, text="120 (3x4, 7.7x7cm)", variable=self.matin_format_var, value="MATIN_120")
        self.rb120.pack(side=LEFT, padx=10)
        
        # Options
        r2 = ttk.Frame(self.settings_labelframe)
        r2.pack(fill=X, pady=5)
        self.check_date = ttk.Checkbutton(r2, text=get_string("show_date", self.lang), variable=self.show_date_var)
        self.check_date.pack(side=LEFT)
        self.check_exif = ttk.Checkbutton(r2, text=get_string("show_exif", self.lang), variable=self.show_exif_var)
        self.check_exif.pack(side=LEFT, padx=15)
        
        # 3. Action Buttons
        self.generate_button = ttk.Button(
            self.left_panel, 
            text=get_string("generate_slides", self.lang), 
            command=self.start_generation, 
            bootstyle="primary"
        )
        self.generate_button.pack(fill=X, pady=20)

        
        # 4. Log Area
        log_frame = ttk.Labelframe(self.left_panel, text=get_string("log_title", self.lang), padding=10)
        log_frame.pack(fill=BOTH, expand=YES, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=10, state="disabled", font=("Consolas", 9), background="#1A1A1A", foreground="#00FF00", borderwidth=0)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scrollbar.set)


        
        # EN: Right part: Preview Placeholder / CN: 右侧：预览占位
        self.right_panel = ttk.Frame(self.paned)
        self.paned.add(self.right_panel, weight=2)
        
        self.preview_label = ttk.Label(self.right_panel, text=get_string("no_preview", self.lang), anchor=CENTER)
        self.preview_label.pack(fill=BOTH, expand=YES)
        
    def start_generation(self):
        input_dir = self.input_folder_var.get()
        if not input_dir or not os.path.exists(input_dir):
            tk.messagebox.showwarning(get_string("warning", self.lang), get_string("select_folder_first", self.lang))
            return
            
        output_dir = os.path.join(input_dir, "..", "photos_out")
        
        self.generate_button.config(state="disabled")
        self.log(f"--- {get_string('generate_slides', self.lang)} ---")
        
        thread = threading.Thread(target=self.generation_worker, args=(input_dir, output_dir))
        thread.daemon = True
        thread.start()
        
    def generation_worker(self, input_dir, output_dir):
        try:
            handler = ContactSheetPro()
            result = handler.generate(
                input_dir=input_dir,
                output_dir=output_dir,
                format=self.matin_format_var.get(),
                show_date=self.show_date_var.get(),
                show_exif=self.show_exif_var.get(),
                progress_callback=self.log,
                lang=self.lang
            )
            
            if result['success']:
                self.log(f"✓ {get_string('success', self.lang)}")
                self.parent.after(0, lambda: tk.messagebox.showinfo("GT23", get_string("success", self.lang)))
            else:
                self.log(f"✗ {result['message']}")
        except Exception as e:
            self.log(f"✗ Error: {e}")
        finally:
            self.parent.after(0, lambda: self.generate_button.config(state="normal"))

    def on_folder_selected(self, folder):
        """EN: Handle folder selection / CN: 处理文件夹选择"""
        self.update_file_count_label(self.file_count_label)

    def update_language(self, lang):
        """EN: Update UI language / CN: 更新界面语言"""
        self.lang = lang
        # Update Folder Section
        self.browse_button.config(text=get_string("browse", lang))
        self.update_file_count_label(self.file_count_label)
        
        # Update Settings Section
        self.settings_labelframe.config(text=get_string("matin_style", lang))
        self.format_label.config(text=get_string("format", lang) + ":")
        self.check_date.config(text=get_string("show_date", lang))
        self.check_exif.config(text=get_string("show_exif", lang))
        
        # Update Log Area
        # self.log_frame is not a member yet, so use a local find or a ref
        # For now, update the main button
        self.generate_button.config(text=get_string("generate_slides", lang))
        
        # Update Preview/Log headers if they were stored
        self.preview_label.config(text=get_string("no_preview", lang))

