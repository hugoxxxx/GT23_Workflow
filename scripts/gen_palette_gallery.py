import os
import sys
import numpy as np
import colorsys
from PIL import Image, ImageDraw, ImageFont

# Add project root to path for core imports
sys.path.append(os.getcwd())

from core.renderer import FilmRenderer

def extract_dominant_clusters(img):
    """Base clustering engine."""
    thumb = img.resize((150, 150), Image.Resampling.LANCZOS)
    quantized = thumb.quantize(colors=24, method=Image.Quantize.MAXCOVERAGE)
    palette = quantized.getpalette()[:72] # 24 colors
    counts = np.bincount(np.array(quantized).flatten(), minlength=24)
    
    clusters = []
    for i in range(24):
        r, g, b = palette[i*3 : i*3+3]
        rn, gn, bn = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(rn, gn, bn)
        clusters.append({
            'rgb': (r, g, b),
            'hls': (h, l, s),
            'count': counts[i]
        })
    return clusters

def apply_recipe(clusters, recipe_id):
    """Apply specific aesthetic logic to select and tune 4 colors."""
    
    # 0. EN: Calculate scores for each cluster / CN: 计算每个聚类的得分
    scored = []
    for c in clusters:
        h, l, s = c['hls']
        cnt = c['count']
        
        if recipe_id == "vibrant": score = cnt * (s**2 + 0.1)
        elif recipe_id == "muted": score = cnt * (1.1 - s)
        elif recipe_id == "airy": score = cnt * (l)
        elif recipe_id == "deep": score = cnt * (1.0 - l)
        elif recipe_id == "diverse": score = cnt * (s + 0.2)
        else: score = cnt * (s + 0.1)
            
        if l > 0.98 or l < 0.02: score = 0
        scored.append((score, c))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # 1. Selection & Tuning Strategy
    final = []
    selected_clusters = []
    
    if recipe_id == "monochrome":
        # EN: Pick the single best cluster and create variations
        # CN: 选择最强的主色，并制作同色系变化
        best_c = scored[0][1]
        h, l, s = best_c['hls']
        for i in range(4):
            # Vary L and S for monochrome feel
            l_out = 0.3 + (i * 0.18)
            s_out = max(0.2, s * (0.6 + i*0.1))
            r, g, b = colorsys.hls_to_rgb(h, l_out, s_out)
            final.append((int(r*255), int(g*255), int(b*255)))
        return final

    # General Selection with Diversity (for other recipes)
    hues = []
    for s_val, c in scored:
        h, l, s = c['hls']
        if s_val <= 0: continue
        
        # Diversity check
        is_diverse = True
        # For some recipes, we WANT diversity, for others we might be more relaxed
        div_threshold = 0.12 if recipe_id != "pastel" else 0.05
        
        for sh in hues:
            diff = abs(h - sh)
            if diff > 0.5: diff = 1.0 - diff
            if diff < div_threshold: is_diverse = False; break
            
        if is_diverse or len(selected_clusters) == 0:
            selected_clusters.append(c)
            hues.append(h)
        if len(selected_clusters) >= 4: break

    # 2. Tuning Logic for the 4 selected clusters
    for i, c in enumerate(selected_clusters):
        h, l, s = c['hls']
        
        if recipe_id == "vibrant":
            s_out, l_out = max(s * 1.5, 0.70), max(l, 0.45)
        elif recipe_id == "muted":
            s_out, l_out = max(s * 0.75, 0.28), l
        elif recipe_id == "airy":
            s_out, l_out = max(s * 0.6, 0.25), 0.75 + (l * 0.15)
        elif recipe_id == "deep":
            s_out, l_out = max(s * 1.2, 0.50), min(l, 0.35)
            if l_out < 0.15: l_out = 0.15
        elif recipe_id == "vintage":
            h_warm = (h + 0.02) % 1.0
            s_out, l_out = max(s * 0.8, 0.30), l * 0.95
            h = h_warm
        elif recipe_id == "contrast":
            s_out = max(s * 1.3, 0.6)
            l_out = 0.3 if i % 2 == 0 else 0.8
        elif recipe_id == "pastel":
            s_out, l_out = 0.35, 0.85
        elif recipe_id == "diverse":
            s_out, l_out = max(s, 0.5), l
        else: # Classic
            s_out, l_out = s, l
            
        r, g, b = colorsys.hls_to_rgb(h, l_out, min(1.0, s_out))
        final.append((int(r*255), int(g*255), int(b*255)))
        
    while len(final) < 4: final.append((128, 128, 128))
    final.sort(key=lambda x: colorsys.rgb_to_hls(x[0]/255, x[1]/255, x[2]/255)[1])
    return final

def gen_gallery():
    img_path = "photos_in/20260213-17-11-00.jpg"
    raw_img = Image.open(img_path)
    from PIL import ImageOps
    raw_img = ImageOps.exif_transpose(raw_img).convert("RGB")
    
    # 1. Extract base clusters once
    clusters = extract_dominant_clusters(raw_img)
    
    recipes = [
        ("Classic", "classic"),
        ("Muted Pro", "muted"),
        ("Airy Pastel", "airy"),
        ("Deep Cinema", "deep"),
        ("Vivid Pop", "vibrant"),
        ("Vintage Warm", "vintage"),
        ("High Contrast", "contrast"),
        ("Monochrome", "monochrome"),
        ("Pure Pastel", "pastel"),
        ("Diverse Hub", "diverse")
    ]
    
    # Render Gallery
    card_w, card_h = 400, 150
    gallery = Image.new("RGB", (card_w * 2, card_h * 5), (255, 255, 255))
    draw = ImageDraw.Draw(gallery)
    
    try:
        font = ImageFont.truetype("assets/fonts/palab.ttf", 24)
    except:
        font = ImageFont.load_default()
        
    for i, (name, r_id) in enumerate(recipes):
        colors = apply_recipe(clusters, r_id)
        
        row = i // 2
        col = i % 2
        x_off = col * card_w
        y_off = row * card_h
        
        # Draw Name
        draw.text((x_off + 20, y_off + 20), f"{i+1}. {name}", fill=(50, 50, 50), font=font)
        
        # Draw Chips
        chip_size = 60
        spacing = 15
        for j, color in enumerate(colors):
            cx0 = x_off + 20 + (chip_size + spacing) * j
            cy0 = y_off + 60
            draw.rounded_rectangle([cx0, cy0, cx0 + chip_size, cy0 + chip_size], radius=12, fill=color)
            # Border for light
            l_val = 0.299*color[0] + 0.587*color[1] + 0.114*color[2]
            if l_val > 230:
                draw.rounded_rectangle([cx0, cy0, cx0 + chip_size, cy0 + chip_size], radius=12, outline=(200, 200, 200), width=1)

    if not os.path.exists("photos_out_test"): os.makedirs("photos_out_test")
    gallery.save("photos_out_test/palette_gallery.jpg", quality=95)
    print("SUCCESS: photos_out_test/palette_gallery.jpg generated")

if __name__ == "__main__":
    gen_gallery()
