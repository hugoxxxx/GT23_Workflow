# pre_release_check.py
"""
EN: Pre-release validation script for GT23 Film Workflow
CN: GT23 胶片工作流发布前验证脚本
"""

import os
import sys

def check_required_files():
    """Check if all required files exist"""
    print("\n=== 检查必需文件 / Checking Required Files ===")
    required = [
        "main.py",
        "main_cli.py",
        "requirements.txt",
        "requirements-gui.txt",
        "build.spec",
        "README.md",
        "config/films.json",
        "config/layouts.json",
        "config/contact_layouts.json",
    ]
    
    missing = []
    for file in required:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - 缺失!")
            missing.append(file)
    
    return len(missing) == 0

def check_config_files():
    """Validate JSON config files"""
    print("\n=== 检查配置文件 / Checking Config Files ===")
    import json
    
    configs = [
        "config/films.json",
        "config/layouts.json",
        "config/contact_layouts.json",
    ]
    
    all_valid = True
    for config_file in configs:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"  ✓ {config_file} - 格式正确")
        except Exception as e:
            print(f"  ✗ {config_file} - 错误: {e}")
            all_valid = False
    
    return all_valid

def check_imports():
    """Check if all required packages can be imported"""
    print("\n=== 检查依赖包 / Checking Dependencies ===")
    
    required_packages = [
        ("PIL", "Pillow"),
        ("exifread", "ExifRead"),
        ("fonttools", "fonttools"),
        ("numpy", "numpy"),
        ("ttkbootstrap", "ttkbootstrap"),
        ("svgwrite", "svgwrite"),
    ]
    
    all_ok = True
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            print(f"  ✗ {package_name} - 未安装!")
            all_ok = False
    
    # Cairo check (Windows specific)
    try:
        from cairosvg import svg2png
        print(f"  ✓ CairoSVG (含 Cairo DLL)")
    except Exception as e:
        print(f"  ⚠ CairoSVG - 警告: {str(e)[:50]}...")
        print(f"     (仅135画幅需要，其他画幅可正常使用)")
    
    return all_ok

def check_assets():
    """Check if asset files exist"""
    print("\n=== 检查资源文件 / Checking Assets ===")
    
    asset_dirs = ["assets/fonts", "assets/samples"]
    all_exist = True
    
    for dir_path in asset_dirs:
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"  ✓ {dir_path} ({len(files)} 文件)")
        else:
            print(f"  ✗ {dir_path} - 目录不存在!")
            all_exist = False
    
    return all_exist

def check_version_consistency():
    """Check if version numbers are consistent"""
    print("\n=== 检查版本一致性 / Checking Version Consistency ===")
    
    try:
        # Read version from version.py if it exists
        if os.path.exists("version.py"):
            with open("version.py", 'r', encoding='utf-8') as f:
                content = f.read()
                if '__version__' in content:
                    print(f"  ✓ version.py 存在")
                else:
                    print(f"  ⚠ version.py 缺少 __version__")
        else:
            print(f"  ⚠ version.py 不存在（建议创建）")
        
        # Check main.py title
        with open("main.py", 'r', encoding='utf-8') as f:
            if "v2.0.0" in f.read() or "Film Workflow" in f.read():
                print(f"  ✓ main.py 包含版本信息")
        
        return True
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

def main():
    """Main validation routine"""
    print("\n" + "="*60)
    print("  GT23 Film Workflow - 发布前检查")
    print("  Pre-Release Validation")
    print("="*60)
    
    checks = [
        ("必需文件", check_required_files),
        ("配置文件", check_config_files),
        ("依赖包", check_imports),
        ("资源文件", check_assets),
        ("版本信息", check_version_consistency),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n检查 {name} 时出错: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("检查总结 / Summary")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("\n✓ 所有检查通过！可以发布。")
        print("✓ All checks passed! Ready for release.\n")
        return 0
    else:
        print("\n✗ 部分检查未通过，请修复后再发布。")
        print("✗ Some checks failed. Please fix before release.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
