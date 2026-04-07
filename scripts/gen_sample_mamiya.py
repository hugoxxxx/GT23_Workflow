import os
import sys
from PIL import Image

# Add project root to path for core imports
sys.path.append(os.getcwd())

from core.renderer import FilmRenderer

def gen_mamiya_sample():
    renderer = FilmRenderer()
    
    # 1. Create 18% gray dummy image (1500x1500 for 6x6 Square Format)
    # 18% gray is typically RGB(119, 119, 119)
    grey_img = Image.new("RGB", (1500, 1500), (119, 119, 119))
    base_path = "temp_grey_sample.jpg"
    grey_img.save(base_path)
    
    # 2. Metadata for Mamiya 6
    # Lens: Mamiya G 75mm f/3.5 L (Standard)
    # Film: PROVIA 100F (Classic choice for Mamiya 6)
    data = {
        'Make': 'MAMIYA',
        'Model': '6',
        'Film': 'PROVIA 100F',
        'LensModel': 'Mamiya G 75mm f/3.5 L',
        'ExposureTimeStr': '1/125',
        'FNumber': '8',
        'ISO': '100',
        # Standard preview layout settings
        'layout': {'name': 'PREVIEW', 'side': 0.05, 'top': 0.05, 'bottom': 0.15, 'font_scale': 0.04}
    }
    
    output_dir = "photos_out_test"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print("Rendering Mamiya 6 sample...")
    # Using a higher target_long_edge for better visual quality in the artifact
    try:
        success = renderer.process_image(base_path, data, output_dir, target_long_edge=2400)
        if success:
            print(f"SUCCESS: Sample saved to {output_dir}")
        else:
            print("ERROR: process_image returned False")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    gen_mamiya_sample()
