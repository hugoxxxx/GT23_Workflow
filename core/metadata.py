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

        # --- [精准重构] 扁平化特征映射表：匹配即所得 ---
        # CN: 将 edge_code 和 color 直接绑定到特征词上，实现一次匹配全属性交付
        self.feature_db = {} 

        for brand, films in self.films_map.items():
            for std_name, info in films.items():
                # EN: Create an attribute bundle for each film
                # CN: 封装属性包：包含标准名、喷码和视觉颜色
                attr_bundle = {
                    "std_name": std_name,
                    "edge_code": info.get('edge_code', std_name.upper()),
                    "color": info.get('visual', {}).get('edge_marking_color', [245, 130, 35, 210])
                }
                
                # EN: Map std_name and features to the same bundle
                # CN: 建立特征索引：标准名 + 特征列表 (如 P400) 全指向同一个属性包
                self.feature_db[std_name.upper()] = attr_bundle
                for feat in info.get('features', []):
                    self.feature_db[feat.upper()] = attr_bundle

        # EN: Sort by length descending to prevent partial matching (e.g., 'Portra' vs 'Portra 400')
        # CN: 按长度倒序排列特征词，确保长词（如 PORTRA 400）优先于短词（如 PORTRA）被匹配
        self.sorted_features = sorted(self.feature_db.keys(), key=len, reverse=True)

    def match_film(self, raw_input):
        if not raw_input: return None
        q = str(raw_input).strip().upper()
        for feat in self.sorted_features:
            if feat in q:
                return self.feature_db[feat]["std_name"]
        return None
    
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
        aperture_str = str(float(f_num.values[0])) if f_num else None
        expo = tags.get('EXIF ExposureTime')
        shutter_str = str(expo.values[0]) if expo else None
        focal = tags.get('EXIF FocalLength')
        focal_val = float(focal.values[0].num) / float(focal.values[0].den) if focal else 0
        focal_str = f"{int(focal_val)}mm" if focal_val > 0 else None
        dt = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
        dt_str = str(dt.values) if dt else ""
        iso = tags.get('EXIF ISOSpeedRatings')
        iso_str = str(iso.values[0]) if iso else ""

        # --- [核心逻辑修复] 三级识别引擎 ---
        display_film = ""
        edge_code = "ahahahah！"
        contact_color = (245, 130, 35, 210)

        if not is_digital_mode:
            # 1. 自动扫描 (合并多个 Description 字段以体现专业性)
            d1 = str(tags.get('Image ImageDescription', ''))
            d2 = str(tags.get('EXIF UserComment', ''))
            d3 = str(tags.get('EXIF ImageDescription', '')) # 补充扫描位
            search_pool = f"{d1} {d2} {d3}".upper()
            
            # 2. 尝试自动识别
            auto_bundle = None
            for feat in self.sorted_features:
                if feat in search_pool:
                    auto_bundle = self.feature_db[feat]
                    break
            
            if auto_bundle:
                display_film = auto_bundle["std_name"]
                edge_code = auto_bundle["edge_code"]
                contact_color = tuple(auto_bundle["color"])
            
            # 3. 如果自动失败，使用手动输入并撞库
            elif manual_film:
                m_q = manual_film.upper().strip()
                manual_bundle = None
                for feat in self.sorted_features:
                    if feat == m_q or feat in m_q:
                        manual_bundle = self.feature_db[feat]
                        break
                
                if manual_bundle:
                    display_film = manual_bundle["std_name"]
                    edge_code = manual_bundle["edge_code"]
                    contact_color = tuple(manual_bundle["color"])
                else:
                    # 4. 彻底兜底：原样输出
                    display_film = manual_film
                    edge_code = manual_film.upper()
                    contact_color = (245, 130, 35, 210)

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