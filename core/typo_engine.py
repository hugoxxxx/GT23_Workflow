# core/typo_engine.py
# EN: Typography engine for kerning and text rendering
# CN: 排版引擎，处理字间距和文本渲染

import os
import sys
import time
from fontTools.ttLib import TTFont
from PIL import ImageFont, Image

class TypoEngine:
    """
    EN: Dedicated typography engine for kerning.
    CN: 排版引擎，专门处理字间距算法。
    """
    _font_cache = {}  # EN: Cache for (path, size) -> (pil_font, ttfont)
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
        
        return os.path.normcase(os.path.normpath(os.path.join(project_root, font_path)))

    @classmethod
    def draw_mixed_text(cls, draw, pos, segments, font_path, font_size, default_fill, timings=None, key_prefix="mixed"):
        """
        EN: Render a mix of text segments and image tokens (badges).
        CN: 渲染混合了文本片段和图片标识（勋章）的内容。
        args:
            segments: List of dicts, e.g. [{"type": "text", "content": "FE 24-70mm ", "color": (rgb)}, {"type": "image", "path": "path/to/gm.png"}]
        """
        if timings is None: timings = {}
        t0 = time.perf_counter()
        font_path = cls._resolve_font_path(font_path)
        
        cache_key = (font_path, font_size)
        if cache_key in cls._font_cache:
            pil_font, ttfont = cls._font_cache[cache_key]
        else:
            try:
                if font_path.lower().endswith(".ttc"):
                    ttfont = TTFont(font_path, fontNumber=0)
                    pil_font = ImageFont.truetype(font_path, font_size, index=0)
                else:
                    ttfont = TTFont(font_path)
                    pil_font = ImageFont.truetype(font_path, font_size)
                cls._font_cache[cache_key] = (pil_font, ttfont)
            except:
                pil_font = ImageFont.load_default()
                ttfont = None

        # 1. EN: Pre-calculate widths and load images / CN: 预计算宽度并加载图片
        prepared_segments = []
        total_w = 0
        ascent, descent = pil_font.getmetrics()
        line_h = ascent + descent

        for seg in segments:
            if seg["type"] == "text":
                content = seg["content"]
                color = seg.get("color", default_fill)
                
                chars = list(content)
                widths = [draw.textlength(c, font=pil_font) for c in chars]
                offsets = [0]
                if ttfont:
                    for i in range(len(chars) - 1):
                        offsets.append(cls.get_kerning_offset(ttfont, chars[i], chars[i+1], font_size))
                
                seg_w = sum(widths) + sum(offsets)
                prepared_segments.append({
                    "type": "text",
                    "content": content,
                    "color": color,
                    "width": seg_w,
                    "char_widths": widths,
                    "offsets": offsets
                })
                total_w += seg_w
            elif seg["type"] == "image":
                img_path = seg["path"]
                try:
                    token_img = Image.open(img_path).convert("RGBA")
                    # EN: Scale to match text height / CN: 缩放以匹配文字高度
                    orig_w, orig_h = token_img.size
                    scaled_w = int(orig_w * (line_h / orig_h))
                    token_img = token_img.resize((scaled_w, line_h), Image.Resampling.LANCZOS)
                    
                    prepared_segments.append({
                        "type": "image",
                        "img": token_img,
                        "width": scaled_w
                    })
                    total_w += scaled_w
                except Exception as e:
                    print(f"CN: [!] 无法加载混合 Token: {e}")
                    continue

        # 2. EN: Global Start Position (Center aligned) / CN: 全局起始点（居中对齐）
        curr_x = pos[0] - total_w / 2
        base_y = pos[1]

        # 3. EN: Sequential Rendering / CN: 顺序渲染
        for seg in prepared_segments:
            if seg["type"] == "text":
                # EN: Draw text character by character for precision / CN: 逐字精准绘制文本
                content = seg["content"]
                colors = seg["color"] if isinstance(seg["color"], list) else [seg["color"]] * len(content)
                char_widths = seg["char_widths"]
                offsets = seg["offsets"]
                
                for i, char in enumerate(content):
                    curr_x += offsets[i]
                    y_offset = font_size * 0.02
                    draw.text((curr_x, base_y + y_offset), char, font=pil_font, fill=colors[i], anchor="lm")
                    curr_x += char_widths[i]
            elif seg["type"] == "image":
                # EN: Paste image token / CN: 粘贴图片 Token
                img = seg["img"]
                # EN: Vertical alignment - anchor="lm" equivalent for images
                # CN: 垂直对齐 - 图片的等效 "lm" 居中
                paste_y = int(base_y - img.height // 2)
                draw._image.paste(img, (int(curr_x), paste_y), img)
                curr_x += seg["width"]
        
        timings[f'{key_prefix}_total'] = time.perf_counter() - t0
