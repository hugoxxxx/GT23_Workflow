import os
import sys
from PIL import Image
from core.renderer import FilmRenderer

def test_pure_border():
    print("Testing Pure Border Mode...")
    renderer = FilmRenderer()
    # Dummy data
    data = {
        'Make': 'Leica',
        'Model': 'M11',
        'layout': {'side': 0.05, 'top': 0.05, 'bottom': 0.15, 'font_scale': 0.03}
    }
    
    # Use a dummy small image
    img = Image.new('RGB', (1000, 1000), color=(200, 200, 200))
    img.save('test_in.jpg')
    
    output_dir = 'test_out'
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    
    # Test Pure Border
    print("-> Rendering Pure Border...")
    out_name_pure = renderer.process_image('test_in.jpg', data, output_dir, is_pure=True, theme="fuji_rainbow")
    print(f"Generated pure border image: {out_name_pure}")
    
    # Test Chinese Font
    print("-> Rendering CJK Text...")
    data_cn = data.copy()
    data_cn['Model'] = '徕卡 M11 (上海)'
    out_name_cn = renderer.process_image('test_in.jpg', data_cn, output_dir, is_pure=False, theme="light")
    print(f"Generated CJK image: {out_name_cn}")
    
    print("\n[VERIFICATION DONE]")

if __name__ == "__main__":
    test_pure_border()
