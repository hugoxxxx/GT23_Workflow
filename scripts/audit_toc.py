import os
import ast

def audit_toc(toc_path):
    if not os.path.exists(toc_path):
        print(f"TOC file not found: {toc_path}")
        return

    with open(toc_path, 'r', encoding='utf-8') as f:
        # PYZ-00.toc and Analysis-00.toc are basicallyrepr() of Python lists of tuples
        content = f.read()
        try:
            # We skip the first few characters if it's a tuple start like (['path'], ...
            # Actually literal_eval is usually safe for PyInstaller TOCs if not too huge
            data = ast.literal_eval(content)
        except Exception as e:
            print(f"Error parsing TOC: {e}")
            return

    # Structure of Analysis-00.toc is (scripts, binaries, datas, ...)
    # data[12] is often where binaries are in modern PyInstaller versions, 
    # but let's just find the list of tuples like ('name', 'path', 'TYPE')
    
    all_items = []
    
    def find_items(obj):
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, tuple) and len(item) >= 3 and item[2] in ('BINARY', 'EXTENSION'):
                    all_items.append(item)
                elif isinstance(item, (list, tuple)):
                    find_items(item)
        elif isinstance(obj, tuple):
            for item in obj:
                find_items(item)

    find_items(data)
    
    results = []
    for name, path, kind in all_items:
        if os.path.exists(path):
            size = os.path.getsize(path) / (1024 * 1024)
            results.append((name, path, size))
    
    results.sort(key=lambda x: x[2], reverse=True)
    
    print(f"{'Name':<30} | {'Size (MB)':<10} | {'Path'}")
    print("-" * 80)
    for name, path, size in results[:30]:
        print(f"{name or 'N/A':<30} | {size:<10.2f} | {path}")

if __name__ == "__main__":
    audit_toc(r"d:\Projects\GT23_Workflow\build\build\Analysis-00.toc")
