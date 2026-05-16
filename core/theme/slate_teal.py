import numpy as np
from PIL import Image
from .base import BaseTheme
from ..effects.texture import TextureEngine

class SlateTealTheme(BaseTheme):
    """
    EN: Premium Slate-Teal Gradient theme.
    CN: 顶级石板青渐变主题。
    """
    def get_colors(self, index=0):
        # EN: Luminous Air / Breathable Slate
        return (210, 222, 228), (245, 245, 250), (215, 222, 228), (180, 190, 200)

    def create_canvas(self, w, h, **kwargs):
        c_top = (210, 222, 228)
        c_bottom = (125, 142, 152)
        
        # EN: We'll use a shared gradient utility later, but for now we implement it here 
        # or use the renderer's existing private method if we can't move it yet.
        # Actually, let's implement a reusable gradient helper in core/utils/gradient.py
        # But for Step 9, I'll put a simplified implementation here to keep it moving.
        
        canvas = self._generate_gradient(w, h, c_top, c_bottom, vertical=True, gamma=1.6)
        canvas = TextureEngine.apply_matte_texture(canvas, intensity=0.06)
        return canvas

    def draw_photo(self, canvas, img, x, y, line_color):
        # EN: Floating Photo Effect
        from ..effects.shadow import ShadowEngine
        ShadowEngine.apply_floating_shadow(canvas, img, x, y)

    def _generate_gradient(self, w, h, c1, c2, vertical=True, gamma=1.0):
        # EN: Basic linear gradient with gamma correction
        base = np.linspace(0, 1, h if vertical else w)
        if gamma != 1.0:
            base = np.power(base, gamma)
        
        line = np.outer(base, np.ones(w if vertical else h))
        if not vertical:
            line = line.T
            
        res = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(3):
            res[:, :, i] = c1[i] + (c2[i] - c1[i]) * line
            
        return Image.fromarray(res)
