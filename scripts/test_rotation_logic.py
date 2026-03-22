import os
import sys
from PIL import Image
from core.renderer import FilmRenderer
from core.metadata import MetadataHandler

def test_rotation():
    # Create a simple test image
    img = Image.new('RGB', (100, 200), color='red')
    img.save('test_rot_in.jpg')
    
    renderer = FilmRenderer()
    meta = MetadataHandler()
    data = meta.get_data('test_rot_in.jpg')
    
    # Test 90 degree rotation (should result in landscape-ish border)
    out_dir = 'test_rot_out'
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    
    success = renderer.process_image('test_rot_in.jpg', data, out_dir, target_long_edge=800, manual_rotation=90)
    
    if success:
        print("Processing successful with 90deg rotation.")
        # Check output dimensions roughly
        out_file = os.path.join(out_dir, os.listdir(out_dir)[0])
        with Image.open(out_file) as out_img:
            print(f"Output size: {out_img.size}")
            # Original was 100x200. Rotated 90 is 200x100.
            # With borders, width should be > 200, height > 100.
            if out_img.width > out_img.height:
                print("Confirmed: Image was rotated to landscape.")
    else:
        print("Processing failed.")

if __name__ == "__main__":
    test_rotation()
