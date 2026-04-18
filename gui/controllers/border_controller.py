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
    EN: Decoupled logic for batch image processing
    CN: 用于批量图片处理的解耦逻辑
    """
    def __init__(self, lang="en", log_callback=None, progress_callback=None, complete_callback=None, error_callback=None):
        self.lang = lang
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.complete_callback = complete_callback
        self.error_callback = error_callback
        self.stop_requested = False
        
        # Load necessary singletons/handers
        self.renderer = FilmRenderer()
        self.metadata_handler = MetadataHandler(layout_config='layouts.json', films_config='films.json')

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def request_stop(self):
        self.stop_requested = True

    def run_batch(self, files, output_dir, global_cfg, image_configs, batch_width_cache, film_list):
        """
        EN: Main batch processing loop
        CN: 主批量处理循环
        """
        self.stop_requested = False
        total = len(files)
        
        if total == 0:
            self.log("CN: [!] 文件夹内未找到图片" if self.lang=="zh" else "EN: [!] No images found")
            return

        try:
            # EN: Pre-calculate total relative width for physical slice (Rainbow/Macaron)
            # CN: 预先计算总相对宽度，用于物理切片比例（彩虹/马卡龙）
            relative_widths = []
            total_rel_w = 0.0
            for img_path in files:
                p_norm = os.path.normcase(os.path.normpath(img_path))
                rel_w = batch_width_cache.get(p_norm)
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

                # EN: Progress feedback
                t_start = current_w_accum / total_rel_w
                current_w_accum += relative_widths[i]
                t_end = current_w_accum / total_rel_w

                if self.progress_callback:
                    self.progress_callback(i + 1, total, os.path.basename(img_path))

                # EN: Resolve configuration
                cfg = image_configs.get(img_path)
                is_digital = global_cfg['is_digital']
                is_pure = global_cfg['is_pure']
                theme_str = cfg.get('theme', global_cfg['theme']) if cfg else global_cfg['theme']
                
                # EN: Resolve film
                m_film = global_cfg['manual_film']
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
                c_layout = cfg if cfg else global_cfg['layout']
                data['layout'].update({
                    "side": c_layout.get('side_ratio', 0.04),
                    "top": c_layout.get('top_ratio', 0.04),
                    "bottom": c_layout.get('bottom_ratio', 0.13),
                    "font_scale": c_layout.get('font_scale', 0.032)
                })
                
                c_exif = cfg.get('exif') if cfg else global_cfg['exif']
                if c_exif:
                    for k, v in c_exif.items():
                        if v is not None and v != "":
                            key = k if k != 'Lens' else 'LensModel'
                            key = key if key != 'Shutter' else 'ExposureTimeStr'
                            key = key if key != 'Aperture' else 'FNumber'
                            data[key] = v

                # EN: Theme mapping
                theme_val = self.resolve_theme(theme_str)
                
                # EN: Batch positioning
                r_range = (t_start, t_end)
                r_idx = i % 9 # Position-based indexing for rainbow colors
                
                out_prefix = ""
                if theme_val in ["macaron", "rainbow", "sakura"]:
                    out_prefix = f"{i+1:03d}_"

                # EN: Render
                self.renderer.process_image(img_path, data, output_dir, 
                                     manual_rotation=cfg.get('rotation', global_cfg['rotation']) if cfg else global_cfg['rotation'],
                                     theme=theme_val,
                                     is_pure=is_pure,
                                     use_lens_branding=global_cfg['use_branding'],
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

    def get_preview_image(self, img_path, is_digital, is_pure, manual_film, rotation, image_configs, batch_width_cache, current_batch_paths, use_branding=True):
        """
        EN: Generate a preview image for the given path
        CN: 为给定路径生成预览图
        """
        import time
        t_start = time.perf_counter()
        render_timings = {}
        
        cfg = image_configs.get(img_path)
        
        # EN: Resolve film
        m_film = manual_film
        if cfg and not cfg.get('auto_detect', True):
            m_film = cfg.get('film_combo')
            
        # EN: Resolve keyword from display name
        # Note: film_list resolution should ideally be external or handled here
        # For simplicity, we assume m_film is already resolved or we pass film_list if needed
        # But let's look at how data is fetched
        data = self.metadata_handler.get_data(img_path, is_digital_mode=is_digital, manual_film=m_film)
        t_meta = time.perf_counter() - t_start

        # EN: Apply overrides
        c_layout = cfg if cfg else {
            "side_ratio": 0.04, "top_ratio": 0.04, "bottom_ratio": 0.13, "font_scale": 0.032
        }
        data['layout'].update({
            "side": c_layout.get('side_ratio', 0.04),
            "top": c_layout.get('top_ratio', 0.04),
            "bottom": c_layout.get('bottom_ratio', 0.13),
            "font_scale": c_layout.get('font_scale', 0.032)
        })
        
        c_exif = cfg.get('exif') if cfg else None
        if c_exif:
            for k, v in c_exif.items():
                if v is not None and v != "":
                    key = k if k != 'Lens' else 'LensModel'
                    key = key if key != 'Shutter' else 'ExposureTimeStr'
                    key = key if key != 'Aperture' else 'FNumber'
                    data[key] = v

        theme_str = cfg.get('theme', 'light') if cfg else 'light'
        theme_val = self.resolve_theme(theme_str)

        # EN: Position calculation for Rainbow/Macaron
        r_index = 0
        r_total = 1
        r_range = (0.0, 1.0)
        
        if theme_val in ["macaron", "rainbow", "sakura"] and current_batch_paths:
            r_total = len(current_batch_paths)
            norm_img_path = os.path.normcase(os.path.normpath(img_path))
            
            # Find index
            for idx, p in enumerate(current_batch_paths):
                if os.path.normcase(os.path.normpath(p)) == norm_img_path:
                    r_index = idx % 9
                    break
            
            # EN: Calculate total width for range
            total_rel_w = sum(batch_width_cache.get(os.path.normcase(os.path.normpath(p)), 1.6) for p in current_batch_paths)
            curr_accum = 0.0
            for p in current_batch_paths:
                p_norm = os.path.normcase(os.path.normpath(p))
                if p_norm == norm_img_path:
                    w = batch_width_cache.get(p_norm, 1.6)
                    r_range = (curr_accum / total_rel_w, (curr_accum + w) / total_rel_w)
                    break
                curr_accum += batch_width_cache.get(p_norm, 1.6)

        # EN: Final Render
        final_pil = self.renderer.process_image(img_path, data, None, 
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
            "dark": "dark", "深色": "dark", "Dark": "dark",
            "light": "light", "浅色": "light", "Light": "light", "Default": "light"
        }
        theme_str_lower = theme_str.lower()
        for k, v in t_map.items():
            if k.lower() in theme_str_lower:
                return v
        return "light"
