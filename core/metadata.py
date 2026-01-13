# core/metadata.py
import os
import json
import exifread
from fractions import Fraction
from PIL import Image

class MetadataHandler:
    def __init__(self, layout_config='layouts.json', films_config='films.json', contact_config='contact_layouts.json'):
        """
        EN: Strictly preserved original logic with added EdgeCode/Color mapping.
        CN: 中英双语：严格保留原始逻辑，仅添加 EdgeCode/Color 映射。
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        layout_path = os.path.join(project_root, 'config', layout_config)
        films_path = os.path.join(project_root, 'config', films_config)
        contact_path = os.path.join(project_root, 'config', contact_config)

        if not all(os.path.exists(p) for p in [layout_path, films_path, contact_path]):
            raise FileNotFoundError(f"CN: 配置文件缺失! 请检查 config/ 文件夹。")

        with open(layout_path, 'r', encoding='utf-8') as f:
            self.layout_db = json.load(f)
        with open(films_path, 'r', encoding='utf-8') as f:
            raw_films = json.load(f)
        with open(contact_path, 'r', encoding='utf-8') as f:
            self.contact_db = json.load(f)

        self.films_map = {}
        self.edge_code_map = {} 
        self.marking_color_map = {} 

        for brand, models in raw_films.items():
            for model_name, content in models.items():
                full_display_name = f"{brand} {model_name}"
                if isinstance(content, dict):
                    aliases = content.get("features", [])
                    self.edge_code_map[full_display_name] = content.get("edge_code", model_name.upper())
                    self.marking_color_map[full_display_name] = content.get("visual", {}).get("color", [245, 130, 35, 210])
                else:
                    aliases = content 
                
                self.films_map[model_name.upper()] = full_display_name
                for alias in aliases:
                    self.films_map[alias.upper()] = full_display_name

        self.sorted_film_keys = sorted(self.films_map.keys(), key=len, reverse=True)

    def match_film(self, raw_input):
        if not raw_input: return ""
        q = str(raw_input).strip().upper()
        for key in self.sorted_film_keys:
            if key in q: return self.films_map[key]
        return q

    def get_contact_layout(self, layout_name):
        return self.contact_db.get(layout_name, self.contact_db.get("135"))
    
    def detect_batch_layout(self, img_paths):
        """
        EN: Detect format key based on image count and aspect ratio.
        CN: 中英双语：根据图片数量和长宽比自动探测画幅 Key。
        """
        if not img_paths: return "66"
        count = len(img_paths)
        with Image.open(img_paths[0]) as img:
            w, h = img.size
            ratio = max(w, h) / min(w, h)

        if count > 20: return "135"
        if count > 12: return "645"
        if 11 <= count <= 12: return "66"
        
        if ratio < 1.35: return "67"
        if ratio < 1.55: return "68"
        if ratio < 1.85: return "69"
        if ratio < 2.5: return "612"
        return "617"

    def get_data(self, img_path, is_digital_mode=False):
        """
        EN: Extract metadata. FocalLength is now universally extracted.
        CN: 中英双语：提取元数据。焦距信息现在在所有模式下均会提取。
        """
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # 1. EN: Date/Time / CN: 提取日期时间
        dt_raw = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
        dt_str = str(dt_raw).strip() if dt_raw else ""

        # 2. EN: Hardware / CN: 提取硬件信息
        make = str(tags.get('Image Make', 'Unknown')).strip()
        model = str(tags.get('Image Model', 'Unknown')).strip()
        lens = str(tags.get('EXIF LensModel', 
                   tags.get('MakerNote LensModel', 
                   tags.get('EXIF LensSpecification', '')))).strip()

        # 3. EN: Exposure / CN: 提取曝光参数
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

        # --- EN: Focal Length Extraction (Universal) / CN: 焦距提取 (通用) ---
        focal_str = ""
        focal_val = tags.get('EXIF FocalLength')
        if focal_val:
            f_num = focal_val.values[0]
            f_res = float(f_num.numerator) / float(f_num.denominator)
            focal_str = f"{int(f_res)}mm"

        iso_str = ""; display_film = ""
        edge_code = "SAFETY FILM"; contact_color = (245, 130, 35, 210)

        if is_digital_mode:
            iso_val = tags.get('EXIF ISOSpeedRatings')
            iso_str = str(iso_val.values[0]) if iso_val else ""
        else:
            film_raw = (tags.get('Image ImageDescription') or 
                        tags.get('EXIF ImageDescription') or 
                        tags.get('EXIF UserComment') or "")
            raw_desc = str(film_raw.values if hasattr(film_raw, 'values') else film_raw).strip()
            display_film = self.match_film(raw_desc)
            if display_film in self.edge_code_map:
                edge_code = self.edge_code_map[display_film]
                contact_color = tuple(self.marking_color_map[display_film])

        with Image.open(img_path) as img:
            w, h = img.size
        ratio = max(w, h) / min(w, h)
        is_portrait = h > w
        layout_params = {"name": "CUSTOM", "side": 0.04, "bottom": 0.13, "font_scale": 0.032, "is_portrait": is_portrait}
        
        for name, cfg in self.layout_db.items():
            r_min, r_max = cfg['aspect_range']
            if (r_min - 0.01) <= ratio <= (r_max + 0.01):
                params = cfg.get("portrait" if is_portrait else "landscape", cfg.get("all"))
                layout_params = {
                    "name": name, "side": params['side_ratio'], "bottom": params['bottom_ratio'],
                    "font_scale": params.get('font_scale', 0.032), "is_portrait": is_portrait
                }
                break

        return {
            'Make': make, 'Model': model, 'LensModel': lens,
            'ExposureTimeStr': shutter_str, 'FNumber': aperture_str,
            'ISO': iso_str, 'FocalLength': focal_str,
            'DateTime': dt_str,
            'Film': display_film,
            'EdgeCode': edge_code,
            'ContactColor': contact_color,
            'is_digital': is_digital_mode,
            'layout': layout_params
        }