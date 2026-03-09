# core/typo_engine.py
# EN: Typography engine for kerning and text rendering
# CN: 排版引擎，处理字间距和文本渲染

import os
import sys
from fontTools.ttLib import TTFont
from PIL import ImageFont

class TypoEngine:
    """
    EN: Dedicated typography engine for kerning.
    CN: 排版引擎，专门处理字间距算法。
    """
    @staticmethod
    def get_kerning_offset(ttfont, left, right, font_size):
        # EN: Extract kerning offset from native kern table
        # CN: 从原生 kern 表中提取字间距偏移
        try:
            if 'kern' in ttfont:
                kt = ttfont['kern'].getkern(0)
                upm = ttfont['head'].unitsPerEm
                pair = (left, right)
                if pair in kt:
                    # EN: Conversion formula: (Units / EM) * FontSize
                    # CN: 转换公式：(Units / EM) * FontSize
                    return (kt[pair] / upm) * font_size
        except: 
            pass
        return 0

    @staticmethod
    def _resolve_font_path(font_path):
        # EN: Convert relative path to absolute path for EXE support
        # CN: 将相对路径转换为绝对路径，支持 EXE 环境
        if os.path.isabs(font_path):
            return font_path
        
        # EN: Get project root / CN: 获取项目根目录
        if getattr(sys, 'frozen', False):
            # EN: Running as EXE - use _MEIPASS for unpacked resources
            # CN: 以 EXE 形式运行 - 使用 _MEIPASS 获取解包资源
            project_root = sys._MEIPASS
        else:
            # EN: Running as script / CN: 以脚本形式运行
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
        
        return os.path.join(project_root, font_path)

    @classmethod
    def draw_text(cls, draw, pos, text, font_path, font_size, fill):
        """EN: Render text with native kern table.
           CN: 调用原生 Kern 表渲染文本。"""
        # EN: Resolve font path to support both script and EXE environments
        # CN: 解析字体路径，同时支持脚本和 EXE 环境
        font_path = cls._resolve_font_path(font_path)
        
        try:
            ttfont = TTFont(font_path)
            pil_font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            # EN: Fallback to default font if loading fails
            # CN: 如果加载失败，回退到默认字体
            pil_font = ImageFont.load_default()
            # EN: Draw text without kerning / CN: 不使用字间距绘制文本
            draw.text(pos, text, font=pil_font, fill=fill, anchor="mm")
            return
        
        chars = list(text)
        
        # EN: Calculate width for each character
        # CN: 计算每个字符的宽度
        widths = [draw.textlength(c, font=pil_font) for c in chars]
        
        # EN: Calculate kerning offsets for character pairs
        # CN: 计算字符对之间的字间距偏移
        offsets = [0]
        for i in range(len(chars) - 1):
            offsets.append(cls.get_kerning_offset(ttfont, chars[i], chars[i+1], font_size))
        
        # EN: Calculate total text width including kerning
        # CN: 计算包括字间距的总文本宽度
        total_advance = sum(widths) + sum(offsets)
        
        # --- EN: VISUAL CENTERING REFINEMENT / CN: 视觉居中优化 ---
        # EN: We need to know the actual ink bounds to perfectly match the Logo's centering.
        # CN: 我们需要知道实际墨迹边界，以完美匹配 Logo 的居中。
        
        # EN: Calculate character positions (relative to start)
        # CN: 计算每个字符相对于起始点的坐标
        relative_x_positions = []
        curr_rel_x = 0
        for i in range(len(chars)):
            curr_rel_x += offsets[i]
            relative_x_positions.append(curr_rel_x)
            curr_rel_x += widths[i]
            
        # EN: Estimate actual ink bounds for the whole line
        # CN: 预估整行文字的像素边界
        all_lefts = []
        all_rights = []
        for i, char in enumerate(chars):
            # EN: getmask(...).getbbox() gives (left, top, right, bottom) of glyph ink
            # CN: getmask(...).getbbox() 提供字形的像素包围盒
            char_bbox = pil_font.getmask(char).getbbox()
            if char_bbox:
                # char_bbox[0] is the ink offset from left, char_bbox[2] is ink right
                all_lefts.append(relative_x_positions[i] + char_bbox[0])
                all_rights.append(relative_x_positions[i] + char_bbox[2])
        
        if not all_lefts:
            # EN: Fallback to basic centering if no ink found / CN: 如果无墨迹则回退到基础居中
            start_x = pos[0] - total_advance / 2
        else:
            visual_left = min(all_lefts)
            visual_right = max(all_rights)
            visual_w = visual_right - visual_left
            # EN: Centering based on visual width / CN: 基于视觉宽度进行居中
            start_x = pos[0] - visual_w / 2 - visual_left

        # EN: Handle per-character coloring / CN: 处理逐字着色
        if isinstance(fill, list) and len(fill) == len(chars):
            colors = fill
        else:
            colors = [fill] * len(chars)

        # EN: Render each character with refined coordinates
        # CN: 使用对齐后的坐标进行逐字渲染
        for i, char in enumerate(chars):
            char_x = start_x + relative_x_positions[i]
            y_offset = font_size * 0.02
            # EN: Use anchor="lm" (left middle) for individual chars to keep vertical centering
            # CN: 对单个字符使用 "lm" 锚点，以保持垂直方向上的居中
            draw.text((char_x, pos[1] + y_offset), char, font=pil_font, fill=colors[i], anchor="lm")
