# gui/panels/border_panel.py
"""
EN: Border Tool panel for GUI
CN: 边框工具 GUI 面板
"""

import os
import sys
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QRadioButton, QLabel, QLineEdit, QPushButton, 
                               QComboBox, QTextEdit, QFileDialog, QProgressBar,
                               QCheckBox, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal


class BorderWorker(QThread):
    """
    EN: Worker thread for border processing to avoid UI freezing
    CN: 边框处理工作线程，避免界面冻结
    """
    progress = Signal(int, int, str)  # current, total, filename
    finished = Signal(dict)  # result dictionary
    error = Signal(str)  # error message
    
    def __init__(self, input_dir, output_dir, is_digital, manual_film=None):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.is_digital = is_digital
        self.manual_film = manual_film
    
    def run(self):
        """
        EN: Execute border processing in background thread
        CN: 在后台线程中执行边框处理
        """
        try:
            from apps.border_tool import process_border_batch
            
            result = process_border_batch(
                self.input_dir,
                self.output_dir,
                self.is_digital,
                self.manual_film,
                progress_callback=self.report_progress
            )
            self.finished.emit(result)
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def report_progress(self, current, total, filename):
        """
        EN: Report progress to main thread
        CN: 向主线程报告进度
        """
        self.progress.emit(current, total, filename)


