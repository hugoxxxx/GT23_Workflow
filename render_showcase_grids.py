import os
import time
from PIL import Image
from core.renderer import FilmRenderer

def create_3x3_grid(image_paths, output_path, bg_color=(255, 255, 255)):
    valid_paths = [p for p in image_paths if os.path.exists(p)]
    if not valid_paths: return
    
    images = [Image.open(p) for p in valid_paths[:9]]
    
    # Resize for grid
    target_w = 1000
    resized = [img.resize((target_w, int(img.height * target_w / img.width)), Image.Resampling.LANCZOS) for img in images]
    
    cell_w, cell_h = resized[0].size
    gap = 20
    grid_w = cell_w * 3 + gap * 2 + 60
    grid_h = cell_h * 3 + gap * 2 + 60
    
    canvas = Image.new('RGB', (grid_w, grid_h), bg_color)
    
    for i, img in enumerate(resized):
        row = i // 3
        col = i % 3
        x = 30 + col * (cell_w + gap)
        y = 30 + row * (cell_h + gap)
        canvas.paste(img, (x, y))
        
    canvas.save(output_path, quality=95)
    print(f"Saved grid to {output_path}")

def render_single(renderer, img_path, data, theme, output_path):
    renderer.process_image(img_path, data, "temp_renders", theme=theme, is_sample=True)
    time.sleep(0.5)
    files = os.listdir("temp_renders")
    if files:
        final_p = os.path.abspath(output_path)
        img = Image.open(os.path.join("temp_renders", files[0]))
        img.save(final_p, quality=95)
        print(f"Saved single to {final_p}")
        return final_p
    return None

def main():
    renderer = FilmRenderer()
    img_path = "temp_grey.jpg"
    if not os.path.exists(img_path):
        img_path = "test_in.jpg"
        
    data = {
        'make': 'FUJIFILM',
        'model': 'GA645Zi',
        'lens': 'Super-EBC Fujinon 55-90mm f/4.5',
        'shutter': '1/125s',
        'aperture': 'f/8.0',
        'iso': '400',
        'datetime': '2026:03:28 12:00:00',
        'is_sample': True
    }
    
    output_temp = "temp_renders"
    os.makedirs(output_temp, exist_ok=True)
    os.makedirs("previews/v2.3", exist_ok=True)
    
    # 1. Dark - Single Image
    print("Rendering Dark Single...")
    for f in os.listdir(output_temp): 
        try: os.remove(os.path.join(output_temp, f))
        except: pass
    render_single(renderer, img_path, data, "dark", "previews/v2.3/sample_dark.jpg")

    def render_theme_batch(theme, count):
        paths = []
        for i in range(count):
            for f in os.listdir(output_temp): 
                try: os.remove(os.path.join(output_temp, f))
                except: pass
            
            # --- FIX: Pass rainbow_range for rainbow theme ---
            kwargs = {}
            if theme == "rainbow":
                step = 1.0 / count
                kwargs['rainbow_range'] = (i * step, (i + 1) * step)
                print(f"Rendering Rainbow {i}/9 with range {kwargs['rainbow_range']}")
            
            renderer.process_image(img_path, data, output_temp, theme=theme, 
                                   rainbow_index=i, rainbow_total=count, is_sample=True, **kwargs)
            time.sleep(0.3)
            files = sorted(os.listdir(output_temp))
            if files:
                final_p = os.path.abspath(f"previews/v2.3/{theme}_{i}.jpg")
                Image.open(os.path.join(output_temp, files[0])).save(final_p)
                paths.append(final_p)
        return paths

    print("Rendering Macaron Grid...")
    macaron_files = render_theme_batch("macaron", 9)
    create_3x3_grid(macaron_files, "previews/v2.3/grid_macaron.jpg")
    
    print("Rendering Rainbow Grid (True Continuous)...")
    rainbow_files = render_theme_batch("rainbow", 9)
    create_3x3_grid(rainbow_files, "previews/v2.3/grid_rainbow.jpg")

if __name__ == "__main__":
    main()
