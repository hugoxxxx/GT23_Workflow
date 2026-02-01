# gui/panels/matin_panel.py
"""
EN: Matin Slide Mode panel for GUI
CN: Matin 幻灯片模式 GUI 面板
"""

import os
import sys
import threading
import platform
import subprocess
import tempfile
import shutil
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
from gui.panels.base_panel import BasePanel
from utils.i18n import get_string
from core.metadata import MetadataHandler
from apps.contact_sheet import ContactSheetPro

class MatinPanel(BasePanel):
    def __init__(self, parent, lang="en"):
        super().__init__(parent, lang)
        self.meta = MetadataHandler()
        
        from utils.paths import get_asset_path
        
        # EN: Scan for fonts / CN: 扫描字体
        self.font_files = [] # List of filenames
        self.font_map = {}   # Name -> Full Path
        try:
            assets_font_dir = os.path.join(os.path.dirname(get_asset_path("GT23_Icon.png")), "fonts", "slide")
            if os.path.exists(assets_font_dir):
                for f in os.listdir(assets_font_dir):
                    if f.lower().endswith((".ttf", ".otf")):
                        self.font_files.append(f)
                        self.font_map[f] = os.path.join(assets_font_dir, f)
        except Exception as e:
            print(f"Font scan error: {e}")
            
        default_font = "ArchitectsDaughter-Regular.ttf"
        if default_font not in self.font_files and self.font_files:
            default_font = self.font_files[0]
            
        self.font_var = ttk.StringVar(value=default_font)

        # EN: Logic Data / CN: 逻辑数据
        self.img_list = []
        self.current_img_index = 0
        self.overrides = {} # map: filename -> {'l1': str, 'l2': str}
        
        # EN: Variables / CN: 变量
        self.matin_format_var = ttk.StringVar(value="MATIN_135")
        self.show_date_var = tk.BooleanVar(value=True)
        self.show_exif_var = tk.BooleanVar(value=True)
        
        self.global_l1_var = ttk.StringVar()
        self.global_l2_var = ttk.StringVar()
        self.local_l1_var = ttk.StringVar()
        self.local_l2_var = ttk.StringVar()
        
        # EN: New controls for Y-offset and Font Size / CN: 新增位置偏移与字号控制
        # Values are offsets from default: format_name logic / baseline
        self.l1_y_off_var = ttk.IntVar(value=0)
        self.l1_fs_off_var = ttk.IntVar(value=0)
        self.l2_y_off_var = ttk.IntVar(value=0)
        self.l2_fs_off_var = ttk.IntVar(value=0)
        
        # Link trace / 链路追踪
        for v in [self.l1_y_off_var, self.l1_fs_off_var, self.l2_y_off_var, self.l2_fs_off_var]:
            v.trace_add("write", self.on_detail_param_change)
            
        # EN: Handwriting (jitter) config / CN: 手写体（抖动）配置
        self.jitter_cfg = {
            'word_spacing': 0.15,
            'line_spacing': 1.3,
            'perturb_x_sigma': 0.5,
            'perturb_y_sigma': 0.5,
            'perturb_theta_sigma': 0.03,
            'perturb_size_sigma': 0.02
        }
        
        # EN: Preview state / CN: 预览状态
        self._preview_img_ref = None
        self._full_preview_img = None
        self.preview_job_id = 0
        self._resize_job = None
        self._debounce_job = None
        
        self.setup_ui()
        self.auto_detect_photos_in()


    def setup_ui(self):
        """
        EN: Setup user interface with two-column layout using Place geometry
        CN: 使用 Place 几何管理器设置双栏布局
        """
        # ========== LEFT PANEL - 38% width ==========
        self.left_panel = ttk.Frame(self.parent)
        self.left_panel.place(relx=0, rely=0, relwidth=0.38, relheight=1.0)
        
        # EN: Settings Area / CN: 设置区域
        self.settings_frame = ttk.Frame(self.left_panel, padding=(10, 10, 5, 0))
        self.settings_frame.pack(fill=X)
        
        # Row 1: Folder Selection
        r1 = ttk.Frame(self.settings_frame)
        r1.pack(fill=X, pady=5)
        ttk.Entry(r1, textvariable=self.input_folder_var, state="readonly", width=15).pack(side=LEFT, fill=X, expand=YES)
        self.browse_button = ttk.Button(r1, text=get_string("browse", self.lang), command=self.select_input_folder)
        self.browse_button.pack(side=LEFT, padx=2)
        
        # File Count Label
        self.file_count_label = ttk.Label(self.settings_frame, text="", font=("Segoe UI", 8), foreground="#444")
        self.file_count_label.pack(anchor=W, pady=(0, 10))

        # 2. Slide Settings
        self.settings_labelframe = ttk.Labelframe(self.left_panel, text=get_string("matin_style", self.lang), padding=10)
        self.settings_labelframe.pack(fill=X, padx=10, pady=5)
        
        # Format Selection
        r2 = ttk.Frame(self.settings_labelframe)
        r2.pack(fill=X, pady=5)
        self.format_label = ttk.Label(r2, text=get_string("format", self.lang) + ":")
        self.format_label.pack(side=TOP, anchor=W)
        
        radio_container = ttk.Frame(r2)
        radio_container.pack(fill=X, pady=(5, 0))
        
        self.formats_list = [
            ("MATIN_135", "135"),
            ("MATIN_645", "120 (645)"),
            ("MATIN_66", "120 (66)"),
            ("MATIN_67", "120 (67)")
        ]
        
        self.format_radios = []
        for i, (val, label) in enumerate(self.formats_list):
            row = i // 2
            col = i % 2
            rb = ttk.Radiobutton(radio_container, text=label, variable=self.matin_format_var, value=val)
            rb.grid(row=row, column=col, sticky=W, padx=(0, 15), pady=2)
            self.format_radios.append(rb)

        # Font Selection
        r_font = ttk.Frame(self.settings_labelframe)
        r_font.pack(fill=X, pady=5)
        ttk.Label(r_font, text="Font:", width=10).pack(side=LEFT)
        if self.font_files:
            self.font_combo = ttk.Combobox(r_font, textvariable=self.font_var, values=self.font_files, state="readonly")
            self.font_combo.pack(side=LEFT, fill=X, expand=YES)
        else:
            ttk.Label(r_font, text="(No fonts found)", foreground="red").pack(side=LEFT)
            
        # NEW: Handright Settings Button
        self.btn_jitter = ttk.Button(r_font, text="手写设置" if self.lang == "zh" else "Handwriting Settings", 
                                     command=self.open_handright_dialog, bootstyle="outline-secondary", width=12)
        self.btn_jitter.pack(side=LEFT, padx=(5, 0))

        # NEW: Regenerate Button
        self.btn_refresh = ttk.Button(r_font, text="重新生成" if self.lang == "zh" else "Regenerate", 
                                      command=self.on_detail_param_change, bootstyle="outline-info", width=12)
        self.btn_refresh.pack(side=LEFT, padx=(5, 0))
        
        # Global Custom Text
        r_txt = ttk.Frame(self.settings_labelframe)
        r_txt.pack(fill=X, pady=10)
        
        # Line 1 Row
        l1_head = ttk.Frame(r_txt)
        l1_head.pack(fill=X)
        ttk.Label(l1_head, text="Line 1 (Title):", font=("Segoe UI", 8)).pack(side=LEFT)
        
        # Controls for L1
        l1_ctrl = ttk.Frame(r_txt)
        l1_ctrl.pack(fill=X, pady=(0, 5))
        ttk.Entry(l1_ctrl, textvariable=self.global_l1_var).pack(side=LEFT, fill=X, expand=YES)
        
        # Y and Size adjustment
        ttk.Label(l1_ctrl, text="Y:", font=("Segoe UI", 8)).pack(side=LEFT, padx=(5, 0))
        ttk.Spinbox(l1_ctrl, from_=-100, to=100, width=4, textvariable=self.l1_y_off_var).pack(side=LEFT, padx=2)
        ttk.Label(l1_ctrl, text="Size:", font=("Segoe UI", 8)).pack(side=LEFT, padx=(5, 0))
        ttk.Spinbox(l1_ctrl, from_=-50, to=50, width=4, textvariable=self.l1_fs_off_var).pack(side=LEFT, padx=2)
        
        # Line 2 Row
        l2_head = ttk.Frame(r_txt)
        l2_head.pack(fill=X)
        ttk.Label(l2_head, text="Line 2 (Info):", font=("Segoe UI", 8)).pack(side=LEFT)
        
        # Controls for L2
        l2_ctrl = ttk.Frame(r_txt)
        l2_ctrl.pack(fill=X)
        ttk.Entry(l2_ctrl, textvariable=self.global_l2_var).pack(side=LEFT, fill=X, expand=YES)
        
        # Y and Size adjustment
        ttk.Label(l2_ctrl, text="Y:", font=("Segoe UI", 8)).pack(side=LEFT, padx=(5, 0))
        ttk.Spinbox(l2_ctrl, from_=-100, to=100, width=4, textvariable=self.l2_y_off_var).pack(side=LEFT, padx=2)
        ttk.Label(l2_ctrl, text="Size:", font=("Segoe UI", 8)).pack(side=LEFT, padx=(5, 0))
        ttk.Spinbox(l2_ctrl, from_=-50, to=50, width=4, textvariable=self.l2_fs_off_var).pack(side=LEFT, padx=2)


        # Options
        r3 = ttk.Frame(self.settings_labelframe)
        r3.pack(fill=X, pady=5)
        self.check_date = ttk.Checkbutton(r3, text=get_string("show_date", self.lang), variable=self.show_date_var, bootstyle="secondary-round-toggle")
        self.check_date.pack(side=LEFT)
        self.check_exif = ttk.Checkbutton(r3, text=get_string("show_exif", self.lang), variable=self.show_exif_var, bootstyle="secondary-round-toggle")
        self.check_exif.pack(side=LEFT, padx=15)
        
        # 3. Action Buttons
        self.btn_frame = ttk.Frame(self.left_panel, padding=(10, 5, 5, 10))
        self.btn_frame.pack(side=BOTTOM, fill=X)
        self.generate_button = ttk.Button(
            self.btn_frame, 
            text=get_string("generate_slides", self.lang), 
            command=self.start_generation, 
            bootstyle="primary",
            padding=10
        )
        self.generate_button.pack(fill=X)

        # 4. Detail Preview Area
        self.detail_section = ttk.Frame(self.left_panel, padding=(10, 10, 5, 0))
        self.detail_section.pack(fill=BOTH, expand=YES)
        
        detail_title_text = "细节预览 & 单张校正" if self.lang == "zh" else "Detail Preview & Correction"
        self.detail_title = ttk.Label(self.detail_section, text=detail_title_text, font=("Segoe UI", 8, "bold"), foreground="#666")
        self.detail_title.pack(anchor=W, pady=(0, 5))

        # Local Override Fields (Pack Bottom First)
        self.local_frame = ttk.Frame(self.detail_section)
        self.local_frame.pack(side=BOTTOM, fill=X, pady=5)
        
        r_l1 = ttk.Frame(self.local_frame)
        r_l1.pack(fill=X, pady=2)
        ttk.Label(r_l1, text="L1:", width=3).pack(side=LEFT)
        entry_l1 = ttk.Entry(r_l1, textvariable=self.local_l1_var)
        entry_l1.pack(side=LEFT, fill=X, expand=YES)
        
        r_l2 = ttk.Frame(self.local_frame)
        r_l2.pack(fill=X, pady=2)
        ttk.Label(r_l2, text="L2:", width=3).pack(side=LEFT)
        entry_l2 = ttk.Entry(r_l2, textvariable=self.local_l2_var)
        entry_l2.pack(side=LEFT, fill=X, expand=YES)

        # Navigation Bar (Pack Bottom Second)
        self.nav_frame = ttk.Frame(self.detail_section)
        self.nav_frame.pack(side=BOTTOM, fill=X, pady=5)
        
        ttk.Button(self.nav_frame, text="<", width=3, command=self.on_nav_prev, bootstyle="secondary-outline").pack(side=LEFT)
        self.nav_label = ttk.Label(self.nav_frame, text="0 / 0", width=10, anchor="center")
        self.nav_label.pack(side=LEFT, expand=YES)
        ttk.Button(self.nav_frame, text=">", width=3, command=self.on_nav_next, bootstyle="secondary-outline").pack(side=RIGHT)
        
        # Container for the detail image (Pack Last to fill Remaining)
        self.detail_container = ttk.Frame(self.detail_section, bootstyle="secondary")
        self.detail_container.pack(fill=BOTH, expand=YES)
        
        self.detail_preview_label = ttk.Label(self.detail_container, text=get_string("no_preview", self.lang), anchor="center")
        self.detail_preview_label.pack(fill=BOTH, expand=YES, padx=1, pady=1)

        # References
        self._detail_img_ref = None
        self._full_detail_img = None

        # ========== RIGHT PANEL ==========
        self.right_panel = ttk.Frame(self.parent)
        self.right_panel.place(relx=0.38, rely=0, relwidth=0.62, relheight=1.0)
        
        # EN: Preview area / CN: 预览区域
        self.preview_section = ttk.Frame(self.right_panel, padding=(15, 10, 10, 10))
        self.preview_section.pack(fill=BOTH, expand=YES)
        
        self.preview_title_label = ttk.Label(self.preview_section, text="排版概览" if self.lang == "zh" else "Layout Video", font=("Segoe UI", 8, "bold"), foreground="#666")
        self.preview_title_label.pack(anchor=W, pady=(0, 5))
        
        no_p_text = "暂无预览" if self.lang == "zh" else "No Preview"
        self.preview_label = ttk.Label(self.preview_section, text=no_p_text, anchor="center")
        self.preview_label.pack(fill=BOTH, expand=YES)

        # Traces & Binds
        self.preview_label.bind("<Configure>", self.on_preview_resize)
        self.detail_preview_label.bind("<Configure>", self.on_detail_resize)
        
        self.matin_format_var.trace_add("write", lambda *args: self.on_params_changed())
        self.show_date_var.trace_add("write", lambda *args: self.on_params_changed())
        self.show_exif_var.trace_add("write", lambda *args: self.on_params_changed())
        if self.font_files:
            self.font_var.trace_add("write", self.on_detail_param_change)
        
        # Custom input traces (Debounced)
        self.global_l1_var.trace_add("write", self.on_detail_param_change)
        self.global_l2_var.trace_add("write", self.on_detail_param_change)
        self.local_l1_var.trace_add("write", self.on_local_change)
        self.local_l2_var.trace_add("write", self.on_local_change)

        
    def start_generation(self):
        input_dir = self.input_folder_var.get()
        if not input_dir or not os.path.exists(input_dir):
            tk.messagebox.showwarning(get_string("warning", self.lang), get_string("select_folder_first", self.lang))
            return
            
        output_dir = os.path.join(input_dir, "..", "photos_out")
        
        # Resolve Font Path
        font_path = None
        if self.font_files:
            sel_font = self.font_var.get()
            font_path = self.font_map.get(sel_font)
        
        self.generate_button.config(state="disabled")
        
        thread = threading.Thread(target=self.generation_worker, args=(input_dir, output_dir, font_path, self.jitter_cfg))
        thread.daemon = True
        thread.start()
        
    def open_handright_dialog(self):
        """EN: Open Handright Settings Dialog / CN: 打开手写体参数设置窗口"""
        dialog = HandrightSettingsDialog(self.parent, self.jitter_cfg, self.lang)
        self.parent.wait_window(dialog)
        # After dialog closes, jitter_cfg is updated, trigger preview
        self.on_detail_param_change()
        
    def generation_worker(self, input_dir, output_dir, font_path=None, jitter_cfg=None):
        try:
            handler = ContactSheetPro()
            result = handler.generate(
                input_dir=input_dir,
                output_dir=output_dir,
                format=self.matin_format_var.get(),
                show_date=self.show_date_var.get(),
                show_exif=self.show_exif_var.get(),
                progress_callback=print,
                lang=self.lang,
                overrides=self.overrides, # Pass overrides
                global_l1=self.global_l1_var.get(),
                global_l2=self.global_l2_var.get(),
                font_path=font_path,
                label_cfg={
                    'l1_y_offset': self.l1_y_off_var.get(),
                    'l1_fs_offset': self.l1_fs_off_var.get(),
                    'l2_y_offset': self.l2_y_off_var.get(),
                    'l2_fs_offset': self.l2_fs_off_var.get()
                },
                jitter_cfg=jitter_cfg
            )
            
            if result['success']:
                self.parent.after(0, lambda: tk.messagebox.showinfo("GT23", get_string("success", self.lang)))
            else:
                self.parent.after(0, lambda msg=result['message']: tk.messagebox.showerror("Error", msg))
        except Exception as e:
            self.parent.after(0, lambda msg=str(e): tk.messagebox.showerror("Error", msg))
        finally:
            self.parent.after(0, lambda: self.generate_button.config(state="normal"))

    def on_folder_selected(self, folder):
        self.update_file_count_label(self.file_count_label)
        # Scan and reset
        images = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        self.img_list = images
        self.current_img_index = 0
        self.overrides = {} 
        self.update_nav_label()
        self.sync_local_ui()
        self.update_preview(folder)

    def on_nav_prev(self):
        if not self.img_list: return
        self.current_img_index = max(0, self.current_img_index - 1)
        self.update_nav_label()
        self.sync_local_ui() # Pull overrides to UI
        self.update_preview_detail_only()

    def on_nav_next(self):
        if not self.img_list: return
        self.current_img_index = min(len(self.img_list) - 1, self.current_img_index + 1)
        self.update_nav_label()
        self.sync_local_ui()
        self.update_preview_detail_only()
        
    def update_nav_label(self):
        total = len(self.img_list)
        current = self.current_img_index + 1 if total > 0 else 0
        self.nav_label.config(text=f"{current} / {total}")

    def sync_local_ui(self):
        """Update local inputs based on current image override or default to empty (implying global)"""
        if not self.img_list: return
        fname = self.img_list[self.current_img_index]
        ov = self.overrides.get(fname, {})
        
        # Avoid triggering trace updates by unbinding temporarily? 
        # Or just handle the cascade gracefully. Debounce helps.
        # But setting var triggers write.
        # We need a flag to ignore update.
        self._ignore_trace = True
        self.local_l1_var.set(ov.get('l1', ''))
        self.local_l2_var.set(ov.get('l2', ''))
        self._ignore_trace = False
        
    def on_detail_param_change(self, *args):
        if getattr(self, '_ignore_trace', False): return
        self.debounce_update_detail()

    def on_global_change(self, *args):
        self.debounce_update()

    def on_local_change(self, *args):
        if getattr(self, '_ignore_trace', False): return
        # Update overrides data immediately?
        if self.img_list:
            fname = self.img_list[self.current_img_index]
            l1 = self.local_l1_var.get()
            l2 = self.local_l2_var.get()
            if l1 or l2:
                self.overrides[fname] = {'l1': l1, 'l2': l2}
            else:
                if fname in self.overrides: del self.overrides[fname]
        
        self.debounce_update_detail()

    def on_params_changed(self):
        folder = self.input_folder_var.get()
        if folder and os.path.exists(folder):
            self.update_preview(folder)
            
    def debounce_update(self):
        if self._debounce_job: self.parent.after_cancel(self._debounce_job)
        self._debounce_job = self.parent.after(300, lambda: self.update_preview(self.input_folder_var.get()))

    def debounce_update_detail(self):
        # Only update detail view
        if self._debounce_job: self.parent.after_cancel(self._debounce_job)
        self._debounce_job = self.parent.after(300, self.update_preview_detail_only)

    def update_preview_detail_only(self):
        folder = self.input_folder_var.get()
        if not folder or not self.img_list: return
        
        # Resolve Font Path
        font_path = None
        if self.font_files:
            sel_font = self.font_var.get()
            font_path = self.font_map.get(sel_font)
        
        self.preview_job_id += 1
        job_id = self.preview_job_id
        
        def worker():
            try:
                handler = ContactSheetPro()
                fname = self.img_list[self.current_img_index]
                path = os.path.join(folder, fname)
                
                # Determine text
                ov = self.overrides.get(fname, {})
                c_l1 = ov.get('l1') if ov.get('l1') else self.global_l1_var.get()
                c_l2 = ov.get('l2') if ov.get('l2') else self.global_l2_var.get()
                
                detail_img = handler.generate_single(
                    img_path=path,
                    format=self.matin_format_var.get(),
                    show_date=self.show_date_var.get(),
                    show_exif=self.show_exif_var.get(),
                    custom_l1=c_l1,
                    custom_l2=c_l2,
                    font_path=font_path,
                    label_cfg={
                        'l1_y_offset': self.l1_y_off_var.get(),
                        'l1_fs_offset': self.l1_fs_off_var.get(),
                        'l2_y_offset': self.l2_y_off_var.get(),
                        'l2_fs_offset': self.l2_fs_off_var.get()
                    },
                    jitter_cfg=self.jitter_cfg
                )
                
                if job_id != self.preview_job_id: return
                
                if detail_img:
                    mem = detail_img.convert("RGB").copy()
                    def apply():
                        if job_id != self.preview_job_id: return
                        self._full_detail_img = mem
                        self._perform_resize(target="detail")
                    self.parent.after(0, apply)
            except Exception as e:
                print(e)
                
        threading.Thread(target=worker, daemon=True).start()

    def update_preview(self, folder):
        """Full update incl layout"""
        try:
            if not self.img_list:
                images = sorted([f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                self.img_list = images
                self.update_nav_label()
            
            if not self.img_list:
                self.preview_label.config(text=get_string("no_preview", self.lang), image="")
                self.detail_preview_label.config(text=get_string("no_preview", self.lang), image="")
                return

            # Resolve Font Path
            font_path = None
            if self.font_files:
                sel_font = self.font_var.get()
                font_path = self.font_map.get(sel_font)

            self.preview_job_id += 1
            job_id = self.preview_job_id
            
            loading_text = "正在生成预览..." if self.lang == "zh" else "Rendering..."
            self.preview_label.config(text=loading_text, image="")
            
            def worker():
                temp_dir = None
                try:
                    # 1. Layout Preview (Wireframe) - Uses Global Text mainly
                    temp_dir = tempfile.mkdtemp(prefix="gt23_matin_preview_")
                    handler = ContactSheetPro()
                    
                    result_layout = handler.generate(
                        input_dir=folder,
                        output_dir=temp_dir,
                        format=self.matin_format_var.get(),
                        show_date=self.show_date_var.get(),
                        show_exif=self.show_exif_var.get(),
                        limit=20, 
                        lang=self.lang,
                        target_w=1024,
                        preview_mode=True,
                        global_l1=self.global_l1_var.get(),
                        global_l2=self.global_l2_var.get(),
                        font_path=font_path,
                        label_cfg={
                            'l1_y_offset': self.l1_y_off_var.get(),
                            'l1_fs_offset': self.l1_fs_off_var.get(),
                            'l2_y_offset': self.l2_y_off_var.get(),
                            'l2_fs_offset': self.l2_fs_off_var.get()
                        },
                        jitter_cfg=self.jitter_cfg
                    )
                    
                    if job_id != self.preview_job_id: return
                    
                    # 2. Detail Preview
                    fname = self.img_list[self.current_img_index]
                    path = os.path.join(folder, fname)
                    ov = self.overrides.get(fname, {})
                    c_l1 = ov.get('l1') if ov.get('l1') else self.global_l1_var.get()
                    c_l2 = ov.get('l2') if ov.get('l2') else self.global_l2_var.get()
                    
                    detail_img = handler.generate_single(
                        img_path=path,
                        format=self.matin_format_var.get(),
                        show_date=self.show_date_var.get(),
                        show_exif=self.show_exif_var.get(),
                        custom_l1=c_l1,
                        custom_l2=c_l2,
                        font_path=font_path,
                        label_cfg={
                            'l1_y_offset': self.l1_y_off_var.get(),
                            'l1_fs_offset': self.l1_fs_off_var.get(),
                            'l2_y_offset': self.l2_y_off_var.get(),
                            'l2_fs_offset': self.l2_fs_off_var.get()
                        }
                    )
                    
                    if job_id != self.preview_job_id: return

                    # --- PRELOAD INTO MEMORY ---
                    layout_img_mem = None
                    if result_layout['success'] and os.path.exists(result_layout['output_path']):
                        try:
                            with Image.open(result_layout['output_path']) as img:
                                layout_img_mem = img.convert("RGB").copy()
                        except Exception as e:
                            print(f"Error loading layout preview: {e}")
                    
                    detail_img_mem = None
                    if detail_img:
                        detail_img_mem = detail_img.convert("RGB").copy()

                    # --- UPDATE UI ---
                    def apply_ui():
                        if job_id != self.preview_job_id: return
                        
                        # Apply Layout Preview
                        if layout_img_mem:
                            self._full_preview_img = layout_img_mem
                            self._perform_resize(target="layout")
                        else:
                            msg = result_layout.get('message', 'Unknown Error')
                            self.preview_label.config(text=f"Layout Error: {msg}")

                        # Apply Detail Preview
                        if detail_img_mem:
                            self._full_detail_img = detail_img_mem
                            self._perform_resize(target="detail")
                        else:
                            self.detail_preview_label.config(text="Detail Error")
                            
                    self.parent.after(0, apply_ui)
                        
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    def error_log():
                        if job_id == self.preview_job_id:
                            self.preview_label.config(text=f"Error: {e}", image="")
                    self.parent.after(0, error_log)
                finally:
                    if temp_dir and os.path.exists(temp_dir):
                        try:
                            shutil.rmtree(temp_dir, ignore_errors=True)
                        except: pass

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            self.preview_label.config(text=f"Error: {e}", image="")
    def on_detail_resize(self, event):
        """EN: Handle detail preview resize"""
        if not self._full_detail_img: return
        self._perform_resize(target="detail")

    def on_preview_resize(self, event):
        """EN: Handle preview resize / CN: 处理预览图缩放"""
        if not self._full_preview_img: return
        if self._resize_job: self.parent.after_cancel(self._resize_job)
        self._resize_job = self.parent.after(100, lambda: self._perform_resize(target="layout"))

    def _perform_resize(self, target="layout"):
        """
        EN: Perform resizing for specified target ('layout' or 'detail')
        """
        try:
            if target == "layout":
                if not self._full_preview_img: return
                w = self.preview_label.winfo_width() - 20
                h = self.preview_label.winfo_height() - 20
                if w < 50 or h < 50: return
                
                img = self._full_preview_img.copy()
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.preview_label.config(image=tk_img, text="")
                self._preview_img_ref = tk_img
                
            elif target == "detail":
                if not self._full_detail_img: return
                w = self.detail_preview_label.winfo_width()
                h = self.detail_preview_label.winfo_height()
                if w < 20 or h < 20: return # Allow tighter fit
                
                img = self._full_detail_img.copy()
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.detail_preview_label.config(image=tk_img, text="")
                self._detail_img_ref = tk_img
                
        except Exception as e:
            print(f"Resize Error ({target}): {e}")
        finally:
            self._resize_job = None

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
        self.generate_button.config(text=get_string("generate_slides", lang))
        self.preview_title_label.config(text="排版概览" if lang == "zh" else "Layout Video") # Corrected translation
        self.detail_title.config(text="细节预览 & 单张校正" if lang == "zh" else "Detail Preview & Correction")
        
        # Refresh preview text if no image
        if not self._full_preview_img:
            self.preview_label.config(text=get_string("no_preview", lang))
        
        # New button
        self.btn_jitter.config(text="手写设置" if lang == "zh" else "Handwriting Settings")
        self.btn_refresh.config(text="重新生成" if lang == "zh" else "Regenerate")


class HandrightSettingsDialog(tk.Toplevel):
    def __init__(self, parent, jitter_cfg, lang="en"):
        super().__init__(parent)
        self.jitter_cfg = jitter_cfg
        self.lang = lang
        
        self.title("手写配置" if lang == "zh" else "Handwriting Settings")
        self.geometry("480x700")
        self.minsize(400, 400)
        self.resizable(True, True) # EN: Allow user to drag / CN: 允许手动拉大
        self.grab_set() # Modal
        
        self.setup_ui()
        
    def setup_ui(self):
        # EN: Create Scrollable Container / CN: 创建可滚动容器
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # EN: Sync width / CN: 同步宽度
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.window_id, width=event.width)
        self.canvas.bind("<Configure>", on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # EN: Layout / CN: 布局
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        # EN: Mousewheel / CN: 鼠标滚轮
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # EN: Content Container / CN: 内容容器
        container = ttk.Frame(self.scrollable_frame, padding=20)
        container.pack(fill=BOTH, expand=YES)
        
        ttl = "手写引擎参数调节" if self.lang == "zh" else "Handwriting Engine Parameters"
        ttk.Label(container, text=ttl, font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))
        
        # 1. Letter Spacing (word_spacing)
        self.create_slider(container, "字距 (Letter Spacing):", 'word_spacing', 0.0, 1.0, 0.01)
        
        # 2. Line Spacing (line_spacing)
        self.create_slider(container, "行距 (Line Spacing):", 'line_spacing', 0.5, 3.0, 0.1)
        
        ttk.Separator(container, orient=HORIZONTAL).pack(fill=X, pady=20)
        
        jt_ttl = "随机抖动幅度 (Random Jitter):" if self.lang == "zh" else "Random Jitter Magnitudes:"
        ttk.Label(container, text=jt_ttl, font=("Segoe UI", 10, "bold")).pack(anchor=W)
        
        # 3. X Jitter
        self.create_slider(container, "X 轴抖动 (X Jitter):", 'perturb_x_sigma', 0.0, 2.0, 0.1)
        
        # 4. Y Jitter
        self.create_slider(container, "Y 轴抖动 (Y Jitter):", 'perturb_y_sigma', 0.0, 2.0, 0.1)
        
        # 5. Rotation Jitter
        self.create_slider(container, "角度旋转抖动 (Rotation):", 'perturb_theta_sigma', 0.0, 0.1, 0.005)
        
        # 6. Size Jitter
        self.create_slider(container, "字号大小抖动 (Size Var):", 'perturb_size_sigma', 0.0, 0.1, 0.005)
        
        btn_txt = "确定 (Done)" if self.lang == "zh" else "Done"
        btn = ttk.Button(container, text=btn_txt, command=self.destroy, bootstyle="primary", padding=12)
        btn.pack(fill=X, pady=(30, 0))

    def create_slider(self, parent, label_text, key, from_, to_, res):
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=10)
        
        ttk.Label(frame, text=label_text, font=("Segoe UI", 9)).pack(anchor=W)
        
        val_var = ttk.DoubleVar(value=self.jitter_cfg.get(key, 0))
        
        def update_cfg(*args):
            try:
                self.jitter_cfg[key] = val_var.get()
            except: pass
            
        val_var.trace_add("write", update_cfg)
        
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill=X, pady=(2, 0))
        
        scale = ttk.Scale(ctrl_frame, from_=from_, to=to_, variable=val_var, orient=HORIZONTAL, bootstyle="info")
        scale.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        
        spin = ttk.Spinbox(ctrl_frame, from_=from_, to=to_, increment=res, textvariable=val_var, width=8)
        spin.pack(side=LEFT)


