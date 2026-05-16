import hashlib
import numpy as np
from PIL import Image
from .base import BaseTheme

class GradientTheme(BaseTheme):
    """
    EN: Linear gradient themes (Macaron, Sakura).
    CN: 线性渐变主题（马卡龙、樱花）。
    """
    def __init__(self, theme_type="macaron", img_path=""):
        self.theme_type = theme_type
        self.img_path = img_path

    def get_colors(self, index=0):
        if self.theme_type == "sakura":
            return (255, 245, 247), (125, 45, 65), (165, 95, 110), (255, 215, 225)
        else: # Macaron
            return (255, 255, 255), (26, 26, 26), (85, 85, 85), (238, 238, 238)

    def create_canvas(self, w, h, **kwargs):
        index = kwargs.get('index', -1)
        
        if self.theme_type == "sakura":
            palette = [
                (255, 245, 247), (255, 203, 217), (255, 180, 200),
                (255, 235, 240), (255, 190, 205), (255, 170, 190),
                (255, 220, 235), (255, 185, 200), (255, 160, 180)
            ]
        else: # Macaron
            palette = [
                (255, 180, 200), (210, 180, 255), (180, 220, 255), 
                (180, 255, 220), (255, 250, 190), (255, 210, 180),
                (200, 255, 255), (255, 220, 255), (220, 255, 180)
            ]

        if index >= 0:
            c_idx = index
        else:
            c_idx = int(hashlib.md5(self.img_path.encode()).hexdigest(), 16) % len(palette)

        c1 = palette[c_idx % len(palette)]
        c2 = palette[(c_idx + 1) % len(palette)]
        
        return self._generate_linear_gradient(w, h, c1, c2)

    def _generate_linear_gradient(self, w, h, c1, c2):
        base = np.linspace(0, 1, w)
        line = np.outer(np.ones(h), base)
        res = np.zeros((h, w, 3), dtype=np.uint8)
        for i in range(3):
            res[:, :, i] = c1[i] + (c2[i] - c1[i]) * line
        return Image.fromarray(res)
