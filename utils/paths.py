# utils/paths.py
import os
import sys

def get_base_path():
    """
    EN: Get the base path for assets and configs. Detects PyInstaller environment.
    CN: 获取资源和配置的基础路径。检测 PyInstaller 环境（支持 _MEIPASS）。
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # Assuming run from workspace root or similar
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_asset_path(filename):
    """
    EN: Get absolute path for an asset file.
    CN: 获取资源文件的绝对路径。
    """
    return os.path.join(get_base_path(), 'assets', filename)

def get_config_path(filename):
    """
    EN: Get absolute path for a config file.
    CN: 获取配置文件的绝对路径。
    """
    return os.path.join(get_base_path(), 'config', filename)

def get_working_dir():
    """
    EN: Get the current working directory safely.
    CN: 安全获取当前工作目录。
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.getcwd()

def ensure_working_folders():
    """
    EN: Ensure standard input/output folders exist.
    CN: 确保标准的输入/输出文件夹存在。
    """
    working_dir = get_working_dir()
    photos_in = os.path.join(working_dir, 'photos_in')
    photos_out = os.path.join(working_dir, 'photos_out')
    os.makedirs(photos_in, exist_ok=True)
    os.makedirs(photos_out, exist_ok=True)
    return photos_in, photos_out