class BorderPanel(QWidget):
    """
    EN: Border Tool GUI panel
    CN: 边框工具图形界面面板
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.film_list = []
        self.setup_ui()
        self.load_film_library()
    
    def setup_ui(self):
        """
        EN: Setup user interface
        CN: 设置用户界面
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # EN: Mode selection group / CN: 模式选择组
        mode_group = QGroupBox("工作模式 Working Mode")
        mode_layout = QHBoxLayout()
        
        self.radio_film = QRadioButton("胶片项目 Film")
        self.radio_digital = QRadioButton("数码项目 Digital")
        self.radio_film.setChecked(True)
        self.radio_film.toggled.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.radio_film)
        mode_layout.addWidget(self.radio_digital)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # EN: Input folder selection / CN: 输入文件夹选择
        folder_group = QGroupBox("输入文件夹 Input Folder")
        folder_layout = QVBoxLayout()
        
        folder_select_layout = QHBoxLayout()
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setPlaceholderText("选择包含照片的文件夹 Select folder with photos")
        self.input_folder_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("浏览 Browse")
        self.browse_button.clicked.connect(self.select_input_folder)
        
        folder_select_layout.addWidget(self.input_folder_edit)
        folder_select_layout.addWidget(self.browse_button)
        
        self.file_count_label = QLabel("未选择文件夹 No folder selected")
        self.file_count_label.setStyleSheet("color: #888888;")
        
        folder_layout.addLayout(folder_select_layout)
        folder_layout.addWidget(self.file_count_label)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # EN: Film selection group (only for film mode) / CN: 胶片选择组（仅胶片模式）
        self.film_group = QGroupBox("胶片选择 Film Selection")
        film_layout = QVBoxLayout()
        
        self.auto_detect_check = QCheckBox("自动识别胶片（从EXIF）Auto Detect from EXIF")
        self.auto_detect_check.setChecked(True)
        self.auto_detect_check.toggled.connect(self.on_auto_detect_changed)
        
        film_select_layout = QHBoxLayout()
        film_select_layout.addWidget(QLabel("手动选择 Manual Select:"))
        self.film_combo = QComboBox()
        self.film_combo.setEnabled(False)
        film_select_layout.addWidget(self.film_combo, 1)
        
        film_layout.addWidget(self.auto_detect_check)
        film_layout.addLayout(film_select_layout)
        self.film_group.setLayout(film_layout)
        layout.addWidget(self.film_group)
        
        # EN: Process button and progress / CN: 处理按钮和进度
        self.process_button = QPushButton("开始处理 Start Processing")
        self.process_button.clicked.connect(self.start_processing)
        self.process_button.setMinimumHeight(40)
        layout.addWidget(self.process_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # EN: Log output / CN: 日志输出
        log_group = QGroupBox("处理日志 Processing Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setPlaceholderText("处理日志将显示在这里 Processing logs will appear here")
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        # EN: Auto-detect photos_in folder / CN: 自动检测 photos_in 文件夹
        self.auto_detect_photos_in()
    
    def load_film_library(self):
        """
        EN: Load film library from config
        CN: 从配置文件加载胶片库
        """
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            config_path = os.path.join(base_path, 'config', 'films.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                films_data = json.load(f)
            
            # EN: Extract all film names / CN: 提取所有胶片名称
            self.film_list = []
            for brand, films in films_data.items():
                for film_name in films.keys():
                    display_name = f"{brand} {film_name}"
                    self.film_list.append((display_name, film_name))
            
            # EN: Sort and populate combo box / CN: 排序并填充下拉框
            self.film_list.sort()
            self.film_combo.addItem("-- 请选择胶片 Select Film --", None)
            for display_name, film_name in self.film_list:
                self.film_combo.addItem(display_name, film_name)
            
            self.log(f"EN: Loaded {len(self.film_list)} films | CN: 已加载 {len(self.film_list)} 种胶片")
        except Exception as e:
            self.log(f"EN: Failed to load film library: {e} | CN: 胶片库加载失败: {e}")
    
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
                self.input_folder_edit.setText(photos_in)
                self.update_file_count()
        except Exception:
            pass
    
    def select_input_folder(self):
        """
        EN: Open folder selection dialog
        CN: 打开文件夹选择对话框
        """
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输入文件夹 Select Input Folder",
            self.input_folder_edit.text() or os.path.expanduser("~")
        )
        if folder:
            self.input_folder_edit.setText(folder)
            self.update_file_count()
    
    def update_file_count(self):
        """
        EN: Update file count display
        CN: 更新文件数量显示
        """
        folder = self.input_folder_edit.text()
        if not folder or not os.path.exists(folder):
            self.file_count_label.setText("未选择文件夹 No folder selected")
            self.file_count_label.setStyleSheet("color: #888888;")
            return
        
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            count = len(files)
            if count > 0:
                self.file_count_label.setText(f"✓ 找到 {count} 张照片 Found {count} photos")
                self.file_count_label.setStyleSheet("color: #27AE60;")
            else:
                self.file_count_label.setText("⚠ 文件夹中没有图片 No images in folder")
                self.file_count_label.setStyleSheet("color: #E74C3C;")
        except Exception as e:
            self.file_count_label.setText(f"错误 Error: {e}")
            self.file_count_label.setStyleSheet("color: #E74C3C;")
    
    def on_mode_changed(self):
        """
        EN: Handle mode change
        CN: 处理模式切换
        """
        is_film = self.radio_film.isChecked()
        self.film_group.setVisible(is_film)
    
    def on_auto_detect_changed(self):
        """
        EN: Handle auto-detect toggle
        CN: 处理自动检测切换
        """
        auto = self.auto_detect_check.isChecked()
        self.film_combo.setEnabled(not auto)
    
    def start_processing(self):
        """
        EN: Start border processing
        CN: 开始边框处理
        """
        # EN: Validate inputs / CN: 验证输入
        input_folder = self.input_folder_edit.text()
        if not input_folder or not os.path.exists(input_folder):
            QMessageBox.warning(self, "警告 Warning", "请先选择输入文件夹 Please select input folder")
            return
        
        # EN: Check if files exist / CN: 检查是否有文件
        files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not files:
            QMessageBox.warning(self, "警告 Warning", "输入文件夹中没有图片 No images in input folder")
            return
        
        # EN: Get manual film selection if not auto-detect / CN: 如果不自动检测则获取手动选择
        manual_film = None
        if self.radio_film.isChecked() and not self.auto_detect_check.isChecked():
            if self.film_combo.currentIndex() == 0:
                QMessageBox.warning(self, "警告 Warning", "请选择胶片类型 Please select film type")
                return
            manual_film = self.film_combo.currentData()
        
        # EN: Setup output folder / CN: 设置输出文件夹
        if getattr(sys, 'frozen', False):
            working_dir = os.path.dirname(sys.executable)
        else:
            working_dir = os.getcwd()
        output_folder = os.path.join(working_dir, "photos_out")
        os.makedirs(output_folder, exist_ok=True)
        
        # EN: Clear log and show progress / CN: 清空日志并显示进度
        self.log_text.clear()
        self.log("EN: Starting processing... | CN: 开始处理...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_button.setEnabled(False)
        
        # EN: Start worker thread / CN: 启动工作线程
        is_digital = self.radio_digital.isChecked()
        self.worker = BorderWorker(input_folder, output_folder, is_digital, manual_film)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, current, total, filename):
        """
        EN: Handle progress update
        CN: 处理进度更新
        """
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.log(f"[{current}/{total}] {filename}")
    
    def on_finished(self, result):
        """
        EN: Handle processing completion
        CN: 处理完成回调
        """
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        
        if result.get('success'):
            self.log("\n✓ " + "="*50)
            self.log(f"✓ EN: Processing complete! | CN: 处理完成！")
            self.log(f"✓ EN: Processed {result.get('processed', 0)} photos | CN: 已处理 {result.get('processed', 0)} 张照片")
            self.log("✓ " + "="*50)
            
            QMessageBox.information(
                self,
                "完成 Complete",
                f"处理完成！\nProcessing complete!\n\n已处理 {result.get('processed', 0)} 张照片\nProcessed {result.get('processed', 0)} photos"
            )
        else:
            self.log(f"\n✗ EN: Processing failed | CN: 处理失败")
            self.log(f"✗ {result.get('message', 'Unknown error')}")
            
            QMessageBox.critical(self, "错误 Error", result.get('message', 'Unknown error'))
    
    def on_error(self, error_msg):
        """
        EN: Handle processing error
        CN: 处理错误回调
        """
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        
        self.log(f"\n✗ EN: Error occurred | CN: 发生错误\n{error_msg}")
        
        QMessageBox.critical(
            self,
            "错误 Error",
            f"处理过程中发生错误 Error during processing:\n\n{error_msg}\n\n如需帮助请联系 For help contact: xjames007@gmail.com"
        )
    
    def log(self, message):
        """
        EN: Append message to log
        CN: 添加消息到日志
        """
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
