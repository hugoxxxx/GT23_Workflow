from abc import ABC, abstractmethod
from PIL import Image, ImageDraw

class BaseTheme(ABC):
    """
    EN: Abstract base class for all border themes.
    CN: 所有边框主题的抽象基类。
    """
    
    @abstractmethod
    def get_colors(self, index=0):
        """
        EN: Returns (bg_color, main_color, sub_color, line_color).
        CN: 返回颜色配置 (背景色, 主文字色, 副文字色, 线条色)。
        """
        pass

    @abstractmethod
    def create_canvas(self, w, h, **kwargs):
        """
        EN: Creates the base canvas for the theme.
        CN: 为主题创建基础画布。
        """
        pass

    def draw_photo(self, canvas, img, x, y, line_color):
        """
        EN: Default implementation for pasting the photo. Override for custom effects.
        CN: 粘贴照片的默认实现。如果需要特殊效果（如浮动投影）可重写。
        """
        canvas.paste(img, (x, y))
        ImageDraw.Draw(canvas).rectangle([x, y, x + img.width, y + img.height], outline=line_color, width=1)

    def resolve_adaptive_colors(self, canvas, rect, default_main, default_sub):
        """
        EN: Optional: Adjust colors based on the sampled rectangle. Default returns inputs.
        CN: 可选：根据采样区域调整颜色。默认直接返回传入的颜色。
        """
        return default_main, default_sub
