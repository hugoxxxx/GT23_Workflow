import os
from PIL import Image, ImageDraw, ImageFont

class TextAdjuster:
    """
    EN: Responsible for adaptive font scaling to prevent overflow.
    CN: 负责文字的自适应缩放计算，防止溢出。
    """
    @staticmethod
    def adjust(draw, main_text, sub_text, available_width, base_main_size, base_sub_size, resolver, main_path=None, sub_path=None):
        """
        EN: Adjust font sizes to fit available width.
        CN: 调整字体大小使其适应可用宽度。
        """
        if available_width <= 0:
            return 10, 8, 1.0, 1.0
            
        # EN: Resolve font paths / CN: 解析字体路径
        # v2.4.1: Support explicit path overrides from caller
        if main_path and sub_path:
            resolved_main, resolved_sub = main_path, sub_path
        else:
            resolved_main, resolved_sub = resolver.resolve(main_text, sub_text)

        # EN: Create temporary draw for measurement / CN: 创建临时绘图对象测量宽度
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 1. EN: Measure Main Text / CN: 测量主文本
        main_font = TextAdjuster._get_font(resolved_main, base_main_size)
        main_bbox = temp_draw.textbbox((0, 0), main_text, font=main_font)
        main_text_width = main_bbox[2] - main_bbox[0]
        main_scale = min(1.0, available_width / main_text_width) if main_text_width > 0 else 1.0
        
        # 2. EN: Measure Sub Text / CN: 测量副文本
        sub_font = TextAdjuster._get_font(resolved_sub, base_sub_size)
        sub_text_width = sum(temp_draw.textlength(c, font=sub_font) for c in list(sub_text))
        sub_scale = min(1.0, available_width / sub_text_width) if sub_text_width > 0 else 1.0
        
        # EN: Decouple scaling to allow main title to grow independently
        # CN: 解耦主副标题缩放，允许型号名保持独立增长
        final_main_size = max(10, int(base_main_size * main_scale))
        final_sub_size = max(8, int(base_sub_size * sub_scale))
        
        return final_main_size, final_sub_size, main_scale, sub_scale

    @staticmethod
    def _get_font(font_path, size):
        """EN: Safe font loading. / CN: 安全加载字体。"""
        try:
            if os.path.exists(font_path):
                if font_path.lower().endswith(".ttc"):
                    return ImageFont.truetype(font_path, size, index=0)
                return ImageFont.truetype(font_path, size)
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()
