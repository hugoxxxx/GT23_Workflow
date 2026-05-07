import os
from PIL import Image

def draw_png_text(text, font_dir, spacing_ratio=0.15, color=(255, 255, 255)):
    """
    EN: Render text using PNG characters with fully proportional layout.
    CN: 使用 PNG 字符进行渲染，支持全比例布局（间距与高度挂钩）。
    """
    descenders = set("gjpqy")
    
    # EN: 1. Get Reference Height / CN: 1. 获取参考高度
    ref_file = os.path.join(font_dir, "1050-0.png")
    ref_h = 40
    if os.path.exists(ref_file):
        with Image.open(ref_file) as ri:
            bbox = ri.getbbox()
            ref_h = bbox[3] - bbox[1] if bbox else ri.height
            
    # EN: Calculate Relative Spacing / CN: 计算相对间距
    spacing = int(ref_h * spacing_ratio)
    
    processed_items = []
    total_w = 0
    
    for char in text:
        if char == " ":
            w = int(ref_h * 0.5) # Space is 50% of height
            processed_items.append({"img": None, "type": "space", "w": w})
            total_w += w + spacing
            continue
            
        filename = None
        if char.isdigit(): filename = f"1050-{char}.png"
        elif char.isupper(): filename = f"1050-{char}-capital.png"
        elif char.islower(): filename = f"1050-{char.upper()}.png"
        elif char == "/": filename = "1050-U+002F.png"
        elif char == "|": filename = "1050-U+007C.png"
        elif char == ".": filename = "1050-U+002E.png"
        elif char == "*": filename = "1050-U+002A.png"
        
        path = os.path.join(font_dir, filename) if filename else None
        if path and os.path.exists(path):
            img = Image.open(path).convert('RGBA')
            
            # EN: Color Tint (preserving alpha)
            r, g, b, a = img.split()
            img = Image.merge("RGBA", (
                Image.new("L", img.size, color[0]),
                Image.new("L", img.size, color[1]),
                Image.new("L", img.size, color[2]),
                a
            ))
            
            # EN: Auto-Crop
            bbox = img.getbbox()
            if bbox: img = img.crop(bbox)
            
            char_type = "standard"
            if char in descenders: char_type = "descender"
            elif char.islower() and char not in "bdfhklit": char_type = "small"
            elif char in "*'\"": char_type = "superscript"
                
            processed_items.append({"img": img, "type": char_type, "w": img.width, "h": img.height})
            total_w += img.width + spacing
        else:
            processed_items.append({"img": None, "type": "missing", "w": 0})

    # EN: 2. Layout (Relative Ratios) / CN: 2. 布局（相对比例）
    canvas_h = int(ref_h * 1.5)
    baseline = int(ref_h * 1.2)
    result = Image.new('RGBA', (total_w, canvas_h), (0, 0, 0, 0))
    
    x_cursor = 0
    for item in processed_items:
        img = item.get("img")
        if img:
            t = item["type"]
            # EN: Specialized Vertical Alignment / CN: 特殊垂直对齐
            if t == "descender":
                y_pos = baseline - int(img.height * 0.75) 
            elif t == "superscript":
                # EN: Superscripts (like *) float near the top of Cap Height
                # CN: 上标（如 *）漂浮在大写高度的顶部
                y_pos = baseline - ref_h + int(ref_h * 0.05)
            else:
                y_pos = baseline - img.height
            
            result.paste(img, (x_cursor, y_pos), mask=img)
            x_cursor += item["w"] + spacing
        else:
            x_cursor += item.get("w", 0) + spacing
            
    return result

if __name__ == "__main__":
    FONT_PATH = r"D:\Projects\GT23_Workflow\assets\fonts\1050"
    THEME_ORANGE = (255, 120, 0) # Retro Date Back Orange
    
    # EN: Test 1: Full Character Set (White)
    TEST_ALL = [
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "abcdefghijklmnopqrstuvwxyz",
        "0123456789 / | ."
    ]
    
    print("EN: Rendering full character set with spacing_ratio=0.25...")
    strips = [draw_png_text(s, FONT_PATH, spacing_ratio=0.25, color=(255, 255, 255)) for s in TEST_ALL]
    
    max_w = max(s.width for s in strips)
    total_h = sum(s.height for s in strips) + 30
    full_sample = Image.new('RGBA', (max_w, total_h), (0, 0, 0, 255))
    y_off = 5
    for s in strips:
        full_sample.paste(s, (0, y_off), mask=s)
        y_off += s.height + 15
    full_sample.save("png_font_full_sample.png")

    # EN: Test 2: Complex Lens EXIF (Orange)
    # CN: 测试 2: 复杂镜头 EXIF (橙色)
    TEST_STR = "Zeiss Sonnar T* 150mm f/4 CF | f/4.0 1/250s ISO 100"
    combined = draw_png_text(TEST_STR, FONT_PATH, spacing_ratio=0.25, color=THEME_ORANGE)
    combined.save("png_font_test_complex.png")
    
    print("EN: Results saved with spacing_ratio=0.25 (T* Included)")
