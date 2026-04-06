import os
import sys
import numpy as np
import colorsys
from PIL import Image, ImageDraw, ImageFont

# Add project root to path for core imports
sys.path.append(os.getcwd())

from core.renderer import FilmRenderer

def extract_dominant_colors(img, num_colors=4):
    """EN: Extract top N dominant and diverse colors using quantization.
       CN: 使用聚类量子化提取排名前 N 的主导且多样化的色彩。"""
       
    # 1. Resize and Quantize / 缩放并进行色彩聚类
    thumb = img.resize((150, 150), Image.Resampling.LANCZOS)
    # Quantize to 16 colors to have enough diversity / 聚类到 16 色以保证多样性
    quantized = thumb.quantize(colors=16, method=Image.Quantize.MAXCOVERAGE)
    palette = quantized.getpalette()[:48] # 16 colors * 3 (RGB)
    
    # Extract RGB clusters
    clusters = []
    for i in range(16):
        r, g, b = palette[i*3 : i*3+3]
        clusters.append((r, g, b))
        
    # Get pixel counts for each cluster
    counts = np.bincount(np.array(quantized).flatten(), minlength=16)
    
    # 2. Score Clusters / 为聚类评分
    scored_clusters = []
    for i, (r, g, b) in enumerate(clusters):
        count = counts[i]
        # Normalize to 0-1
        rn, gn, bn = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
        
        # EN: Aesthetic Score: Weight by count and saturation
        # CN: 审美得分：结合像素占比与饱和度，防止背景灰过度主导
        # Boost saturation importance for better "icons"
        score = count * (s + 0.1) 
        
        # Filter out extreme near-white or near-black
        if l > 0.95 or l < 0.05: score *= 0.1
        
        scored_clusters.append({
            'rgb': (r, g, b),
            'hls': (h, l, s),
            'score': score
        })
        
    # Sort by score descending
    scored_clusters.sort(key=lambda x: x['score'], reverse=True)
    
    # 3. Diverse Selection / 多样化筛选
    final_palette = []
    selected_hues = []
    
    for c in scored_clusters:
        h, l, s = c['hls']
        
        # Diversity check (hue distance)
        is_diverse = True
        for sh in selected_hues:
            # Hue distance handles wrap-around at 1.0/0.0
            diff = abs(h - sh)
            if diff > 0.5: diff = 1.0 - diff
            if diff < 0.12: # Too close in hue
                is_diverse = False
                break
        
        if is_diverse or len(final_palette) == 0:
            # EN: Translucent High-Key Post-processing (v10)
            # CN: 极简高透方案 (v10)：提升明度与“透明感”，打造马卡龙般的通透色
            
            # 1. EN: Soft Damped Saturation / CN: 柔和饱和度（实现“透明感”）
            # Lower saturation floor and multiplier
            s_muted = max(min(s * 0.75, 0.50), 0.25)
            
            # 2. EN: High-Key Lightness Mapping / CN: 高亮明度映射 (锁定在 0.7 - 0.92 之间)
            # This makes all colors look like airy tints
            l_high = 0.70 + (l * 0.22)
            
            r_new, g_new, b_new = colorsys.hls_to_rgb(h, l_high, s_muted)
            final_palette.append((int(r_new*255), int(g_new*255), int(b_new*255)))
            selected_hues.append(h)
            
        if len(final_palette) >= num_colors:
            break
            
    # If not enough, fill with neutral
    while len(final_palette) < num_colors:
        final_palette.append((128, 128, 128))
    
    # EN: Sort by Luminance for visual order on board
    # CN: 按明度排序，使标签排列更美观
    final_palette.sort(key=lambda rgb: colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)[1])
    
    return final_palette

def gen_palette_sample():
    renderer = FilmRenderer()
    
    img_path = "photos_in/20260213-17-11-00.jpg"
    if not os.path.exists(img_path):
        print(f"ERROR: {img_path} not found")
        return

    # Load original image
    raw_img = Image.open(img_path)
    from PIL import ImageOps
    raw_img = ImageOps.exif_transpose(raw_img)
    if raw_img.mode != "RGB": raw_img = raw_img.convert("RGB")
    
    long_edge = 2000
    w, h = raw_img.size
    if w > h:
        nw, nh = long_edge, int(h * long_edge / w)
    else:
        nh, nw = long_edge, int(w * long_edge / h)
    processed_img = raw_img.resize((nw, nh), Image.Resampling.LANCZOS)
    
    # 1. Extract Dominant (NOT Luminance Zone)
    colors = extract_dominant_colors(processed_img, 4)
    print(f"Extracted Dominant Colors: {colors}")
    
    # 2. Layout (Classic GT23 Layout)
    side_pad = int(nw * 0.05)
    top_pad = int(nw * 0.05)
    bottom_splice = int(nh * 0.15)
    
    total_w = nw + side_pad * 2
    total_h = nh + top_pad + side_pad + bottom_splice
    
    canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    canvas.paste(processed_img, (side_pad, top_pad))
    
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([side_pad, top_pad, side_pad + nw, top_pad + nh], outline=(238, 238, 238), width=1)
    
    chip_size = int(side_pad * 0.45)
    spacing = int(chip_size * 0.4)
    start_x = side_pad
    center_y = top_pad + nh + (side_pad + bottom_splice) // 2
    chip_y = center_y - chip_size // 2
    
    for i, color in enumerate(colors):
        x0 = start_x + (chip_size + spacing) * i
        y0 = chip_y
        x1 = x0 + chip_size
        y1 = y0 + chip_size
        draw.rounded_rectangle([x0, y0, x1, y1], radius=chip_size//4, fill=color)
        l_val = 0.299*color[0] + 0.587*color[1] + 0.114*color[2]
        if l_val > 220:
             draw.rounded_rectangle([x0, y0, x1, y1], radius=chip_size//4, outline=(200, 200, 200), width=1)

    # Text rendering...
    m_size = int(nw * 0.06); s_size = int(nw * 0.035)
    try:
        font_main = ImageFont.truetype("assets/fonts/palab.ttf", m_size)
        font_sub = ImageFont.truetype("assets/fonts/gara.ttf", s_size)
    except:
        font_main = font_sub = ImageFont.load_default()

    main_text = "LEICA M11"; sub_text = "SUMMILUX 35mm f/1.4 ASPH  |  1/500s f/4.0  |  KODAK GOLD 200"
    mw = draw.textbbox((0, 0), main_text, font=font_main)[2]
    draw.text(((total_w - mw) // 2, center_y - int(bottom_splice * 0.15)), main_text, fill=(26, 26, 26), font=font_main)
    sw = draw.textbbox((0, 0), sub_text, font=font_sub)[2]
    draw.text(((total_w - sw) // 2, center_y + int(bottom_splice * 0.28)), sub_text, fill=(85, 85, 85), font=font_sub)

    if not os.path.exists("photos_out_test"): os.makedirs("photos_out_test")
    canvas.save("photos_out_test/color_palette_test.jpg", quality=95)
    print("SUCCESS: photos_out_test/color_palette_test.jpg generated")

if __name__ == "__main__":
    gen_palette_sample()
