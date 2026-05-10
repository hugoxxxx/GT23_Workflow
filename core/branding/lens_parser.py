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
        if not lens:
            base_info = base_info.strip()
        
        segments = []
        
        # EN: Early return if branding is disabled / CN: 如果禁用标识则提前返回
        if not use_lens_branding:
            separator = "  |  " if (lens and base_info) else ""
            segments.append({"type": "text", "content": lens + separator + base_info, "color": sub_color})
            return segments

        # --- EN: Brand Specific Logic / CN: 品牌特定逻辑 ---
        
        # 1. CANON L (Red L)
        if "CANON" in make:
            match = re.search(r'(?<![a-zA-Z])L(?![a-zA-Z])', lens)
            if match:
                start, end = match.span()
                separator = "  |  " if (lens or base_info) else ""
                segments.append({"type": "text", "content": lens[:start], "color": sub_color})
                segments.append({"type": "text", "content": lens[start:end], "color": (196, 30, 58)}) # Pantone 186 C
                segments.append({"type": "text", "content": lens[end:] + (separator if lens[end:] or base_info else "") + base_info, "color": sub_color})
                return segments

        # 2. ZEISS T* (Red T*)
        if "T*" in lens:
            start = lens.find("T*")
            end = start + 2
            separator = "  |  " if (lens or base_info) else ""
            segments.append({"type": "text", "content": lens[:start], "color": sub_color})
            segments.append({"type": "text", "content": "T*", "color": (210, 15, 35)}) # Zeiss Red
            segments.append({"type": "text", "content": lens[end:] + (separator if lens[end:] or base_info else "") + base_info, "color": sub_color})
            return segments

        # 3. Badge Tokens (Sony GM, G, Sigma Art/C)
        token_file = None
        if " GM" in lens.upper() or " G MASTER" in lens.upper():
            token_file = "SONY-GM.png"
        elif " G" in lens.upper() and not " GM" in lens.upper():
            token_file = "SONY-G.png"
        elif "SIGMA" in lens.upper() and (" ART" in lens.upper() or " | A" in lens.upper()):
            token_file = "SIGMA-ART.png"
        elif "SIGMA" in lens.upper() and (" CONTEMPORARY" in lens.upper() or " | C" in lens.upper()):
            token_file = "SIGMA-CONTEMPORARY.png"
        
        separator = "  |  " if (lens and base_info) else ""
        segments.append({"type": "text", "content": lens + separator + base_info, "color": sub_color})
        
        if token_file:
            token_path = resolve_path(os.path.join("assets", "lenses", token_file))
            if os.path.exists(token_path):
                segments.append({"type": "image", "path": token_path})
                    
        return segments
