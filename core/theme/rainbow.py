import numpy as np
from PIL import Image, ImageDraw
from .base import BaseTheme

class RainbowTheme(BaseTheme):
    """
    EN: Fuji Rainbow theme with physical continuity support.
    CN: 富士彩虹主题，支持物理连续性（切片渲染）。
    """
    def get_colors(self, index=0):
        palette = [
            (30, 50, 110), (30, 120, 200), (0, 200, 240), (140, 210, 50), 
            (255, 220, 0), (255, 140, 0), (255, 70, 60), (255, 70, 140), 
            (180, 50, 160), (100, 20, 120)
        ]
        bg = palette[index % len(palette)]
        return bg, (26, 26, 26), (85, 85, 85), (255, 255, 255)

    def create_canvas(self, w, h, **kwargs):
        t_start = max(0.0, min(1.0, float(kwargs.get('t_start', 0.0))))
        t_end = max(0.0, min(1.0, float(kwargs.get('t_end', 1.0))))
        
        colors = [
            (255, 110, 110), (255, 180, 70), (255, 230, 80), 
            (120, 240, 120), (100, 230, 245), (100, 160, 255), (200, 100, 255)
        ]
        
        canvas = Image.new("RGB", (w, h))
        pixels = np.zeros((h, w, 3), dtype=np.uint8)
        
        for x in range(w):
            pos = t_start + (x / w) * (t_end - t_start)
            num_segments = len(colors) - 1
            segment = int(pos * num_segments)
            segment = min(segment, num_segments - 1)
            
            t = (pos * num_segments) - segment
            c1 = colors[segment]
            c2 = colors[segment + 1]
            
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            
            pixels[:, x, :] = [r, g, b]
            
        return Image.fromarray(pixels)
