import os
from fontTools.ttLib import TTFont
from PIL import ImageFont

class TypoEngine:
    """
    EN: Dedicated typography engine for kerning.
    CN: 中英双语：排版引擎，专门处理字间距算法。
    """
    @staticmethod
    def get_kerning_offset(ttfont, left, right, font_size):
        try:
            if 'kern' in ttfont:
                kt = ttfont['kern'].getkern(0)
                upm = ttfont['head'].unitsPerEm
                pair = (left, right)
                if pair in kt:
                    # EN: (Units / EM) * FontSize / CN: 转换公式
                    return (kt[pair] / upm) * font_size
        except: pass
        return 0

    @classmethod
    def draw_text(cls, draw, pos, text, font_path, font_size, fill):
        """
        EN: Render text with native kern table.
        CN: 中英双语：调用原生 Kern 表渲染文本。
        """
        ttfont = TTFont(font_path)
        pil_font = ImageFont.truetype(font_path, font_size)
        chars = list(text)
        
        widths = [draw.textlength(c, font=pil_font) for c in chars]
        offsets = [0]
        for i in range(len(chars) - 1):
            offsets.append(cls.get_kerning_offset(ttfont, chars[i], chars[i+1], font_size))
        
        total_w = sum(widths) + sum(offsets)
        curr_x = pos[0] - total_w / 2
        
        for i, char in enumerate(chars):
            curr_x += offsets[i]
            y_offset = font_size * 0.02
            draw.text((curr_x + widths[i]/2, pos[1]+y_offset), char, font=pil_font, fill=fill, anchor="mm")
            curr_x += widths[i]