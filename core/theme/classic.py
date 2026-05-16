from PIL import Image
from .base import BaseTheme

class ClassicTheme(BaseTheme):
    """
    EN: Classic Light/Dark themes.
    CN: 经典浅色/深色主题。
    """
    def __init__(self, mode="light"):
        self.mode = mode

    def get_colors(self, index=0):
        if self.mode == "dark":
            return (15, 16, 20), (245, 245, 245), (210, 210, 210), (45, 45, 45)
        else: # Light
            return (255, 255, 255), (26, 26, 26), (85, 85, 85), (238, 238, 238)

    def create_canvas(self, w, h, **kwargs):
        bg_color, _, _, _ = self.get_colors()
        return Image.new("RGB", (w, h), bg_color)
