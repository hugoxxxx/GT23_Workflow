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
                stdout = process.stdout.strip()
                if "Already up to date" in stdout or "已经是最新的" in stdout:
                    return True, "EN: Already up to date.\nCN: 资源已是最新，无需更新。"
                
                # EN: Extract file changes / CN: 提取文件变更
                changes = []
                for line in stdout.split('\n'):
                    if "logos/" in line and ("|" in line or "create mode" in line):
                        parts = line.split()
                        for p in parts:
                            if "logos/" in p:
                                changes.append(os.path.basename(p))
                
                detail = f"\nUpdated: {', '.join(changes)}" if changes else ""
                return True, f"EN: Synced via Git ({r_name}).{detail}\nCN: 已通过 Git 同步 ({r_name})。{detail}"
            last_error = process.stderr.strip()
        except Exception as e:
            last_error = str(e)
            
    return False, last_error

def _sync_via_web(remote_name=None):
    """EN: Download ZIP from GitHub/Gitee / CN: 从 GitHub/Gitee 下载 ZIP 包更新"""
    source = remote_name or config_manager.get("preferred_sync_source", "gitee")
    
    if source == "gitee":
        api_url = "https://gitee.com/api/v5/repos/hugoxuuuu/gt23_assets/branches/main"
        download_url = "https://gitee.com/hugoxuuuu/gt23_assets/repository/archive/main.zip"
    else:
        api_url = "https://api.github.com/repos/hugoxxxx/GT23_Assets/branches/main"
        download_url = "https://github.com/hugoxxxx/GT23_Assets/archive/refs/heads/main.zip"

    try:
        # 1. EN: Check for incremental necessity / CN: 增量逻辑：检查哈希是否变动
        remote_hash = None
        try:
            headers = {'User-Agent': 'GT23-Workflow-Client'}
            api_res = requests.get(api_url, timeout=10, headers=headers)
            if api_res.status_code == 200:
                data = api_res.json()
                # Gitee and GitHub structures differ slightly
                remote_hash = data.get("commit", {}).get("sha")
        except Exception:
            pass # EN: Fallback to full download if API fails / CN: API 报错则回退全量下载

        last_hash = config_manager.get(f"last_asset_hash_{source}")
        if remote_hash and last_hash == remote_hash:
            return True, "EN: Already up to date (Hash matched).\nCN: 资源已是最新，无需更新 (已校验哈希)。"

        # 2. EN: Proceed with download / CN: 执行下载
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Target: custom_path if set, else GT23_Assets in project root
        custom_path = config_manager.get("custom_asset_path")
        target_dir = custom_path if custom_path and os.path.exists(custom_path) else os.path.join(base_dir, "GT23_Assets")
        
        os.makedirs(target_dir, exist_ok=True)
        
        updated_logos = []
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # zip usually contains a root folder like 'gt23_assets-main'
            root_in_zip = z.namelist()[0].split('/')[0]
            for member in z.infolist():
                if member.filename.startswith(root_in_zip + '/'):
                    # Remove the root folder prefix
                    old_filename = member.filename
                    member.filename = member.filename[len(root_in_zip)+1:]
                    if not member.filename: continue
                    
                    # Track logo changes
                    if "logos/" in member.filename and (member.filename.endswith(".svg") or member.filename.endswith(".png")):
                        logo_name = os.path.basename(member.filename)
                        if logo_name: updated_logos.append(logo_name)
                        
                    z.extract(member, target_dir)
        
        # 3. EN: Save hash after success / CN: 成功后保存哈希
        if remote_hash:
            config_manager.set(f"last_asset_hash_{source}", remote_hash)
            
        detail = f"\nUpdated: {', '.join(updated_logos[:10])}{'...' if len(updated_logos) > 10 else ''}" if updated_logos else ""
        return True, f"EN: Assets updated via Web ({source})!{detail}\nCN: 边框资源已通过网络完全更新 ({source})！{detail}"
    except Exception as e:
        return False, f"EN: Web Sync Failed: {str(e)}\nCN: 网络同步失败: {str(e)}"
