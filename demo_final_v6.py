# demo_final_v6.py
import os
import sys
from PIL import Image

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.renderers.renderer_matin import RendererMatin
from core.metadata import MetadataHandler

def demo():
    renderer = RendererMatin()
    meta = MetadataHandler()
    
    # Setup dummy paths and config
    img_path = "dummy.jpg"
    if not os.path.exists(img_path):
        Image.new("RGB", (1000, 1000), (100, 120, 140)).save(img_path)
    
    cfg = meta.get_contact_layout("MATIN_135")
    font_path = "assets/fonts/slide/ArchitectsDaughter-Regular.ttf"
    
    # 1. Normal Render (No offset)
    print("Rendering normal...")
    img_normal = renderer.render_single_slide(
        img_path, cfg, meta, 
        custom_l1="NORMAL POSITION",
        custom_l2="DEFAULT SIZE",
        font_path=font_path
    )
    # Composite on white to see shadows
    bg_normal = Image.new("RGB", img_normal.size, (255, 255, 255))
    bg_normal.paste(img_normal, (0, 0), img_normal)
    bg_normal.save("demo_v6_normal.jpg", quality=95)
    
    # 2. Adjusted Render (Y -20, Size +10)
    print("Rendering adjusted...")
    img_adj = renderer.render_single_slide(
        img_path, cfg, meta, 
        custom_l1="Y-OFFSET: +30, SIZE: +15",
        custom_l2="Y-OFFSET: -20, SIZE: -5",
        font_path=font_path,
        label_cfg={
            'l1_y_offset': 30,
            'l1_fs_offset': 15,
            'l2_y_offset': -20,
            'l2_fs_offset': -5
        }
    )
    bg_adj = Image.new("RGB", img_adj.size, (255, 255, 255))
    bg_adj.paste(img_adj, (0, 0), img_adj)
    bg_adj.save("demo_v6_adjusted.jpg", quality=95)
    
    # Combine for easy viewing
    w, h = bg_normal.size
    combined = Image.new("RGB", (w * 2 + 20, h), (240, 240, 240))
    combined.paste(bg_normal, (0, 0))
    combined.paste(bg_adj, (w + 20, 0))
    combined.save("demo_v6_comparison.jpg", quality=95)
    print("Demo saved to demo_v6_comparison.jpg")

if __name__ == "__main__":
    demo()
