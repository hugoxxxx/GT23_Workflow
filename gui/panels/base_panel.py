# gui/panels/base_panel.py
import os
import json
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from utils.paths import get_config_path, get_working_dir

from utils.i18n import get_string

class BasePanel:
    """
    EN: Base class for GUI panels with shared logic.
    CN: 包含共享逻辑的 GUI 面板基类。
    """
    def __init__(self, parent, lang="en"):
        self.parent = parent
        self.lang = lang
        self.film_list = []
        self.input_folder_var = tk.StringVar()
        
    def select_input_folder(self):
        """
        EN: Open folder selection dialog.
        CN: 打开文件夹选择对话框。
        """
        initial_dir = get_working_dir()
        folder = filedialog.askdirectory(initialdir=initial_dir)
        if folder:
            self.input_folder_var.set(folder)
            self.on_folder_selected(folder)
            
    def on_folder_selected(self, folder):
        pass

    def log(self, message):
        if hasattr(self, 'log_text'):
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

    def load_film_library(self, on_success_callback=None):
        try:
            config_path = get_config_path('films.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                films_data = json.load(f)
            
            self.film_list = []
            for brand, films in films_data.items():
                for film_name in films.keys():
                    display_name = f"{brand} {film_name}"
                    self.film_list.append((display_name, film_name))
            
            self.film_list.sort()
            if on_success_callback:
                on_success_callback()
                
            self.log(get_string("load_films_success", self.lang, count=len(self.film_list)))
        except Exception as e:
            self.log(get_string("load_films_fail", self.lang, error=str(e)))

    def update_file_count_label(self, label_widget):
        folder = self.input_folder_var.get()
        if not folder or not os.path.exists(folder):
            label_widget.config(text=get_string("no_folder", self.lang), foreground="gray")
            return 0
        
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            count = len(files)
            if count > 0:
                label_widget.config(text=get_string("found_photos", self.lang, count=count), foreground="green")
            else:
                label_widget.config(text=get_string("no_images", self.lang), foreground="red")
            return count
        except Exception as e:
            label_widget.config(text=f"Error: {e}", foreground="red")
            return 0

    def auto_detect_photos_in(self):
        """
        EN: Auto-detect photos_in folder on startup.
        CN: 启动时自动检测 photos_in 文件夹。
        """
        try:
            photos_in = get_working_dir("photos_in")
            if os.path.exists(photos_in):
                self.input_folder_var.set(photos_in)
                self.on_folder_selected(photos_in)
        except Exception:
            pass
