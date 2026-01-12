# core/metadata.py
import os
import json
import exifread
from fractions import Fraction
from PIL import Image

class MetadataHandler:
    def __init__(self, layout_config='layouts.json', films_config='films.json', contact_config='contact_layouts.json'):
        """
        EN: Refined path logic and multi-config loading for borders and contact sheets.
        CN: 中英双语：重排路径逻辑，支持边框与底片索引的多配置文件加载。
        """
        # EN: Get project root from core/ directory / CN: 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # EN: Define absolute paths / CN: 定义配置文件的绝对路径
        layout_path = os.path.join(project_root, 'config', layout_config)
        films_path = os.path.join(project_root, 'config', films_config)
        contact_path = os.path.join(project_root, 'config', contact_config)

        # EN: Basic error checking / CN: 基础错误检查
        if not all(os.path.exists(p) for p in [layout_path, films_path, contact_path]):
            raise FileNotFoundError(f"CN: 配置文件缺失! 请检查 config/ 文件夹。")

        # EN: Load configurations / CN: 加载配置文件
        with open(layout_path, 'r', encoding='utf-8') as f:
            self.layout_db = json.load(f)
        with open(films_path, 'r', encoding='utf-8') as f:
            raw_films = json.load(f)
        with open(contact_path, 'r', encoding='utf-8') as f:
            self.contact_db = json.load(f)

        # --- EN: Flatten film DB / CN: 拍平胶片库到标准映射表 ---
        self.films_map = {}
        for brand, models in raw_films.items():
            for model_name, aliases in models.items():
                full_display_name = f"{brand} {model_name}"
                self.films_map[model_name.upper()] = full_display_name
                for alias in aliases:
                    self.films_map[alias.upper()] = full_display_name

        self.sorted_film_keys = sorted(self.films_map.keys(), key=len, reverse=True)

    def match_film(self, raw_input):
        """
        EN: Standardize any film string (from EXIF or Manual Input).
        CN: 中英双语：标准化胶片名称的公共方法。
        """
        if not raw_input:
            return ""
        q = str(raw_input).strip().upper()
        for key in self.sorted_film_keys:
            if key in q:
                return self.films_map[key]
        return q

    def get_contact_layout(self, layout_name):
        """
        EN: Data Separation: Fetch contact sheet params from JSON.
        CN: 中英双语：数据分离：从 JSON 获取特定的底片索引排版参数。
        """
        # EN: Fallback to 135 if layout not found / CN: 若找不到画幅则回退至 135
        return self.contact_db.get(layout_name, self.contact_db.get("135"))

    def get_data(self, img_path, is_digital_mode=False):
        """
        EN: High-precision metadata extraction with layout matching.
        CN: 中英双语：具备布局匹配功能的高精度元数据提取。
        """
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # --- EN: BASIC EXIF / CN: 基础信息提取 ---
        make = str(tags.get('Image Make', 'Unknown')).strip()
        model = str(tags.get('Image Model', 'Unknown')).strip()
        lens = str(tags.get('EXIF LensModel', 
                   tags.get('MakerNote LensModel', 
                   tags.get('EXIF LensSpecification', '')))).strip()

        # EN: Exposure / CN: 曝光参数 (快门、光圈)
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

        # --- EN: MODE BASED DATA / CN: 胶片/数码分模式处理 ---
        iso_str = ""; focal_str = ""; display_film = ""

        if is_digital_mode:
            iso_val = tags.get('EXIF ISOSpeedRatings')
            iso_str = str(iso_val.values[0]) if iso_val else ""
            focal_val = tags.get('EXIF FocalLength')
            if focal_val:
                f_num = focal_val.values[0]
                focal_str = f"{int(float(f_num.numerator)/float(f_num.denominator))}mm"
        else:
            film_raw = (tags.get('Image ImageDescription') or 
                        tags.get('EXIF ImageDescription') or 
                        tags.get('EXIF UserComment') or "")
            raw_desc = str(film_raw.values if hasattr(film_raw, 'values') else film_raw).strip()
            display_film = self.match_film(raw_desc)

        # --- EN: LAYOUT RESOLUTION / CN: 比例与布局判定 ---
        with Image.open(img_path) as img:
            w, h = img.size
        
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