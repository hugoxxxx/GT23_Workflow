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
    """EN: Download ZIP from GitHub/Gitee with fallback. / CN: 从 GitHub/Gitee 下载 ZIP 包更新（带自动回退）"""
    primary = remote_name or config_manager.get("preferred_sync_source", "gitee")
    
    # EN: Define sources / CN: 定义同步源
    sources = {
        "gitee": {
            "api": "https://gitee.com/api/v5/repos/hugoxxxx/GT23_Assets/branches/main",
            "zip": "https://gitee.com/hugoxxxx/GT23_Assets/repository/archive/main.zip"
        },
        "github": {
            "api": "https://api.github.com/repos/hugoxxxx/GT23_Assets/branches/main",
            "zip": "https://github.com/hugoxxxx/GT23_Assets/archive/refs/heads/main.zip"
        }
    }
    
    # EN: Determine order / CN: 确定重试顺序
    ordered_keys = [primary, "github" if primary == "gitee" else "gitee"]
    
    last_error = ""
    for source_key in ordered_keys:
        cfg = sources[source_key]
        try:
            # 1. EN: Check for incremental necessity / CN: 增量检测
            remote_hash = None
            try:
                headers = {'User-Agent': 'GT23-Workflow-Client'}
                api_res = requests.get(cfg["api"], timeout=5, headers=headers)
                if api_res.status_code == 200:
                    data = api_res.json()
                    remote_hash = data.get("commit", {}).get("sha")
            except Exception:
                pass
            
            last_hash = config_manager.get(f"last_asset_hash_{source_key}")
            if remote_hash and last_hash == remote_hash:
                return True, "EN: Already up to date.\nCN: 资源已是最新，无需更新。"
            
            # 2. EN: Download and Validate / CN: 下载并校验
            res = requests.get(cfg["zip"], timeout=20)
            res.raise_for_status()
            
            # EN: CRITICAL: Check ZIP signature / CN: 关键：检查 ZIP 签名 (PK\x03\x04)
            if not res.content.startswith(b'PK\x03\x04'):
                raise ValueError("Downloaded data is not a valid ZIP file (Might be HTML).")
            
            # 3. EN: Extract / CN: 解压
            # EN: Determine real target base (next to EXE or custom path)
            # CN: 确定真实的解压根目录（EXE 旁或自定义路径）
            custom_path = config_manager.get("custom_asset_path")
            if custom_path and os.path.exists(custom_path):
                target_base = custom_path
            else:
                if getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                    target_base = os.path.join(exe_dir, "GT23_Assets")
                else:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    target_base = os.path.join(base_dir, "GT23_Assets")
            
            os.makedirs(target_base, exist_ok=True)
            
            updated_logos = []
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                # GitHub/Gitee ZIPs usually have a single root folder like 'GT23_Assets-main'
                namelist = z.namelist()
                if not namelist: raise ValueError("Empty ZIP file.")
                root_in_zip = namelist[0].split('/')[0]
                
                for member in z.infolist():
                    if member.filename.startswith(root_in_zip + '/'):
                        member.filename = member.filename[len(root_in_zip)+1:]
                        if not member.filename: continue
                        
                        # EN: Extract relevant asset folders / CN: 仅解压相关资源文件夹
                        if member.filename.startswith(("logos/", "films/", "config/")):
                            # Track logo changes for UI feedback
                            if "logos/" in member.filename and (member.filename.endswith(".svg") or member.filename.endswith(".png")):
                                logo_name = os.path.basename(member.filename)
                                if logo_name: updated_logos.append(logo_name)
                                
                            z.extract(member, target_base)
            
            if remote_hash:
                config_manager.set(f"last_asset_hash_{source_key}", remote_hash)
            
            detail = f"\nUpdated: {', '.join(updated_logos[:10])}{'...' if len(updated_logos) > 10 else ''}" if updated_logos else ""
            return True, f"EN: Assets synced via {source_key.capitalize()}!{detail}\nCN: 资源已通过 {source_key.capitalize()} 同步成功！{detail}"
            
        except Exception as e:
            last_error = str(e)
            continue # Try next source
            
    return False, f"EN: Web Sync Failed (Checked all sources): {last_error}\nCN: 网络同步失败（已尝试所有源）: {last_error}"
