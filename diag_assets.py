import os
import sys

def diag():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Project root (diagnosed): {base_dir}")
    
    asset_dir = os.path.join(base_dir, "GT23_Assets")
    logo_dir = os.path.join(asset_dir, "logos")
    
    print(f"Asset directory: {asset_dir} (exists: {os.path.exists(asset_dir)})")
    print(f"Logo directory: {logo_dir} (exists: {os.path.exists(logo_dir)})")
    
    if os.path.exists(logo_dir):
        files = os.listdir(logo_dir)
        print(f"Number of files in logo_dir: {len(files)}")
        if len(files) > 0:
            print(f"First 5 files: {files[:5]}")
        
    # Check legacy paths too
    legacy_logo = os.path.join(base_dir, "assets", "logo")
    print(f"Legacy logo path: {legacy_logo} (exists: {os.path.exists(legacy_logo)})")
    if os.path.exists(legacy_logo):
        print(f"Files in legacy: {len(os.listdir(legacy_logo))}")

if __name__ == "__main__":
    diag()
