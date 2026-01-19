# utils/logger.py
"""
EN: Logging utility for GT23 Film Workflow
CN: GT23 胶片工作流日志工具
"""

import logging
import os
import sys
from datetime import datetime

def setup_logger(name="GT23", level=logging.INFO):
    """
    EN: Setup logger for the application
    CN: 为应用程序设置日志记录器
    
    Args:
        name: Logger name / 日志记录器名称
        level: Logging level / 日志级别
    
    Returns:
        logging.Logger: Configured logger / 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # EN: Prevent duplicate handlers / CN: 防止重复添加处理器
    if logger.handlers:
        return logger
    
    # EN: Console handler / CN: 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # EN: File handler (only in development) / CN: 文件处理器（仅开发环境）
    if not getattr(sys, 'frozen', False):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"gt23_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # EN: Console formatter / CN: 控制台格式化器
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

# EN: Convenience function / CN: 便捷函数
def get_logger(name=None):
    """Get or create logger / 获取或创建日志记录器"""
    return logging.getLogger(name or "GT23")
