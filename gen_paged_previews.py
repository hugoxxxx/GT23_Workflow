import os
import sys
import math
from PIL import Image, ImageDraw

# Add project root to path for core imports
sys.path.append(os.getcwd())

# Manually inject Cairo DLL path for gt23 environment
CAIRO_PATH = r"C:\Users\Administrator\miniconda3\envs\gt23\Library\bin"
if os.path.exists(CAIRO_PATH):
    os.environ['PATH'] = CAIRO_PATH + os.pathsep + os.environ['PATH']
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(CAIRO_PATH)

from core.renderer import FilmRenderer

def gen_paged_previews():
    # Force absolute paths for secondary assets to avoid relative lookup issues
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_main = os.path.join(base_dir, "assets", "fonts", "palab.ttf")
    font_sub = os.path.join(base_dir, "assets", "fonts", "gara.ttf")
    
    renderer = FilmRenderer(font_main=font_main, font_sub=font_sub)
    logo_dir = "assets/logo"
    output_temp = "temp_previews"
    if not os.path.exists(output_temp):
        os.makedirs(output_temp)
    else:
        # Clear it first to ensure dynamic scanning only finds NEW images
        for f in os.listdir(output_temp):
            if f.endswith(".jpg"): os.remove(os.path.join(output_temp, f))
        
    logo_files = sorted([f for f in os.listdir(logo_dir) if f.lower().endswith(('.png', '.svg', '.jpg'))])
    print(f"Total logos found: {len(logo_files)}")
    
    # Generate 18% grey dummy image
    dummy_path = os.path.join(base_dir, "temp_grey.jpg")
    grey_img = Image.new("RGB", (1500, 1000), (119, 119, 119))
    grey_img.save(dummy_path)
    
    rendered_images = []
    orig_stdout = sys.stdout

    for filename in logo_files:
        stem = os.path.splitext(filename)[0]
        if "-" in stem:
            parts = stem.split("-")
            make = parts[0]
            model = "-".join(parts[1:])
        else:
            make = ""
            model = stem
            
        data = {
            'Make': make,
            'Model': model,
            'Film': 'Sample Film',
            'LensModel': 'Sample Lens 50mm f/2.0',
            'ExposureTimeStr': '1/125',
            'FNumber': '8',
            'layout': {'name': 'PREVIEW', 'side': 0.05, 'top': 0.05, 'bottom': 0.15, 'font_scale': 0.04}
        }
        
        try:
            success = renderer.process_image(dummy_path, data, output_temp, target_long_edge=2000)
        except Exception:
            import traceback
            traceback.print_exc()
            success = False
        
        if success:
            # Dynamically find what was just created (it should be GT23_temp_grey.jpg then renamed)
            potential_files = [os.path.join(output_temp, f) for f in os.listdir(output_temp) if f.startswith("GT23_") and f.endswith(".jpg")]
            potential_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            if potential_files:
                actual_saved_path = potential_files[0]
                new_path = os.path.join(output_temp, f"{stem}_final.jpg")
                if os.path.exists(new_path): os.remove(new_path)
                os.rename(actual_saved_path, new_path)
                rendered_images.append(os.path.abspath(new_path))
                print(f"Captured: {stem}")
            else:
                print(f"ERROR: Success but no JPG for {stem}")
        else:
            print(f"ERROR: process_image returned False for {stem}")
    
    print(f"Total rendered images to paginate: {len(rendered_images)}")
    
    if not rendered_images:
        print("ERROR: No images were rendered. Exit.")
        return

    # Create Paginated Maps (10 per page, 2x5 grid)
    page_size = 10
    cols = 2
    rows = 5
    
    for i in range(0, len(rendered_images), page_size):
        page_num = (i // page_size) + 1
        batch = rendered_images[i:i + page_size]
        
        sample = Image.open(batch[0])
        sw, sh = sample.size
        # We will crop sh to a smaller height
        crop_h = int(sh * 0.30)
        
        margin = 40
        canvas_w = (sw * cols) + (margin * (cols + 1))
        canvas_h = (crop_h * rows) + (margin * (rows + 1))
        
        page_canvas = Image.new("RGB", (canvas_w, canvas_h), (240, 240, 240))
        
        for idx, img_path in enumerate(batch):
            r = idx // cols
            c = idx % cols
            
            x = margin + c * (sw + margin)
            y = margin + r * (crop_h + margin)
            
            btn_img = Image.open(img_path)
            
            # --- CROP TO BOTTOM AREA (METADATA + SOME IMAGE) ---
            bw, bh = btn_img.size
            # 30% captures the 15% border plus 15% of the grey image
            cropped = btn_img.crop((0, bh - crop_h, bw, bh))
            
            page_canvas.paste(cropped, (x, y))
            
        # Save page
        assets_dir = os.path.abspath("assets")
        if not os.path.exists(assets_dir): os.makedirs(assets_dir)
            
        page_path = os.path.join(assets_dir, f"LOGO_PREVIEW_PAGE_{page_num}.jpg")
        page_canvas.save(page_path, quality=92)
        print(f"SUCCESS_SAVED_PAGE: {page_path}")

    # --- NEW: GENERATE SINGLE CONSOLIDATED FULL MAP ---
    print("Generating Full Map (All logos in one)...")
    full_cols = 8 # Wider grid for 80+ logos
    full_rows = math.ceil(len(rendered_images) / full_cols)
    
    sample = Image.open(rendered_images[0])
    sw, sh = sample.size
    crop_h = int(sh * 0.30)
    
    full_margin = 30
    full_canvas_w = (sw * full_cols) + (full_margin * (full_cols + 1))
    full_canvas_h = (crop_h * full_rows) + (full_margin * (full_rows + 1))
    
    full_canvas = Image.new("RGB", (full_canvas_w, full_canvas_h), (245, 245, 245))
    
    for idx, img_path in enumerate(rendered_images):
        r = idx // full_cols
        c = idx % full_cols
        
        x = full_margin + c * (sw + full_margin)
        y = full_margin + r * (crop_h + full_margin)
        
        btn_img = Image.open(img_path)
        # Use same crop as before
        bw, bh = btn_img.size
        # Note: if rendered_images are already cropped, we don't crop again
        # BUT: the rendered_images list currently holds paths to FULL renders in temp_previews
        # The loop above crops them on the fly. We do the same here.
        cropped = btn_img.crop((0, bh - crop_h, bw, bh))
        full_canvas.paste(cropped, (x, y))
        
    full_map_path = os.path.join(assets_dir, "LOGO_FULL_MAP.jpg")
    full_canvas.save(full_map_path, quality=90)
    print(f"SUCCESS_SAVED_FULL_MAP: {full_map_path}")

if __name__ == "__main__":
    gen_paged_previews()
