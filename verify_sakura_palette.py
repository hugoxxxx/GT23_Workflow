import os
import sys
from PIL import Image
# Add project root to sys.path
sys.path.append(os.getcwd())

from core.renderer import FilmRenderer

def test_sakura_refined():
    renderer = FilmRenderer()
    img_path = "test_sakura_refined.jpg"
    if not os.path.exists(img_path):
        img = Image.new("RGB", (1200, 800), (220, 220, 220))
        img.save(img_path)
    
    data = {
        'Make': 'CANON', 'Model': 'EOS R6', 
        'Film': 'SAKURA REFINED LIGHTNESS',
        'layout': {'side': 0.05, 'top': 0.05, 'bottom': 0.15, 'font_scale': 0.035},
        'show_make': 1, 'show_model': 1, 'show_lens': 1, 'is_digital': True
    }
    
    output_dir = "test_outputs_sakura_refined"
    os.makedirs(output_dir, exist_ok=True)
    
    # Render all 9 colors to check the new deep shades
    for i in range(9):
        renderer.process_image(
            img_path, data, output_dir, 
            target_long_edge=1200, 
            theme="sakura", 
            rainbow_index=i,
            output_prefix=f"refined_{i}_"
        )
    print(f"SUCCESS: Generated 9 refined sakura samples in '{output_dir}/'")

if __name__ == "__main__":
    test_sakura_refined()
