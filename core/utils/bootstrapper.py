import os
import sys
from utils.config_manager import config_manager

def bootstrap_fonts(resolver_func=None):
    """
    EN: Setup external font directory if running as EXE.
    CN: 引导程序：如果作为 EXE 运行，设置外部 Font 目录并释放默认资源。
    """
    # 0. EN: Try User-Defined Path first / CN: 极高优先级：尝试用户自定义路径
    custom_path = config_manager.get("custom_asset_path")
    if custom_path and os.path.exists(custom_path):
        font_sub = os.path.join(custom_path, "fonts")
        if os.path.exists(font_sub): return font_sub
        return custom_path

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    decoupled_path = os.path.join(base_dir, "GT23_Assets", "fonts")
    
    # 1. EN: Try decoupled Assets Repo (Priority) / CN: 优先尝试解耦的资产仓库
    if os.path.exists(decoupled_path) and os.path.isdir(decoupled_path):
        internal_font_path = decoupled_path
    elif resolver_func:
        # 2. EN: Use provided resolver / CN: 使用提供的路径解析函数
        internal_font_path = resolver_func("assets/fonts")
    else:
        # 3. EN: Fallback resolver for early bootstrap
        if hasattr(sys, '_MEIPASS'):
            internal_font_path = os.path.join(sys._MEIPASS, "assets/fonts")
        else:
            internal_font_path = os.path.join(base_dir, "assets", "fonts")
    
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        external_font_path = os.path.join(exe_dir, "GT23_Assets", "fonts")
        
        if not os.path.exists(external_font_path):
            try:
                import shutil
                os.makedirs(os.path.dirname(external_font_path), exist_ok=True)
                shutil.copytree(internal_font_path, external_font_path)
            except Exception as e:
                print(f"CN: [!] 无法释放字体资源: {e}")
        return external_font_path
    else:
        return internal_font_path

def bootstrap_logos(resolver_func=None):
    """
    EN: Setup external logo directory if running as EXE.
    CN: 引导程序：如果作为 EXE 运行，设置外部 Logo 目录并释放默认资源。
    """
    # 0. EN: Try User-Defined Path first / CN: 极高优先级：尝试用户自定义路径
    custom_path = config_manager.get("custom_asset_path")
    if custom_path and os.path.exists(custom_path):
        logo_sub = os.path.join(custom_path, "logos")
        if os.path.exists(logo_sub): return logo_sub
        return custom_path

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    decoupled_path = os.path.join(base_dir, "GT23_Assets", "logos")
    
    # 1. EN: Try decoupled Assets Repo (Priority) / CN: 优先尝试解耦的资产仓库
    if os.path.exists(decoupled_path) and os.path.isdir(decoupled_path):
        internal_logo_path = decoupled_path
    elif resolver_func:
        # 2. EN: Use provided resolver / CN: 使用提供的路径解析函数
        internal_logo_path = resolver_func("assets/logo")
    else:
        if hasattr(sys, '_MEIPASS'):
            internal_logo_path = os.path.join(sys._MEIPASS, "assets/logo")
        else:
            internal_logo_path = os.path.join(base_dir, "assets", "logo")
    
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        external_logo_path = os.path.join(exe_dir, "GT23_Assets", "logos")
        if not os.path.exists(external_logo_path):
            try:
                import shutil
                os.makedirs(os.path.dirname(external_logo_path), exist_ok=True)
                shutil.copytree(internal_logo_path, external_logo_path)
            except Exception as e:
                print(f"CN: [!] 无法释放 Logo 资源: {e}")
        return external_logo_path
    else:
        return internal_logo_path
