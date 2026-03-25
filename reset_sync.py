import os
import shutil
import sys
from utils.config_manager import config_manager

def reset_sync():
    # 1. EN: Clear physical assets / CN: 清空本地资源文件夹
    base_dir = os.path.dirname(os.path.abspath(__file__))
    asset_dir = os.path.join(base_dir, "GT23_Assets")
    if os.path.exists(asset_dir):
        shutil.rmtree(asset_dir)
    os.makedirs(asset_dir)
    print(f"EN: Cleared {asset_dir}\nCN: 已清空 {asset_dir}")

    # 2. EN: Clear config hashes / CN: 清空配置文件里的同步记录
    has_changes = False
    keys_to_del = [k for k in config_manager.config.keys() if k.startswith("last_asset_hash_")]
    for key in keys_to_del:
        del config_manager.config[key]
        has_changes = True
    
    if has_changes:
        config_manager.save()
        print("EN: Cleared sync hashes from config.\nCN: 已从配置文件中清除同步记录。")
    else:
        print("EN: No sync hashes found in config.\nCN: 配置文件中没有同步记录。")

if __name__ == "__main__":
    reset_sync()
