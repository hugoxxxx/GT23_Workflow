from PIL import Image, ImageFilter, ImageEnhance
from .base import BaseTheme
from ..effects.texture import TextureEngine
from ..effects.shadow import ShadowEngine

class FrostedTheme(BaseTheme):
    """
    EN: Glassmorphism / Frosted theme using blurred original image.
    CN: 磨砂玻璃主题，基于原图虚化。
    """
    def __init__(self):
        # EN: Theme-specific constants that can be overridden by data
        # CN: 主题专用常量，未来可被 data 字典覆盖
        self.shadow_offset = (70, 180)
        self.shadow_intensity = 1.5

    def get_colors(self, index=0):
        # EN: Default light-on-frosted colors. 
        # CN: 默认磨砂背景下的文字颜色（浅色模式）。
        return (240, 240, 240), (26, 26, 26), (85, 85, 85), (200, 200, 200)

    def create_canvas(self, w, h, **kwargs):
        img = kwargs.get('img')
        if not img:
            return Image.new("RGB", (w, h), (240, 240, 240))
            
        # EN: Create frosted background using 'Cover' logic to preserve aspect ratio
        # CN: 使用 Cover 逻辑创建磨砂背景，保持原图比例不被拉伸
        img_ratio = img.width / img.height
        canvas_ratio = w / h
        
        if img_ratio > canvas_ratio:
            # EN: Image is wider, crop sides / CN: 原图更宽，裁剪两侧
            new_h = h
            new_w = int(h * img_ratio)
            bg = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - w) // 2
            canvas = bg.crop((left, 0, left + w, h))
        else:
            # EN: Image is taller, crop top/bottom / CN: 原图更高，裁剪上下
            new_w = w
            new_h = int(w / img_ratio)
            bg = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            top = (new_h - h) // 2
            canvas = bg.crop((0, top, w, top + h))

        # EN: Calculate dynamic blur radius based on resolution
        # CN: 根据分辨率计算动态模糊半径，确保预览与导出效果一致
        long_edge = max(w, h)
        dynamic_radius = int(80 * (long_edge / 2000.0))
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=dynamic_radius))
        
        # EN: Increase brightness to simulate "Frosted" surface
        # CN: 增加亮度以模拟“磨砂”表面
        canvas = ImageEnhance.Brightness(canvas).enhance(1.15)
        
        # EN: Apply matte texture
        canvas = TextureEngine.apply_matte_texture(canvas, intensity=0.05)
        return canvas

    def draw_photo(self, canvas, img, x, y, line_color):
        # EN: Premium Studio Floating Shadow using class configuration
        # CN: 使用类配置的高级悬浮投影
        ShadowEngine.apply_floating_shadow(
            canvas, img, x, y, 
            offset=self.shadow_offset, 
            intensity=self.shadow_intensity
        )
