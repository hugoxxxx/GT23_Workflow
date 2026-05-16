from PIL import Image, ImageFilter, ImageEnhance
from .base import BaseTheme
from ..effects.texture import TextureEngine
from ..effects.shadow import ShadowEngine

class FrostedTheme(BaseTheme):
    """
    EN: Glassmorphism / Frosted theme using blurred original image.
    CN: 磨砂玻璃主题，基于原图虚化。
    """
    def get_colors(self, index=0):
        # EN: Default light-on-frosted colors. 
        # CN: 默认磨砂背景下的文字颜色（浅色模式）。
        return (240, 240, 240), (26, 26, 26), (85, 85, 85), (200, 200, 200)

    def create_canvas(self, w, h, **kwargs):
        img = kwargs.get('img')
        if not img:
            return Image.new("RGB", (w, h), (240, 240, 240))
            
        # EN: Create frosted background by blurring the original image
        # CN: 通过对原图进行高斯模糊来创建磨砂背景
        canvas = img.resize((w, h), Image.Resampling.LANCZOS)
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=80))
        
        # EN: Increase brightness to simulate "Frosted" surface
        # CN: 增加亮度以模拟“磨砂”表面
        canvas = ImageEnhance.Brightness(canvas).enhance(1.15)
        
        # EN: Apply matte texture
        canvas = TextureEngine.apply_matte_texture(canvas, intensity=0.05)
        return canvas

    def draw_photo(self, canvas, img, x, y, line_color):
        # EN: Floating Photo Effect
        ShadowEngine.apply_floating_shadow(canvas, img, x, y)
