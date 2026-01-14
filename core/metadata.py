# core/metadata.py
import os
import json
import exifread
from fractions import Fraction
from PIL import Image

class MetadataHandler:
    def __init__(self, layout_config='layouts.json', films_config='films.json', contact_config='contact_layouts.json'):
        """
        EN: Refined MetadataHandler - Strictly preserves structure, fixes keyword matching.
        CN: 核心逻辑修复版：严格保留结构，修复关键字匹配路径。
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        layout_path = os.path.join(project_root, 'config', layout_config)
        films_path = os.path.join(project_root, 'config', films_config)
        contact_path = os.path.join(project_root, 'config', contact_config)

        with open(layout_path, 'r', encoding='utf-8') as f:
            self.layout_db = json.load(f)
        with open(films_path, 'r', encoding='utf-8') as f:
            self.films_map = json.load(f)
        with open(contact_path, 'r', encoding='utf-8') as f:
            self.contact_layouts = json.load(f)

        # --- [必要修改 1/3] CN: 拍平特征映射表，用于 match_film ---
        self.edge_code_map = {}
        self.marking_color_map = {}
        self.feature_to_std = {} 

        for brand, films in self.films_map.items():
            for std_name, info in films.items():
                self.edge_code_map[std_name] = info.get('edge_code', std_name.upper())
                self.marking_color_map[std_name] = info.get('visual', {}).get('edge_marking_color', [245, 130, 35, 210])
                
                # 建立特征关键字搜索 (标准名 + features 列表)
                self.feature_to_std[std_name.upper()] = std_name
                for feat in info.get('features', []):
                    self.feature_to_std[feat.upper()] = std_name

        self.sorted_features = sorted(self.feature_to_std.keys(), key=len, reverse=True)

    def match_film(self, raw_input):
        """
        CN: 修正后的匹配逻辑，现在可以搜到 p400 等缩写。
        """
        if not raw_input: return ""
        q = str(raw_input).strip().upper()
        for feat in self.sorted_features:
            if feat in q:
                return self.feature_to_std[feat]
        return raw_input # 没搜到则返回原样

    def get_data(self, img_path, is_digital_mode=False, manual_film=None):
        """
        CN: 核心数据提取逻辑。
        [必要修改 2/3] 增加 manual_film 参数默认值，确保 Renderer66/67 等调用不报错。
        """
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # --- 基础 EXIF 提取逻辑 (完全保留，不改动任何变量名) ---
        make = str(tags.get('Image Make', 'Unknown'))
        model = str(tags.get('Image Model', 'Unknown'))
        lens = str(tags.get('EXIF LensModel', 'Unknown Lens'))
        f_num = tags.get('EXIF FNumber')
        aperture_str = str(float(f_num.values[0]) if f_num else "--")
        expo = tags.get('EXIF ExposureTime')
        shutter_str = str(expo.values[0]) if expo else "--"
        focal = tags.get('EXIF FocalLength')
        focal_val = float(focal.values[0].num) / float(focal.values[0].den) if focal else 0
        focal_str = f"{int(focal_val)}mm" if focal_val > 0 else "--mm"
        dt = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
        dt_str = str(dt.values) if dt else ""
        iso = tags.get('EXIF ISOSpeedRatings')
        iso_str = str(iso.values[0]) if iso else ""

        # --- [必要修改 3/3] CN: 优先逻辑实现 ---
        display_film = ""
        if not is_digital_mode:
            # A. 优先尝试自动识别
            film_raw = (tags.get('Image ImageDescription') or tags.get('EXIF UserComment') or "")
            raw_desc = str(film_raw.values if hasattr(film_raw, 'values') else film_raw).strip()
            auto_matched = self.match_film(raw_desc)
            
            # B. 自动优先决策
            if auto_matched:
                display_film = auto_matched
            elif manual_film:
                display_film = manual_film # 自动识别不到时，才用手动传入的

        # 挂载喷码和颜色 (Renderer135/66/67 都会用到这些字段)
        edge_code = self.edge_code_map.get(display_film, display_film.upper() if display_film else "SAFETY FILM")
        contact_color = tuple(self.marking_color_map.get(display_film, [245, 130, 35, 210]))

        # --- 布局参数计算 (完全保留) ---
        with Image.open(img_path) as img: w, h = img.size
        ratio = max(w, h) / min(w, h)
        is_portrait = h > w
        layout_params = {"name": "CUSTOM", "side": 0.04, "bottom": 0.13, "font_scale": 0.032, "is_portrait": is_portrait}
        for name, cfg in self.layout_db.items():
            r_min, r_max = cfg['aspect_range']
            if (r_min - 0.01) <= ratio <= (r_max + 0.01):
                params = cfg.get("portrait" if is_portrait else "landscape", cfg.get("all"))
                layout_params = {"name": name, "side": params['side_ratio'], "bottom": params['bottom_ratio'], 
                                "font_scale": params.get('font_scale', 0.032), "is_portrait": is_portrait}
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

    def detect_batch_layout(self, img_paths):
        with Image.open(img_paths[0]) as img: w, h = img.size
        ratio = max(w, h) / min(w, h)
        if 0.95 <= ratio <= 1.05: return "66"
        if 1.2 <= ratio <= 1.4: return "645"
        if 1.4 <= ratio <= 1.6: return "135"
        if 1.1 <= ratio <= 1.2: return "67"
        return "135"

    def get_contact_layout(self, key):
        return self.contact_layouts.get(key, self.contact_layouts["135"])