import random
from PIL import Image, ImageChops

class TextureEngine:
    """
    EN: Matte texture and grain simulation engine.
    CN: 哑光纹理与颗粒模拟引擎。
    """
    
    @staticmethod
    def apply_matte_texture(canvas, intensity=0.03):
        """
        EN: Adds a subtle fine-art paper grain effect.
        CN: 添加微细的艺术纸张颗粒感特效。
        """
        w, h = canvas.size
        # EN: Create a tileable noise block for performance (256x256)
        tile_size = 256
        noise_tile = Image.new('L', (tile_size, tile_size))
        
        # EN: Fast noise generation
        pixels = [random.randint(110, 145) for _ in range(tile_size * tile_size)]
        noise_tile.putdata(pixels)
        
        # EN: Create full-size noise overlay
        noise_overlay = Image.new('L', (w, h))
        for y in range(0, h, tile_size):
            for x in range(0, w, tile_size):
                noise_overlay.paste(noise_tile, (x, y))
        
        # EN: Blend noise with canvas (Visual Parity with v2.4.0)
        noise_rgb = Image.merge("RGB", (noise_overlay, noise_overlay, noise_overlay))
        return Image.blend(canvas.convert("RGB"), noise_rgb, intensity)
