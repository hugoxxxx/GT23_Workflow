import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont
import io

# Manually inject Cairo DLL path for gt23 environment
CAIRO_PATH = r"C:\Users\Administrator\miniconda3\envs\gt23\Library\bin"
if os.path.exists(CAIRO_PATH):
    os.environ['PATH'] = CAIRO_PATH + os.pathsep + os.environ['PATH']
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(CAIRO_PATH)

import cairosvg

def gen_pure_logo_map():
    logo_dir = "assets/logo"
    assets_dir = os.path.abspath("assets")
    output_path = os.path.join(assets_dir, "LOGO_CATALOG_PURE.jpg")
    
    logo_files = sorted([f for f in os.listdir(logo_dir) if f.lower().endswith(('.png', '.svg', '.jpg'))])
    print(f"Total logos found: {len(logo_files)}")
    
    # Grid settings
    cols = 8 # Wider grid for 80+ logos
    rows = math.ceil(len(logo_files) / cols)
    
    cell_w = 400
    cell_h = 160 # Reduced height since text is gone
    margin = 40
    
    canvas_w = (cell_w * cols) + (margin * (cols + 1))
    canvas_h = (cell_h * rows) + (margin * (rows + 1))
    
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    
    for idx, filename in enumerate(logo_files):
        r = idx // cols
        c = idx % cols
        
        x_start = margin + c * (cell_w + margin)
        y_start = margin + r * (cell_h + margin)
        
        logo_path = os.path.join(logo_dir, filename)
        
        # 1. Load Logo
        logo_img = None
        try:
            if filename.lower().endswith('.svg'):
                # Render SVG at high res first, then downscale for quality and size control
                out = io.BytesIO()
                cairosvg.svg2png(url=logo_path, write_to=out, output_height=400) # Render tall
                out.seek(0)
                logo_img = Image.open(out).convert("RGBA")
            else:
                logo_img = Image.open(logo_path).convert("RGBA")
            
            # STRICT UNIFORM SIZING:
            # Scale to fit inside 320x100 box while maintaining aspect ratio
            logo_img.thumbnail((320, 100), Image.Resampling.LANCZOS)
            
        except Exception as e:
            print(f"ERR loading {filename}: {e}")
            continue

        if logo_img:
            lw, lh = logo_img.size
            # Horizontal centering
            lx = x_start + (cell_w - lw) // 2
            # Vertical centering in the cell
            ly = y_start + (cell_h - lh) // 2 
            
            canvas.paste(logo_img, (lx, ly), logo_img)

    canvas.save(output_path, quality=95)
    print(f"SUCCESS: Saved pure logo catalog to {output_path}")

if __name__ == "__main__":
    gen_pure_logo_map()
