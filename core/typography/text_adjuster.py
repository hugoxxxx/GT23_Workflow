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
        if "1050" in str(resolved_main):
            # EN: PNG font 1050 is narrow (avg width ~0.45-0.5x height)
            # CN: 1050 字体较瘦窄，宽度系数调整为 0.48
            main_text_width = len(main_text) * (base_main_size * 0.48)
        else:
            main_font = TextAdjuster._get_font(resolved_main, base_main_size)
            main_bbox = temp_draw.textbbox((0, 0), main_text, font=main_font)
            main_text_width = main_bbox[2] - main_bbox[0]
            
        main_scale = min(1.0, available_width / main_text_width) if main_text_width > 0 else 1.0
        
        # 2. EN: Measure Sub Text / CN: 测量副文本
        if "1050" in str(resolved_sub):
            sub_text_width = len(sub_text) * (base_sub_size * 0.48)
        else:
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

    @staticmethod
    def check_vertical_collision(actual_main_size, actual_sub_size, resolved_main, h_img, top_pad, inner_bottom_margin, bottom_splice, ref_factor):
        """
        EN: Check if text overlaps with the photo and suggest adjustments.
        CN: 检查文字是否与照片重叠，并给出调整建议。
        """
        m_font = TextAdjuster._get_font(resolved_main, actual_main_size)
        m_ascent, m_descent = m_font.getmetrics()
        
        photo_bottom = top_pad + h_img
        total_bottom_space = inner_bottom_margin + bottom_splice
        
        # EN: v2.4.1 Layout logic constants
        base_y = photo_bottom + int(total_bottom_space * 0.38)
        v_gap_ref = max(actual_main_size, actual_sub_size)
        main_y = base_y - int(v_gap_ref * 0.55)
        
        v_overflow = (main_y - m_ascent) < photo_bottom
        
        suggested_main_px = None
        if v_overflow:
            # EN: Approximate max font size that fits vertically without overlapping
            center_gap = (inner_bottom_margin + bottom_splice) // 2
            suggested_main_px = int(center_gap / 1.35 / ref_factor)
            
        return v_overflow, suggested_main_px
