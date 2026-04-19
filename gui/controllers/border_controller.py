# gui/controllers/border_controller.py
"""
EN: Controller for border processing logic
CN: 边框处理逻辑控制器
"""

import os
import sys
import platform
import subprocess
import threading
from PIL import Image
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer, bootstrap_logos

class BorderController:
    """
    EN: Decoupled logic for batch image processing and state management
    CN: 用于批量图片处理和状态管理的解耦逻辑
    """
    def __init__(self, lang="en", log_callback=None, progress_callback=None, complete_callback=None, error_callback=None):
        self.lang = lang
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.complete_callback = complete_callback
        self.error_callback = error_callback
        self.stop_requested = False
        
        # State Management
        self.image_configs = {} # path -> params
        self.batch_width_cache = {} # normalized_path -> aspect_ratio
        self.current_batch_paths = [] # List of absolute paths
        self.input_folder = None
        
        # Load necessary singletons/handlers
        self.renderer = FilmRenderer()
        self.metadata_handler = MetadataHandler(layout_config='layouts.json', films_config='films.json')

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def request_stop(self):
        self.stop_requested = True

    # --- State & File Management ---

    def scan_folder(self, folder_path):
        """EN: Scan folder for images and update batch / CN: 扫描文件夹并更新批次"""
        if not folder_path or not os.path.exists(folder_path):
            return 0
            
        self.input_folder = folder_path
        valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.tiff')
        found_files = []
        for f in os.listdir(folder_path):
            if f.lower().endswith(valid_exts):
                found_files.append(os.path.join(folder_path, f))
        
        # EN: Use stable sort to maintain order / CN: 使用稳定排序保持顺序
        found_files.sort()
        self.current_batch_paths = [os.path.normcase(os.path.normpath(p)) for p in found_files]
        
        # EN: Scan images to cache aspect ratios in background
        # (This is usually handled by the Panel calling a specific method)
        return len(found_files)

    def update_batch_order(self, new_paths):
        """EN: Update current batch order / CN: 更新当前批次顺序"""
        self.current_batch_paths = new_paths

    def add_to_batch(self, paths):
        """EN: Add specific files to current batch / CN: 将特定文件添加到当前批次"""
        for p in paths:
            p_norm = os.path.normcase(os.path.normpath(p))
            if p_norm not in self.current_batch_paths:
                self.current_batch_paths.append(p_norm)
        return len(self.current_batch_paths)

    def remove_from_batch(self, path):
        """EN: Remove file from batch / CN: 从批次中移除文件"""
        p_norm = os.path.normcase(os.path.normpath(path))
        if p_norm in self.current_batch_paths:
            self.current_batch_paths.remove(p_norm)
        if p_norm in self.image_configs:
            del self.image_configs[p_norm]

    def update_image_config(self, path, params):
        """EN: Update config for a specific image / CN: 更新单张图片的配置"""
        p_norm = os.path.normcase(os.path.normpath(path))
        if params is None:
            if p_norm in self.image_configs:
                del self.image_configs[p_norm]
            return
            
        if p_norm not in self.image_configs:
            self.image_configs[p_norm] = {}
        self.image_configs[p_norm].update(params)

    def clear_all_configs(self):
        """EN: Clear all image configurations / CN: 清除所有图片配置"""
        self.image_configs = {}

    def get_image_config(self, path):
        """EN: Get config for image, fallback to empty / CN: 获取图片配置，无则返回空"""
        p_norm = os.path.normcase(os.path.normpath(path))
        return self.image_configs.get(p_norm, {})

    def sync_config_to_similar(self, source_path, params):
        """
        EN: Apply source params to all images in batch with same aspect ratio and rotation.
        CN: 将当前图片的配置应用到批次中具有相同宽高比和旋转角度的所有图片。
        """
        p_norm = os.path.normcase(os.path.normpath(source_path))
        source_ratio = self.batch_width_cache.get(p_norm)
        if source_ratio is None: return
        
        source_rotation = params.get('rotation', 0)
        
        # EN: Parameters to sync (exclude EXIF and path-specific stuff)
        # CN: 需要同步的参数（不含 EXIF 等特定信息）
        sync_keys = [
            'left_px', 'right_px', 'top_px', 'bottom_px', 
            'font_scale', 'font_sub_px', 'font_v_offset',
            'theme', 'branding', 'auto_detect', 'film_combo'
        ]
        sync_data = {k: params[k] for k in sync_keys if k in params}
        
        count = 0
        for path in self.current_batch_paths:
            if path == p_norm: continue
            
            target_ratio = self.batch_width_cache.get(path)
            if target_ratio is None: continue
            
            # EN: Match aspect ratio (tolerance 0.02) and rotation
            # CN: 匹配宽高比（容差 0.02）和旋转角度
            if abs(target_ratio - source_ratio) < 0.05: # EN: Slightly wider tolerance for same format / CN: 同画幅稍微放宽容差
                target_cfg = self.image_configs.get(path, {})
                target_rotation = target_cfg.get('rotation', 0)
                
                if target_rotation == source_rotation:
                    if path not in self.image_configs:
                        self.image_configs[path] = {}
                    self.image_configs[path].update(sync_data)
                    count += 1
        return count

    def update_aspect_ratio_cache(self, path, ratio):
        """EN: Cache aspect ratio for an image / CN: 缓存图片的宽高比"""
        norm_p = os.path.normcase(os.path.normpath(path))
        self.batch_width_cache[norm_p] = ratio

    # --- Processing Logic ---

    def run_batch(self, output_dir, global_cfg, film_list):
        """
        EN: Main batch processing loop using internal state
        CN: 使用内部状态的主批量处理循环
        """
        self.stop_requested = False
        files = self.current_batch_paths
        total = len(files)
        
        if total == 0:
            self.log("CN: [!] 队列内未找到待处理图片" if self.lang=="zh" else "EN: [!] No images in queue")
            return

        try:
            # EN: Pre-calculate total relative width for physical slice (Rainbow/Macaron)
            relative_widths = []
            total_rel_w = 0.0
            for img_path in files:
                p_norm = os.path.normcase(os.path.normpath(img_path))
                rel_w = self.batch_width_cache.get(p_norm)
                if rel_w is None:
                    try:
                        with Image.open(img_path) as img:
                            w, h = img.size
                            rel_w = w / h
                    except:
                        rel_w = 1.6
                relative_widths.append(rel_w)
                total_rel_w += rel_w

            current_w_accum = 0.0
            
            for i, img_path in enumerate(files):
                if self.stop_requested:
                    self.log("\n⚡ 用户手动终止处理" if self.lang == "zh" else "\n⚡ User canceled processing")
                    break

                t_start = current_w_accum / total_rel_w
                current_w_accum += relative_widths[i]
                t_end = current_w_accum / total_rel_w

                if self.progress_callback:
                    self.progress_callback(i + 1, total, os.path.basename(img_path))

                # EN: Resolve configuration
                p_norm = os.path.normcase(os.path.normpath(img_path))
                cfg = self.image_configs.get(p_norm, {})
                is_digital = global_cfg.get('is_digital', False)
                is_pure = global_cfg.get('is_pure', False)
                theme_str = cfg.get('theme', global_cfg.get('theme', 'light'))
                
                # EN: Resolve film
                m_film = global_cfg.get('manual_film')
                if cfg and not cfg.get('auto_detect', True):
                    m_film = cfg.get('film_combo')
                
                # EN: Resolve keyword from display name
                for display_name, keyword in film_list:
                    if m_film == display_name:
                        m_film = keyword
                        break

                # EN: Resolve metadata
                data = self.metadata_handler.get_data(img_path, is_digital_mode=is_digital, manual_film=m_film)
                
                # EN: Apply overrides
                layout_cfg = cfg if cfg else global_cfg.get('layout', {})
                # EN: Convert pixels to ratios based on 4500px reference
                # CN: 基于 4500px 基准将像素转换为比例
                ref = 4500.0
                data['layout'].update({
                    "left": layout_cfg.get('left_px', 180) / ref,
                    "right": layout_cfg.get('right_px', 180) / ref,
                    "top": layout_cfg.get('top_px', 180) / ref,
                    "bottom": layout_cfg.get('bottom_px', 585) / ref,
                    "font_main_scale": layout_cfg.get('font_scale', 144) / ref,
                    "font_sub_scale": layout_cfg.get('font_sub_px', 112) / ref,
                    "font_v_offset": layout_cfg.get('font_v_offset', 0) / ref
                })
                
                exif_cfg = cfg.get('exif') if cfg else global_cfg.get('exif')
                if exif_cfg:
                    for k, v in exif_cfg.items():
                        if v is not None and v != "":
                            key = k if k != 'Lens' else 'LensModel'
                            key = key if key != 'Shutter' else 'ExposureTimeStr'
                            key = key if key != 'Aperture' else 'FNumber'
                            data[key] = v

                # EN: Theme mapping
                theme_val = self.resolve_theme(theme_str)
                r_range = (t_start, t_end)
                r_idx = i % 9 
                
                out_prefix = ""
                if theme_val in ["macaron", "rainbow", "sakura"]:
                    out_prefix = f"{i+1:03d}_"

                # EN: Render (Unpack tuple to avoid error)
                _, _ = self.renderer.process_image(img_path, data, output_dir, 
                                     manual_rotation=cfg.get('rotation', global_cfg.get('rotation', 0)),
                                     theme=theme_val,
                                     is_pure=is_pure,
                                     use_lens_branding=global_cfg.get('use_branding', True),
                                     rainbow_index=r_idx,
                                     rainbow_total=total,
                                     rainbow_range=r_range,
                                     output_prefix=out_prefix)

            if self.complete_callback:
                self.complete_callback({'success': True, 'processed': total if not self.stop_requested else i})
                
        except Exception as e:
            import traceback
            if self.error_callback:
                self.error_callback(traceback.format_exc())

    def get_preview_image(self, img_path, is_digital, is_pure, manual_film, rotation, use_branding=True):
        """
        EN: Generate a preview image using internal and passed state
        CN: 使用内部和传入状态生成预览图
        """
        import time
        t_start = time.perf_counter()
        render_timings = {}
        
        p_norm = os.path.normcase(os.path.normpath(img_path))
        cfg = self.image_configs.get(p_norm, {})
        m_film = manual_film
        if cfg and not cfg.get('auto_detect', True):
            m_film = cfg.get('film_combo')
            
        data = self.metadata_handler.get_data(img_path, is_digital_mode=is_digital, manual_film=m_film)
        t_meta = time.perf_counter() - t_start

        layout_cfg = cfg if cfg else {
            "left_px": 180, "right_px": 180, "top_px": 180, "bottom_px": 585, 
            "font_scale": 144, "font_sub_px": 112, "font_v_offset": 0
        }
        ref = 4500.0
        data['layout'].update({
            "left": layout_cfg.get('left_px', 180) / ref,
            "right": layout_cfg.get('right_px', 180) / ref,
            "top": layout_cfg.get('top_px', 180) / ref,
            "bottom": layout_cfg.get('bottom_px', 585) / ref,
            "font_main_scale": layout_cfg.get('font_scale', 144) / ref,
            "font_sub_scale": layout_cfg.get('font_sub_px', 112) / ref,
            "font_v_offset": layout_cfg.get('font_v_offset', 0) / ref
        })
        
        exif_cfg = cfg.get('exif')
        if exif_cfg:
            for k, v in exif_cfg.items():
                if v is not None and v != "":
                    key = k if k != 'Lens' else 'LensModel'
                    key = key if key != 'Shutter' else 'ExposureTimeStr'
                    key = key if key != 'Aperture' else 'FNumber'
                    data[key] = v

        theme_str = cfg.get('theme', 'light')
        theme_val = self.resolve_theme(theme_str)

        r_index = 0
        r_total = 1
        r_range = (0.0, 1.0)
        
        if theme_val in ["macaron", "rainbow", "sakura"] and self.current_batch_paths:
            r_total = len(self.current_batch_paths)
            norm_img_path = os.path.normcase(os.path.normpath(img_path))
            
            for idx, p in enumerate(self.current_batch_paths):
                if os.path.normcase(os.path.normpath(p)) == norm_img_path:
                    r_index = idx % 9
                    break
            
            total_rel_w = sum(self.batch_width_cache.get(os.path.normcase(os.path.normpath(p)), 1.6) for p in self.current_batch_paths)
            curr_accum = 0.0
            for p in self.current_batch_paths:
                p_norm = os.path.normcase(os.path.normpath(p))
                if p_norm == norm_img_path:
                    w = self.batch_width_cache.get(p_norm, 1.6)
                    r_range = (curr_accum / total_rel_w, (curr_accum + w) / total_rel_w)
                    break
                curr_accum += self.batch_width_cache.get(p_norm, 1.6)

        # EN: Render (Unpack tuple for info)
        final_pil, _ = self.renderer.process_image(img_path, data, None, 
                                         target_long_edge=1200, 
                                         manual_rotation=rotation,
                                         theme=theme_val,
                                         is_pure=is_pure,
                                         use_lens_branding=use_branding,
                                         rainbow_index=r_index,
                                         rainbow_total=r_total,
                                         rainbow_range=r_range,
                                         timing_results=render_timings)
        
        total_time = time.perf_counter() - t_start
        performance_report = {
            'total': total_time,
            'metadata': t_meta,
            'render_breakdown': render_timings
        }
        
        return final_pil, performance_report

    def resolve_theme(self, theme_str):
        """EN: Map localized theme name to internal key / CN: 将本地化主题名映射到内部键值"""
        t_map = {
            "sakura": "sakura", "樱花粉": "sakura", "Sakura": "sakura",
            "macaron": "macaron", "马卡龙": "macaron", "Macaron": "macaron",
            "rainbow": "rainbow", "彩虹": "rainbow", "Rainbow": "rainbow",
            "frosted": "frosted", "磨砂": "frosted", "glass": "frosted",
            "slate_teal": "slate_teal", "石板青": "slate_teal", "Slate Teal": "slate_teal",
            "dark": "dark", "深色": "dark", "Dark": "dark",
            "light": "light", "浅色": "light", "Light": "light", "Default": "light"
        }
        theme_str_lower = str(theme_str).lower()
        for k, v in t_map.items():
            if k.lower() in theme_str_lower:
                return v
        return "light"

    def detect_layout_from_folder(self, folder):
        """EN: Detect best layout match for folder / CN: 为文件夹检测最匹配的布局"""
        try:
            valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.tiff')
            files = [f for f in os.listdir(folder) if f.lower().endswith(valid_exts)]
            if not files: return None
            
            first_img = os.path.join(folder, files[0])
            with Image.open(first_img) as img:
                w, h = img.size
                aspect = w / h
                is_portrait = h > w
            
            layout_config = self.load_layout_config()
            best_match = "default"
            min_diff = float('inf')
            
            for name, cfg in layout_config.items():
                target_aspect = cfg.get('aspect_ratio', 1.5)
                diff = abs(aspect - target_aspect)
                if diff < min_diff:
                    min_diff, best_match = diff, name
            
            if min_diff < 0.1:
                match_cfg = layout_config[best_match]
                return match_cfg.get("portrait" if is_portrait else "landscape", match_cfg.get("all"))
        except: pass
        return None

    def load_layout_config(self):
        """EN: Load layout config from JSON / CN: 从JSON加载布局配置"""
        try:
            config_path = self.metadata_handler._resolve_config_path('layouts.json')
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def load_film_library(self):
        """EN: Load film library from config / CN: 从配置文件加载胶片库"""
        film_list = []
        try:
            if hasattr(self.metadata_handler, 'films_map'):
                for brand, films in self.metadata_handler.films_map.items():
                    for film_name in films.keys():
                        display_name = f"[{brand}] {film_name}"
                        film_list.append((display_name, film_name))
            film_list.sort()
        except:
            pass
        return film_list

    def get_asset_status_msg(self, film_list_len):
        """EN: Generate unified asset status message / CN: 生成统一的资产状态消息"""
        logo_count = 0
        try:
            logo_dir = bootstrap_logos()
            if os.path.exists(logo_dir):
                logo_count = len([f for f in os.listdir(logo_dir) if f.lower().endswith(('.svg', '.png'))])
        except: pass
        
        msg_film = f"CN: 已加载 {film_list_len} 种虚拟胶片资料 / EN: Loaded {film_list_len} film profiles"
        msg_logo = f"CN: 已同步 {logo_count} 款相机品牌图标 / EN: Synced {logo_count} camera logos"
        return f"{msg_film}\n{msg_logo}"
