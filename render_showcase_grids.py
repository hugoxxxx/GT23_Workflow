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

def create_horizontal_strip(image_paths, output_path):
    valid_paths = [p for p in image_paths if os.path.exists(p)]
    if not valid_paths: return
    
    images = [Image.open(p) for p in valid_paths]
    # Resize for strip
    target_h = 800
    resized = [img.resize((int(img.width * target_h / img.height), target_h), Image.Resampling.LANCZOS) for img in images]
    
    total_w = sum(img.width for img in resized)
    canvas = Image.new('RGB', (total_w, target_h), (255, 255, 255))
    
    curr_x = 0
    for img in resized:
        canvas.paste(img, (curr_x, 0))
        curr_x += img.width
        
    canvas.save(output_path, quality=95)
    print(f"Saved horizontal strip to {output_path}")

def render_single(renderer, img_path, data, theme, output_path):
    # Ensure a fresh render
    if not os.path.exists("temp_renders"): os.makedirs("temp_renders")
    for f in os.listdir("temp_renders"):
        try: os.remove(os.path.join("temp_renders", f))
        except: pass
        
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
    render_single(renderer, img_path, data, "dark", "previews/v2.3/sample_dark.jpg")

    def render_theme_batch(theme, count):
        paths = []
        for i in range(count):
            for f in os.listdir(output_temp): 
                try: os.remove(os.path.join(output_temp, f))
                except: pass
            
            kwargs = {}
            if theme == "rainbow":
                step = 1.0 / count
                kwargs['rainbow_range'] = (i * step, (i + 1) * step)
                print(f"Rendering Rainbow {i}/{count} with range {kwargs['rainbow_range']}")
            
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
    
    print("Rendering Rainbow 10-Image Strip...")
    rainbow_files = render_theme_batch("rainbow", 10)
    create_horizontal_strip(rainbow_files, "previews/v2.3/strip_rainbow_10.jpg")

if __name__ == "__main__":
    main()
