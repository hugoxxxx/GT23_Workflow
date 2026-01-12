import os
import json
import exifread
from fractions import Fraction
from PIL import Image

class MetadataHandler:
    def __init__(self, layout_config='layouts.json', films_config='films.json'):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        with open(os.path.join(project_root, 'config', layout_config), 'r', encoding='utf-8') as f:
            self.layout_db = json.load(f)
        with open(os.path.join(project_root, 'config', films_config), 'r', encoding='utf-8') as f:
            raw_films = json.load(f)

        # --- EN: Flatten film DB to standard mapping / CN: 拍平胶片库到标准映射表 ---
        self.films_map = {}
        for brand, models in raw_films.items():
            for model_name, aliases in models.items():
                # EN: Standard display name / CN: 标准显示名 (例如: FUJIFILM Provia 100F)
                full_display_name = f"{brand} {model_name}"
                
                # EN: Match both the model name and all its aliases
                # CN: 匹配型号名本身及其所有别名
                self.films_map[model_name.upper()] = full_display_name
                for alias in aliases:
                    self.films_map[alias.upper()] = full_display_name

        # EN: Sort keys by length DESC / CN: 按长度倒序排列 Key
        # EN: This ensures "PROVIA 100F" is checked before "100"
        # CN: 确保 "PROVIA 100F" 在 "100" 这种短词之前被检查，防止截胡
        self.sorted_film_keys = sorted(self.films_map.keys(), key=len, reverse=True)

    def get_data(self, img_path, is_digital_mode=False):
        """
        EN: High-precision metadata extraction with manual mode override.
        CN: 中英双语：具备手动模式覆盖功能的高精度元数据提取。
        """
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # --- EN: BASIC EXIF / CN: 基础信息 ---
        make = str(tags.get('Image Make', 'Unknown')).strip()
        model = str(tags.get('Image Model', 'Unknown')).strip()
        lens = str(tags.get('EXIF LensModel', 
                   tags.get('MakerNote LensModel', 
                   tags.get('EXIF LensSpecification', '')))).strip()

        # EN: Exposure / CN: 曝光参数
        exposure_time = tags.get('EXIF ExposureTime')
        shutter_str = ""
        if exposure_time:
            val = exposure_time.values[0]
            shutter_str = str(Fraction(val).limit_denominator()) if val < 1 else str(val)

        f_number = tags.get('EXIF FNumber')
        aperture_str = ""
        if f_number:
            v = f_number.values[0]
            aperture_str = str(round(float(v.numerator) / float(v.denominator), 1))

        # --- EN: MODE BASED DATA / CN: 分模式数据处理 ---
        iso_str = ""; focal_str = ""; display_film = ""

        if is_digital_mode:
            # EN: Digital Mode: Capture ISO and Focal Length, FORCE film empty
            # CN: 数码模式：强制清空胶卷字段，抓取 ISO 和 焦距
            iso_val = tags.get('EXIF ISOSpeedRatings')
            iso_str = str(iso_val.values[0]) if iso_val else ""
            
            focal_val = tags.get('EXIF FocalLength')
            if focal_val:
                f_num = focal_val.values[0]
                focal_str = f"{int(float(f_num.numerator)/float(f_num.denominator))}mm"
            display_film = "" # EN: Ensure no "Unknown Film" / CN: 确保不会出现未知胶卷
        else:
            # --- EN: FILM STANDARDIZATION / CN: 胶片标准化逻辑 ---
            film_raw = (tags.get('Image ImageDescription') or 
                        tags.get('EXIF ImageDescription') or 
                        tags.get('EXIF UserComment') or "")
            raw_desc = str(film_raw.values if hasattr(film_raw, 'values') else film_raw).strip().upper()
            
            # EN: Fuzzy match with long-word priority / CN: 长词优先模糊匹配
            matched_key = ""
            for key in self.sorted_film_keys:
                if key in raw_desc:
                    matched_key = key
                    break
            
            if matched_key:
                display_film = self.films_map[matched_key]
            else:
                display_film = raw_desc

        # --- EN: LAYOUT RESOLUTION / CN: 布局匹配 ---
        with Image.open(img_path) as img:
            w, h = img.size
        
        # EN: Reuse your existing layout logic / CN: 复用画幅比对逻辑
        ratio = max(w, h) / min(w, h)
        is_portrait = h > w
        eps = 0.01
        layout_params = {"name": "CUSTOM", "side": 0.04, "bottom": 0.13, "font_scale": 0.032, "is_portrait": is_portrait}
        for name, cfg in self.layout_db.items():
            r_min, r_max = cfg['aspect_range']
            if (r_min - eps) <= ratio <= (r_max + eps):
                params = cfg['all'] if "all" in cfg else cfg.get("portrait" if is_portrait else "landscape")
                layout_params = {
                    "name": name, "side": params['side_ratio'], "bottom": params['bottom_ratio'],
                    "font_scale": params.get('font_scale', 0.032), "is_portrait": is_portrait
                }
                break

        return {
            'Make': make, 'Model': model, 'LensModel': lens,
            'ExposureTimeStr': shutter_str, 'FNumber': aperture_str,
            'ISO': iso_str, 'FocalLength': focal_str,
            'Film': display_film,
            'is_digital': is_digital_mode,
            'layout': layout_params
        }