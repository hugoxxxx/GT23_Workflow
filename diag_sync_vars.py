import os
import sys
import requests
# Add parent dir to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.config_manager import config_manager

def diag_sync_vars():
    GITEE_TOKEN = "e6310b92bf4609c5f55e09f78fe4415a"
    sources = [
        {"label": "Gitee (Main)", "api": f"https://gitee.com/api/v5/repos/hugoxuuuu/gt23_assets/branches/main?access_token={GITEE_TOKEN}", "key": "gitee_main"},
        {"label": "Gitee (Master)", "api": f"https://gitee.com/api/v5/repos/hugoxuuuu/gt23_assets/branches/master?access_token={GITEE_TOKEN}", "key": "gitee_master"},
        {"label": "GitHub (Main)", "api": "https://api.github.com/repos/hugoxxxx/GT23_Assets/branches/main", "key": "github_main"},
        {"label": "GitHub (Proxy)", "api": "https://api.github.com/repos/hugoxxxx/GT23_Assets/branches/main", "key": "github_proxy"}
    ]
    
    headers = {'User-Agent': 'GT23-Workflow-Client'}
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_base = os.path.join(base_dir, "GT23_Assets")
    logo_check_dir = os.path.join(target_base, "logos")
    assets_exist = os.path.exists(logo_check_dir) and (len(os.listdir(logo_check_dir)) > 0 if os.path.isdir(logo_check_dir) else False)
    
    print(f"Target Base: {target_base}")
    print(f"Logo Check Dir: {logo_check_dir}")
    print(f"Assets Exist physically: {assets_exist}")
    
    for src in sources:
        print(f"\nSource: {src['label']}")
        remote_hash = None
        try:
            res = requests.get(src["api"], timeout=5, headers=headers)
            print(f"  API Status: {res.status_code}")
            if res.status_code == 200:
                remote_hash = res.json().get("commit", {}).get("sha")
        except Exception as e:
            print(f"  API Error: {e}")
        
        last_hash = config_manager.get(f"last_asset_hash_{src['key']}")
        print(f"  Remote Hash: {remote_hash}")
        print(f"  Last Hash:   {last_hash}")
        
        would_skip = remote_hash and last_hash == remote_hash and assets_exist
        print(f"  Would Skip:  {would_skip}")

if __name__ == "__main__":
    diag_sync_vars()
