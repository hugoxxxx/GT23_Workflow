from core.renderer import FilmRenderer
from core.metadata import MetadataHandler
import os

def test_render():
    renderer = FilmRenderer()
    meta = MetadataHandler()
    
    img_dir = r"d:\Projects\GT23_Workflow\photos_in"
    out_dir = r"d:\Projects\GT23_Workflow\photos_out_test"
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    photos = sorted([f for f in os.listdir(img_dir) if f.lower().endswith('.jpg')])
    if not photos:
        print("No photos found.")
        return
        
    img_path = os.path.join(img_dir, photos[0])
    print(f"Testing with: {img_path}")
    
    # Force CONTAX G2 data for testing the new UI
    data = meta.get_data(img_path)
    # Ensure it's treated as Contax G2
    data['Make'] = "CONTAX"
    data['Model'] = "G2"
    data['LensModel'] = "Biogon T* 21mm f/2.8"
    data['Film'] = "PROVIA 100F"
    
    # Apply standard layout
    data['layout'] = {
        "side": 0.04,
        "top": 0.04,
        "bottom": 0.13,
        "font_scale": 0.032
    }
    
    success = renderer.process_image(img_path, data, out_dir)
    if success:
        print(f"Render successful! Output: {os.path.join(out_dir, 'GT23_' + os.path.splitext(photos[0])[0] + '.png')}")
    else:
        print("Render failed.")

if __name__ == "__main__":
    test_render()
