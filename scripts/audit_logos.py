import os

logo_dir = r"d:\Projects\GT23_Workflow\GT23_Assets\logos"
if not os.path.exists(logo_dir):
    print("Logo directory not found!")
    exit(1)

files = os.listdir(logo_dir)
logos = [f for f in files if f.lower().endswith(('.png', '.svg'))]
brands = {}

for f in logos:
    parts = f.split('-', 1)
    if len(parts) > 1:
        brand = parts[0].upper()
        model = os.path.splitext(parts[1])[0]
    else:
        brand = "OTHER"
        model = os.path.splitext(f)[0]
    
    if brand not in brands:
        brands[brand] = []
    brands[brand].append(model)

merged_brands = {}
for b, m in brands.items():
    norm_b = b.upper()
    if norm_b not in merged_brands:
        merged_brands[norm_b] = []
    merged_brands[norm_b].extend(m)

with open(r"d:\Projects\GT23_Workflow\scripts\logo_audit_results.txt", "w", encoding="utf-8") as out:
    for b in sorted(merged_brands.keys()):
        models = sorted(set(merged_brands[b]))
        line = f"**{b}**\n> {', '.join(models)}\n"
        print(line, end="")
        out.write(line + "\n")
