import os
import re
from ..utils.path import resolve_path

class LensParser:
    """
    EN: Responsible for parsing lens model strings and identifying special branding markers.
    CN: 负责解析镜头型号字符串并识别特殊的品牌标识（如 Zeiss T*, Sony GM, Canon L 等）。
    """
    
    @staticmethod
    def prepare_segments(data, sub_color, use_lens_branding=True):
        """
        EN: Parses lens data into styled segments (text + tokens).
        CN: 将镜头数据解析为带样式的片段（文本 + 图标）。
        """
        lens = str(data.get('LensModel') or "").strip()
        make = str(data.get('Make') or "").strip().upper()
        is_digi = data.get('is_digital', False)
        
        # EN: Handle visibility toggles / CN: 处理显示开关
        show_lens = data.get('show_lens', 1)
        show_aperture = data.get('show_aperture', 1)
        show_shutter = data.get('show_shutter', 1)
        show_iso = data.get('show_iso', 1)
        show_focal = data.get('show_focal', 1)

        if not show_lens:
            lens = ""

        # EN: Basic info parts / CN: 基础信息部分
        info_parts = []
        
        focal = data.get('FocalLength')
        if is_digi and focal and show_focal: info_parts.append(focal)
        
        aperture = data.get('FNumber')
        if aperture and show_aperture: info_parts.append(f"f/{aperture}")
        
        shutter = data.get('ExposureTimeStr')
        if shutter and show_shutter: info_parts.append(f"{shutter}s")
        
        iso = data.get('ISO')
        if is_digi and iso and show_iso: info_parts.append(f"ISO {iso}")
        
        if not is_digi:
            film_name = str(data.get('Film') or "").upper()
            if film_name: info_parts.append(film_name)
        
        base_info = "  |  ".join(info_parts)
        
        segments = []
        
        # EN: Early return if branding is disabled / CN: 如果禁用标识则提前返回
        if not use_lens_branding:
            separator = "  |  " if (lens and base_info) else ""
            segments.append({"type": "text", "content": lens + separator + base_info, "color": sub_color})
            return segments

        # --- EN: Brand Specific Logic (Ported from v2.4.0 main) / CN: 品牌特定逻辑（同步自 main 分支） ---
        
        # 1. CANON L (Red L)
        if "CANON" in make:
            match = re.search(r'(?<![a-zA-Z])L(?![a-zA-Z])', lens)
            if match:
                start, end = match.span()
                segments.append({"type": "text", "content": lens[:start].strip(), "color": sub_color})
                segments.append({"type": "text", "content": "L", "color": (196, 30, 58)}) # Pantone 186 C
                # EN: Add trailing text and base info with proper separator
                trailing = lens[end:].strip()
                separator = "  |  " if (trailing or base_info) else ""
                segments.append({"type": "text", "content": trailing + separator + base_info, "color": sub_color})
                return segments

        # 2. NIKON GOLD (Gold N)
        if "NIKON" in make:
            match = re.search(r'(?<![a-zA-Z])N(?![a-zA-Z])', lens, re.IGNORECASE)
            if match:
                start, end = match.span()
                segments.append({"type": "text", "content": lens[:start].strip(), "color": sub_color})
                segments.append({"type": "text", "content": lens[start:end], "color": (172, 147, 78)}) # Brighter Pantone 871 C
                trailing = lens[end:].strip()
                separator = "  |  " if (trailing or base_info) else ""
                segments.append({"type": "text", "content": trailing + separator + base_info, "color": sub_color})
                return segments

        # 3. SONY GM (Token)
        if "SONY" in make:
            if re.search(r'\bGM\b', lens.upper()):
                token_path = resolve_path(os.path.join("assets", "lenses", "SONY-GM.png"))
                if os.path.exists(token_path):
                    clean_lens = re.sub(r'\bGM\b', '', lens, flags=re.IGNORECASE).strip()
                    if clean_lens:
                        segments.append({"type": "text", "content": clean_lens + " ", "color": sub_color})
                    segments.append({"type": "image", "path": token_path})
                    if base_info:
                        segments.append({"type": "text", "content": "  |  " + base_info, "color": sub_color})
                    return segments

        # 4. SIGMA (Art/S/C Token)
        keywords_art = ["ART", "| A", "(A)"]
        keywords_sport = ["SPORT", "| S", "(S)"]
        keywords_contemp = ["CONTEMP", "| C", "(C)"]
        
        upper_lens = lens.upper()
        token_file = None
        if any(k in upper_lens for k in keywords_art):
            token_file = "SIGMA-ART.png"
        elif any(k in upper_lens for k in keywords_sport):
            token_file = "SIGMA-SPORTS.png"
        elif any(k in upper_lens for k in keywords_contemp):
            token_file = "SIGMA-CONTEMPORARY.png"
        
        if token_file:
            token_path = resolve_path(os.path.join("assets", "lenses", token_file))
            if os.path.exists(token_path):
                all_k = ["ART", "SPORTS", "SPORT", "CONTEMPORARY", "CONTEMP"]
                pattern = r'\b(?:' + r'|'.join([re.escape(k) for k in all_k]) + r')\b|\|\s*[ASC]\b|\([ASC]\)'
                clean_lens = re.sub(pattern, '', lens, flags=re.IGNORECASE)
                clean_lens = re.sub(r'\|\s*$', '', clean_lens.strip()).strip()
                clean_lens = re.sub(r'\s{2,}', ' ', clean_lens)
                
                if clean_lens:
                    segments.append({"type": "text", "content": clean_lens + " ", "color": sub_color})
                segments.append({"type": "image", "path": token_path})
                if base_info:
                    segments.append({"type": "text", "content": "  |  " + base_info, "color": sub_color})
                return segments

        # 5. ZEISS T* (Red T*)
        separator = "  |  " if (lens and base_info) else ""
        full_text = lens + separator + base_info
        if "T*" in full_text:
            segments.append({"type": "text", "content": full_text, "color": LensParser._get_zeiss_colors(full_text, sub_color)})
            return segments

        # EN: Default Fallback / CN: 默认回退
        segments.append({"type": "text", "content": full_text, "color": sub_color})
        return segments

    @staticmethod
    def _get_zeiss_colors(text, base_color):
        colors = [base_color] * len(text)
        zeiss_red = (237, 31, 37)
        i = 0
        while i < len(text) - 1:
            if text[i:i+2] == "T*":
                colors[i] = zeiss_red
                colors[i+1] = zeiss_red
                i += 2
            else:
                i += 1
        return colors

    @staticmethod
    def format_display_strings(data):
        """
        EN: Generate main and sub display strings based on metadata.
        CN: 根据元数据生成主标题和副标题显示字符串。
        """
        show_make = data.get('show_make', 1)
        show_model = data.get('show_model', 1)
        make = str(data.get('Make') or "").strip().upper() if show_make else ""
        model = str(data.get('Model') or "").strip().upper() if show_model else ""
        
        # EN: De-duplicate Make from Model / CN: 从型号中去重品牌名
        dedup_model = model
        if make and model and model.startswith(make):
            dedup_model = model[len(make):].lstrip(" -_/") or model
            
        main_text = f"{make} {dedup_model}".strip() if make and dedup_model else (dedup_model or make)
        if "HASSELBLAD" in make: 
            main_text = f"HASSELBLAD {dedup_model or model or make}".strip()
            
        # EN: Sub-text generation / CN: 副标题字符串生成
        sub_segments = LensParser.prepare_segments(data, (0,0,0))
        sub_text = "".join([s["content"] for s in sub_segments if s["type"] == "text"])
        
        return main_text, sub_text
