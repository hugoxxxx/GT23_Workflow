import os
import sys

def resolve_path(path):
    """
    EN: Resolves a relative path to an absolute path, supporting both dev and PyInstaller environments.
    CN: 将相对路径解析为绝对路径，支持开发环境与 PyInstaller 打包环境。
    """
    if not path:
        return ""
    if os.path.isabs(path):
        return path
        
    if getattr(sys, 'frozen', False):
        # EN: Running in PyInstaller bundle / CN: 在 PyInstaller 打包环境下运行
        base_path = sys._MEIPASS
    else:
        # EN: Running in normal Python dev environment / CN: 在开发环境下运行
        # EN: We assume the project root is two levels up from core/utils/
        # CN: 假定项目根目录在 core/utils/ 的上两层
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(os.path.dirname(current_dir))
        
    return os.path.normpath(os.path.join(base_path, path))
