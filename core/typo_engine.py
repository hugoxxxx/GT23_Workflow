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
    _fallback_cache = {} # EN: Cache for fallback fonts

    @classmethod
    def _has_glyph(cls, ttfont, char):
        # EN: Check if the character is supported by the font
        # CN: 检查字库是否支持该字符
        if not ttfont: return False
        try:
            for table in ttfont['cmap'].tables:
                if ord(char) in table.cmap:
                    return True
        except:
            pass
        return False

    @classmethod
    def _get_fallback_font(cls, size):
        # EN: Get a reliable fallback font (Garamond)
        # CN: 获取一个可靠的备用字体 (Garamond)
        if size in cls._fallback_cache:
            return cls._fallback_cache[size]
        
        # EN: Defaulting to the built-in Garamond for fallback symbols
        fallback_path = cls._resolve_font_path("assets/fonts/gara.ttf")
        try:
            f = ImageFont.truetype(fallback_path, size)
            cls._fallback_cache[size] = f
            return f
        except:
            return ImageFont.load_default()

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
        # EN: Handle None or empty / CN: 强力处理空值
        if not font_path or not isinstance(font_path, str):
            return None
            
        # EN: Convert relative path to absolute path for EXE support
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
        
        # EN: Guard against None path / CN: 防止空路径导致崩溃
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
                widths = []
                # EN: Resolve character widths with fallback awareness
                fallback_pil = cls._get_fallback_font(font_size)
                
                for c in chars:
                    if cls._has_glyph(ttfont, c):
                        widths.append(draw.textlength(c, font=pil_font))
                    else:
                        widths.append(draw.textlength(c, font=fallback_pil))

                offsets = [0] * len(chars)
                if ttfont:
                    for i in range(len(chars) - 1):
                        # EN: Only calculate kening if both characters are in the font
                        if cls._has_glyph(ttfont, chars[i]) and cls._has_glyph(ttfont, chars[i+1]):
                            offsets[i+1] = cls.get_kerning_offset(ttfont, chars[i], chars[i+1], font_size)
                
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
                    # EN: Defensive check for indexing / CN: 越界容错检查
                    off = offsets[i] if i < len(offsets) else 0
                    
                    # EN: Determine which font to use for this specific character
                    target_font = pil_font
                    if not cls._has_glyph(ttfont, char):
                        target_font = cls._get_fallback_font(font_size)
                    
                    cw = char_widths[i] if i < len(char_widths) else draw.textlength(char, font=target_font)
                    
                    # EN: Draw text with true center anchor
                    # CN: 使用真实的中心锚点进行绘制，确保在窄边框内绝对居中
                    draw.text((curr_x, base_y), char, font=target_font, fill=colors[i], anchor="lm")
                    curr_x += cw
            elif seg["type"] == "image":
                # EN: Paste image token / CN: 粘贴图片 Token
                img = seg["img"]
                # EN: Vertical alignment - anchor="lm" equivalent for images
                # CN: 垂直对齐 - 图片的等效 "lm" 居中
                paste_y = int(base_y - img.height // 2)
                draw._image.paste(img, (int(curr_x), paste_y), img)
                curr_x += seg["width"]
        
        timings[f'{key_prefix}_total'] = time.perf_counter() - t0
    @classmethod
    def draw_png_text(cls, text, font_dir, spacing_ratio=0.25, color=(255, 255, 255)):
        """
        EN: Render text using PNG characters with fully proportional layout.
        CN: 使用 PNG 字符进行渲染，支持全比例布局（间距与高度挂钩）。
        """
        font_dir = cls._resolve_font_path(font_dir)
        descenders = set("gjpqy")
        superscripts = set("*'\"")
        
        # EN: 1. Get Reference Height / CN: 1. 获取参考高度
        ref_file = os.path.join(font_dir, "1050-0.png")
        ref_h = 40
        if os.path.exists(ref_file):
            with Image.open(ref_file) as ri:
                bbox = ri.getbbox()
                ref_h = bbox[3] - bbox[1] if bbox else ri.height
                
        # EN: Calculate Relative Spacing / CN: 计算相对间距
        spacing = int(ref_h * spacing_ratio)
        
        processed_items = []
        total_w = 0
        
        for char in text:
            if char == " ":
                w = int(ref_h * 0.5) 
                processed_items.append({"img": None, "type": "space", "w": w})
                total_w += w + spacing
                continue
                
            filename = None
            if char.isdigit(): filename = f"1050-{char}.png"
            elif char.isupper(): filename = f"1050-{char}-capital.png"
            elif char.islower(): filename = f"1050-{char.upper()}.png"
            elif char == "/": filename = "1050-U+002F.png"
            elif char == "|": filename = "1050-U+007C.png"
            elif char == ".": filename = "1050-U+002E.png"
            elif char == "*": filename = "1050-U+002A.png"
            
            path = os.path.join(font_dir, filename) if filename else None
            if path and os.path.exists(path):
                try:
                    img = Image.open(path).convert('RGBA')
                    
                    # EN: Color Tint (preserving alpha)
                    r, g, b, a = img.split()
                    img = Image.merge("RGBA", (
                        Image.new("L", img.size, color[0]),
                        Image.new("L", img.size, color[1]),
                        Image.new("L", img.size, color[2]),
                        a
                    ))
                    
                    # EN: Auto-Crop
                    bbox = img.getbbox()
                    if bbox: img = img.crop(bbox)
                    
                    char_type = "standard"
                    if char in descenders: char_type = "descender"
                    elif char.islower() and char not in "bdfhklit": char_type = "small"
                    elif char in superscripts: char_type = "superscript"
                        
                    processed_items.append({"img": img, "type": char_type, "w": img.width, "h": img.height})
                    total_w += img.width + spacing
                except:
                    processed_items.append({"img": None, "type": "error", "w": 0})
            else:
                processed_items.append({"img": None, "type": "missing", "w": 0})

        # EN: 2. Layout (Relative Ratios) / CN: 2. 布局（相对比例）
        canvas_h = int(ref_h * 1.5)
        baseline = int(ref_h * 1.2)
        result = Image.new('RGBA', (total_w, canvas_h), (0, 0, 0, 0))
        
        x_cursor = 0
        for item in processed_items:
            img = item.get("img")
            if img:
                t = item["type"]
                if t == "descender":
                    y_pos = baseline - int(img.height * 0.75) 
                elif t == "superscript":
                    y_pos = baseline - ref_h + int(ref_h * 0.05)
                else:
                    y_pos = baseline - img.height
                
                result.paste(img, (x_cursor, y_pos), mask=img)
                x_cursor += item["w"] + spacing
            else:
                x_cursor += item.get("w", 0) + spacing
                
        return result
