import os
import sys
import subprocess
import threading
import requests
import zipfile
import shutil
import io
from utils.config_manager import config_manager

def sync_assets_async(callback=None):
    """
    EN: Sync assets in a background thread to prevent GUI freezing.
    CN: 在后台线程同步资源，防止 GUI 卡死。
    """
    def worker():
        success, message = sync_assets()
        if callback:
            callback(success, message)
            
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

def sync_assets(remote_name=None):
    """
    EN: Update the GT23_Assets submodule to the latest remote state.
    CN: 更新 GT23_Assets 子模块到最新的远程状态。
    """
    # 1. EN: Try Git Sync first (for devs) / CN: 优先尝试 Git 同步 (开发者模式)
    if not getattr(sys, 'frozen', False):
        success, msg = _sync_via_git(remote_name)
        if success: return True, msg
    
    # 2. EN: Fallback to Web Sync (for users/portable) / CN: 回退至网络下载 (普通用户/EXE 模式)
    return _sync_via_web(remote_name)

def _sync_via_git(remote_name=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    asset_dir = os.path.join(base_dir, "GT23_Assets")
    
    if not os.path.exists(asset_dir):
        return False, "Git directory missing."

    remotes_to_try = [remote_name] if remote_name else ["gitee", "origin"]
    last_error = ""
    for r_name in remotes_to_try:
        try:
            cmd = ["git", "pull", r_name, "main"]
            process = subprocess.run(cmd, cwd=asset_dir, capture_output=True, text=True, shell=True if sys.platform == "win32" else False)
            if process.returncode == 0:
                return True, f"EN: Synced via Git ({r_name}).\nCN: 已通过 Git 同步 ({r_name})。"
            last_error = process.stderr.strip()
        except Exception as e:
            last_error = str(e)
            
    return False, last_error

def _sync_via_web(remote_name=None):
    """EN: Download ZIP from GitHub/Gitee / CN: 从 GitHub/Gitee 下载 ZIP 包更新"""
    source = remote_name or config_manager.get("preferred_sync_source", "gitee")
    
    if source == "gitee":
        url = "https://gitee.com/hugoxuuuu/gt23_assets/repository/archive/main.zip"
    else:
        url = "https://github.com/hugoxxxx/GT23_Assets/archive/refs/heads/main.zip"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Target: custom_path if set, else GT23_Assets in project root
        custom_path = config_manager.get("custom_asset_path")
        target_dir = custom_path if custom_path and os.path.exists(custom_path) else os.path.join(base_dir, "GT23_Assets")
        
        os.makedirs(target_dir, exist_ok=True)
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # zip usually contains a root folder like 'gt23_assets-main'
            root_in_zip = z.namelist()[0].split('/')[0]
            for member in z.infolist():
                if member.filename.startswith(root_in_zip + '/'):
                    # Remove the root folder prefix
                    member.filename = member.filename[len(root_in_zip)+1:]
                    if not member.filename: continue
                    z.extract(member, target_dir)
                    
        return True, f"EN: Assets updated via Web ({source})!\nCN: 边框资源已通过网络完全更新 ({source})！"
    except Exception as e:
        return False, f"EN: Web Sync Failed: {str(e)}\nCN: 网络同步失败: {str(e)}"
