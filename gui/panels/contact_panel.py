# gui/panels/contact_panel.py
"""
EN: Contact Sheet panel for GUI
CN: 底片索引 GUI 面板
"""

import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QLineEdit, QPushButton, QComboBox,
                               QTextEdit, QFileDialog, QProgressBar,
                               QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal


class ContactWorker(QThread):
    """
    EN: Worker thread for contact sheet generation
    CN: 底片索引生成工作线程
    """
    progress = Signal(str)  # status message
    finished = Signal(dict)  # result dictionary
    error = Signal(str)  # error message
    
    def __init__(self, input_dir, output_dir, format_type, manual_film, emulsion):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.format_type = format_type
        self.manual_film = manual_film
        self.emulsion = emulsion
    
    def run(self):
        """
        EN: Execute contact sheet generation
        CN: 执行底片索引生成
        """
        try:
            from apps.contact_sheet import ContactSheetPro
            
            app = ContactSheetPro()
            result = app.generate(
                self.input_dir,
                self.output_dir,
                self.format_type,
                self.manual_film,
                self.emulsion,
                progress_callback=self.report_progress
            )
            self.finished.emit(result)
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def report_progress(self, message):
        """
        EN: Report progress message
        CN: 报告进度消息
        """
        self.progress.emit(message)


class ContactPanel(QWidget):
    """
    EN: Contact Sheet GUI panel
    CN: 底片索引图形界面面板
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """
        EN: Setup user interface
        CN: 设置用户界面
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
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
        
        # EN: Format selection / CN: 画幅选择
        format_group = QGroupBox("画幅选择 Format Selection")
        format_layout = QHBoxLayout()
        
        format_layout.addWidget(QLabel("画幅 Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("自动检测 Auto Detect", None)
        self.format_combo.addItem("135 (35mm Full Frame)", "135")
        self.format_combo.addItem("645 (6x4.5cm)", "645")
        self.format_combo.addItem("66 (6x6cm)", "66")
        self.format_combo.addItem("67 (6x7cm)", "67")
        format_layout.addWidget(self.format_combo, 1)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # EN: Film information / CN: 胶片信息
        info_group = QGroupBox("胶片信息 Film Information (可选 Optional)")
        info_layout = QVBoxLayout()
        
        film_layout = QHBoxLayout()
        film_layout.addWidget(QLabel("胶片 Film:"))
        self.film_edit = QLineEdit()
        self.film_edit.setPlaceholderText("留空自动识别 Leave empty for auto-detect (e.g. Portra 400)")
        film_layout.addWidget(self.film_edit)
        info_layout.addLayout(film_layout)
        
        emulsion_layout = QHBoxLayout()
        emulsion_layout.addWidget(QLabel("乳剂号 Emulsion:"))
        self.emulsion_edit = QLineEdit()
        self.emulsion_edit.setPlaceholderText("例如 e.g. 2024-01 or leave empty")
        emulsion_layout.addWidget(self.emulsion_edit)
        info_layout.addLayout(emulsion_layout)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # EN: Process button / CN: 处理按钮
        self.process_button = QPushButton("生成索引页 Generate Contact Sheet")
        self.process_button.clicked.connect(self.start_generation)
        self.process_button.setMinimumHeight(40)
        layout.addWidget(self.process_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
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
    
    def start_generation(self):
        """
        EN: Start contact sheet generation
        CN: 开始生成底片索引
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
        
        # EN: Get parameters / CN: 获取参数
        format_type = self.format_combo.currentData()
        manual_film = self.film_edit.text().strip() or None
        emulsion = self.emulsion_edit.text().strip() or None
        
        # EN: Setup output folder / CN: 设置输出文件夹
        if getattr(sys, 'frozen', False):
            working_dir = os.path.dirname(sys.executable)
        else:
            working_dir = os.getcwd()
        output_folder = os.path.join(working_dir, "photos_out")
        os.makedirs(output_folder, exist_ok=True)
        
        # EN: Clear log and show progress / CN: 清空日志并显示进度
        self.log_text.clear()
        self.log("EN: Starting generation... | CN: 开始生成...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.process_button.setEnabled(False)
        
        # EN: Start worker thread / CN: 启动工作线程
        self.worker = ContactWorker(input_folder, output_folder, format_type, manual_film, emulsion)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_progress(self, message):
        """
        EN: Handle progress message
        CN: 处理进度消息
        """
        self.log(message)
    
    def on_finished(self, result):
        """
        EN: Handle generation completion
        CN: 生成完成回调
        """
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        
        if result.get('success'):
            self.log("\n✓ " + "="*50)
            self.log(f"✓ EN: Contact sheet generated! | CN: 索引页生成完成！")
            self.log(f"✓ EN: Output: {result.get('output_path', '')} | CN: 输出: {result.get('output_path', '')}")
            self.log(f"✓ EN: Layout: {result.get('layout_detected', '')} | CN: 画幅: {result.get('layout_detected', '')}")
            self.log(f"✓ EN: Frames: {result.get('frames_count', 0)} | CN: 张数: {result.get('frames_count', 0)}")
            self.log("✓ " + "="*50)
            
            QMessageBox.information(
                self,
                "完成 Complete",
                f"索引页生成完成！\nContact sheet generated!\n\n输出文件 Output:\n{result.get('output_path', '')}"
            )
        else:
            self.log(f"\n✗ EN: Generation failed | CN: 生成失败")
            self.log(f"✗ {result.get('message', 'Unknown error')}")
            
            QMessageBox.critical(self, "错误 Error", result.get('message', 'Unknown error'))
    
    def on_error(self, error_msg):
        """
        EN: Handle generation error
        CN: 生成错误回调
        """
        self.progress_bar.setVisible(False)
        self.process_button.setEnabled(True)
        
        self.log(f"\n✗ EN: Error occurred | CN: 发生错误\n{error_msg}")
        
        QMessageBox.critical(
            self,
            "错误 Error",
            f"生成过程中发生错误 Error during generation:\n\n{error_msg}\n\n如需帮助请联系 For help contact: xjames007@gmail.com"
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
