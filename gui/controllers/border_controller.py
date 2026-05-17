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
import json
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer
from core.utils.bootstrapper import bootstrap_logos
from utils.config_manager import config_manager

from gui.controllers.batch_state import BatchState

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
        
        # --- State Management (Now Encapsulated) ---
        self.state = BatchState()
        self.input_folder = None
        
        # Load necessary singletons/handlers
        self.renderer = FilmRenderer()
        self.metadata_handler = MetadataHandler(layout_config='layouts.json', films_config='films.json')
        
        # User settings for presets (Persistence)
        self.user_settings_path = os.path.join(config_manager.config_dir, "user_presets.json")
        self.user_presets = self._load_user_presets()
        
        # System aesthetic presets
        self.aesthetic_presets = self._load_aesthetic_presets()

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
        self.state.set_paths(found_files)
        
        return len(found_files)

    def update_batch_order(self, new_paths):
        """EN: Update current batch order / CN: 更新当前批次顺序"""
        self.state.set_paths(new_paths)

    def add_to_batch(self, paths):
        """EN: Add specific files to current batch / CN: 将特定文件添加到当前批次"""
        for p in paths:
            self.state.add_path(p)
        return len(self.state.get_paths())

    def remove_from_batch(self, path):
        """EN: Remove file from batch / CN: 从批次中移除文件"""
        self.state.remove_path(path)

    def update_image_config(self, path, params):
        """EN: Update config for a specific image / CN: 更新单张图片的配置"""
        self.state.set_config(path, params)

    def clear_all_configs(self):
        """EN: Clear all image configurations / CN: 清除所有图片配置"""
        for p in self.state.get_paths():
            self.state.set_config(p, None)

    def get_image_config(self, path):
        """EN: Get config for a specific image / CN: 获取单张图片的配置"""
        return self.state.get_config(path) or {}

    def sync_config_to_similar(self, source_path, params):
        """
        EN: Apply source params to all images in batch with same aspect ratio and rotation.
        CN: 将当前图片的配置应用到批次中具有相同宽高比和旋转角度的所有图片。
        """
        source_ratio = self.state.get_width(source_path)
        if source_ratio is None: return 0
        
        source_rotation = params.get('rotation', 0)
        sync_keys = [
            'left_px', 'right_px', 'top_px', 'bottom_px', 
            'font_scale', 'font_sub_px', 'font_v_offset', 'font_spacing',
            'font_main_path', 'font_sub_path',
            'theme', 'branding', 'auto_detect', 'film_combo', 'sync_lr',
            'v_offset', 'h_offset'
        ]
        sync_data = {k: params[k] for k in sync_keys if k in params}
        
        count = 0
        all_paths = self.state.get_paths()
        source_norm = os.path.normcase(os.path.normpath(source_path))
        
        for path in all_paths:
            if path == source_norm: continue
            
            target_ratio = self.state.get_width(path)
            if target_ratio is None: continue
            
            if abs(target_ratio - source_ratio) < 0.05:
                target_cfg = self.state.get_config(path) or {}
                if target_cfg.get('rotation', 0) == source_rotation:
                    new_cfg = dict(target_cfg)
                    new_cfg.update(sync_data)
                    self.state.set_config(path, new_cfg)
                    count += 1
        return count

    def update_aspect_ratio_cache(self, path, ratio):
        """EN: Cache aspect ratio for an image / CN: 缓存图片的宽高比"""
        self.state.update_width(path, ratio)

    # --- Processing Logic ---

    def run_batch(self, output_dir, global_cfg, film_list):
        """
        EN: Main batch processing loop using internal state
        CN: 使用内部状态的主批量处理循环
        """
        self.stop_requested = False
        files = self.state.get_paths()
        total = len(files)
        
        if total == 0:
            self.log("CN: [!] 队列内未找到待处理图片" if self.lang=="zh" else "EN: [!] No images in queue")
            return

        try:
            # EN: Pre-calculate total relative width for physical slice (Rainbow/Macaron)
            relative_widths = []
            total_rel_w = 0.0
            for img_path in files:
                rel_w = self.state.get_width(img_path)
                if rel_w is None:
                    try:
                        # EN: Protect image open with semaphore (#5)
                        with self.state.image_limit:
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
                cfg = self.state.get_config(img_path) or {}
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
                    "font_v_offset": layout_cfg.get('font_v_offset', 0) / ref,
                    "font_spacing_scale": layout_cfg.get('font_spacing', 0) / ref
                })
                
                # EN: Apply Font Overrides / CN: 应用字体覆盖
                data['font_main_path'] = cfg.get('font_main_path', 'Default')
                data['font_sub_path'] = cfg.get('font_sub_path', 'Default')
                
                exif_cfg = cfg.get('exif') if cfg else global_cfg.get('exif')
                if exif_cfg:
                    for k, v in exif_cfg.items():
                        if v is not None and v != "":
                            key = k if k != 'Lens' else 'LensModel'
                            key = key if key != 'Shutter' else 'ExposureTimeStr'
                            key = key if key != 'Aperture' else 'FNumber'
                            data[key] = v
                
                data['target_ratio'] = cfg.get('target_ratio', global_cfg.get('target_ratio', 'Original'))

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
                                     output_prefix=out_prefix,
                                     v_offset=cfg.get('v_offset', 0),
                                     h_offset=cfg.get('h_offset', 0))

            if self.complete_callback:
                self.complete_callback({'success': True, 'processed': total if not self.stop_requested else i})
                
        except Exception as e:
            import traceback
            if self.error_callback:
                self.error_callback(traceback.format_exc())

    def get_preview_image(self, img_path, is_digital, is_pure, manual_film, rotation, use_branding=True, panel_job_id=0):
        """
        EN: Generate a preview image using internal and passed state
        CN: 使用内部和传入状态生成预览图
        """
        # EN: Sync with Panel's job ID to allow discard of stale renders (#4)
        # CN: 与面板的 Job ID 同步，以便丢弃过时的渲染请求
        self.state.sync_job_id(panel_job_id)
        
        job_id = panel_job_id
        import time
        t_start = time.perf_counter()
        render_timings = {}
        
        cfg = self.state.get_config(img_path) or {}
        m_film = manual_film
        if cfg and not cfg.get('auto_detect', True):
            m_film = cfg.get('film_combo')
            
        data = self.metadata_handler.get_data(img_path, is_digital_mode=is_digital, manual_film=m_film)
        t_meta = time.perf_counter() - t_start

        layout_cfg = cfg if cfg else {
            "left_px": 180, "right_px": 180, "top_px": 180, "bottom_px": 585, 
            "font_scale": 144, "font_sub_px": 112, "font_v_offset": 0, "font_spacing": 0
        }
        ref = 4500.0
        data['layout'].update({
            "left": layout_cfg.get('left_px', 180) / ref,
            "right": layout_cfg.get('right_px', 180) / ref,
            "top": layout_cfg.get('top_px', 180) / ref,
            "bottom": layout_cfg.get('bottom_px', 585) / ref,
            "font_main_scale": layout_cfg.get('font_scale', 144) / ref,
            "font_sub_scale": layout_cfg.get('font_sub_px', 112) / ref,
            "font_v_offset": layout_cfg.get('font_v_offset', 0) / ref,
            "font_spacing_scale": layout_cfg.get('font_spacing', 0) / ref
        })
        
        # EN: Apply Font Overrides / CN: 应用字体覆盖
        data['font_main_path'] = cfg.get('font_main_path', 'Default')
        data['font_sub_path'] = cfg.get('font_sub_path', 'Default')
        
        exif_cfg = cfg.get('exif')
        if exif_cfg:
            for k, v in exif_cfg.items():
                if v is not None and v != "":
                    key = k if k != 'Lens' else 'LensModel'
                    key = key if key != 'Shutter' else 'ExposureTimeStr'
                    key = key if key != 'Aperture' else 'FNumber'
                    data[key] = v
        
        data['target_ratio'] = cfg.get('target_ratio', 'Original')

        theme_str = cfg.get('theme', 'light')
        theme_val = self.resolve_theme(theme_str)

        r_index = 0
        r_total = 1
        r_range = (0.0, 1.0)
        
        all_paths = self.state.get_paths()
        if theme_val in ["macaron", "rainbow", "sakura"] and all_paths:
            r_total = len(all_paths)
            norm_img_path = os.path.normcase(os.path.normpath(img_path))
            
            for idx, p in enumerate(all_paths):
                if p == norm_img_path:
                    r_index = idx % 9
                    break
            
            total_rel_w = sum(self.state.get_width(p) or 1.6 for p in all_paths)
            curr_accum = 0.0
            for p in all_paths:
                if p == norm_img_path:
                    w = self.state.get_width(p) or 1.6
                    r_range = (curr_accum / total_rel_w, (curr_accum + w) / total_rel_w)
                    break
                curr_accum += self.state.get_width(p) or 1.6

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
                                         v_offset=cfg.get('v_offset', 0),
                                         h_offset=cfg.get('h_offset', 0),
                                         timing_results=render_timings)
        
        total_time = time.perf_counter() - t_start
        performance_report = {
            'total': total_time,
            'metadata': t_meta,
            'render_breakdown': render_timings
        }
        
        # EN: Final check if this job is still relevant (#4)
        if not self.state.is_job_current(job_id):
            return None, performance_report
            
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

    def _load_aesthetic_presets(self):
        """EN: Load aesthetic presets from JSON / CN: 从JSON加载美学预设"""
        try:
            config_path = os.path.join(os.getcwd(), 'assets', 'config', 'aesthetic_presets.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
            
    def get_aesthetic_presets(self):
        return self.aesthetic_presets

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
        
    def load_font_library(self):
        """EN: Load fonts from asset directory / CN: 从资源目录加载字体库"""
        fonts = ["LEICA-1050"]
        try:
            f_dir = self.renderer.font_dir
            if os.path.exists(f_dir):
                for f in os.listdir(f_dir):
                    if f.lower().endswith(('.ttf', '.otf', '.ttc')):
                        fonts.append(f)
            # fonts.sort() # Keep LEICA-1050 at top
        except:
            pass
        return fonts

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

    # --- User Presets Persistence ---

    def _load_user_presets(self):
        default = {"border": {}, "metadata": {}}
        if os.path.exists(self.user_settings_path):
            try:
                with open(self.user_settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except: pass
        return default

    def _save_user_presets(self):
        try:
            with open(self.user_settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"CN: [!] 无法保存用户预设: {e}")

    def get_border_presets(self):
        return self.user_presets.get("border", {})

    def add_border_preset(self, name, params):
        if "border" not in self.user_presets: self.user_presets["border"] = {}
        self.user_presets["border"][name] = params
        self._save_user_presets()

    def delete_border_preset(self, name):
        if name in self.user_presets.get("border", {}):
            del self.user_presets["border"][name]
            self._save_user_presets()

    def get_metadata_presets(self):
        return self.user_presets.get("metadata", {})

    def add_metadata_preset(self, name, data):
        if "metadata" not in self.user_presets: self.user_presets["metadata"] = {}
        self.user_presets["metadata"][name] = data
        self._save_user_presets()

    def delete_metadata_preset(self, name):
        if name in self.user_presets.get("metadata", {}):
            del self.user_presets["metadata"][name]
            self._save_user_presets()

    def save_ui_state(self, path, ui_vars):
        """EN: Save UI variables state into BatchState / CN: 将UI变量状态存入BatchState"""
        if not path: return
        
        # Helper to get variable value safely
        def get_val(var):
            return var.get() if hasattr(var, 'get') else var
            
        def get_int(var, default=0):
            try:
                val = get_val(var)
                if val is None: return default
                return int(float(val)) if str(val).strip() != "" else default
            except:
                return default

        exif_vars = ui_vars.get('exif_vars', {})
        params = {
            'left_px': get_int(ui_vars.get('left_px_var'), 180),
            'right_px': get_int(ui_vars.get('right_px_var'), 180),
            'top_px': get_int(ui_vars.get('top_px_var'), 180),
            'bottom_px': get_int(ui_vars.get('bottom_px_var'), 585),
            'font_scale': get_int(ui_vars.get('font_scale_var'), 144),
            'font_sub_px': get_int(ui_vars.get('font_sub_px_var'), 112),
            'font_v_offset': get_int(ui_vars.get('font_offset_px_var'), 0),
            'font_main_path': str(get_val(ui_vars.get('font_main_path_var'))),
            'font_sub_path': str(get_val(ui_vars.get('font_sub_path_var'))),
            'v_offset': get_int(ui_vars.get('v_offset_var'), 0),
            'h_offset': get_int(ui_vars.get('h_offset_var'), 0),
            'theme': str(get_val(ui_vars.get('theme_var'))),
            'rotation': get_int(ui_vars.get('rotation_var'), 0),
            'auto_detect': bool(get_val(ui_vars.get('auto_detect_var'))),
            'film_combo': str(get_val(ui_vars.get('film_combo'))),
            'sync_lr': bool(get_val(ui_vars.get('sync_lr_var'))),
            'target_ratio': str(get_val(ui_vars.get('target_ratio_var'))),
            'font_spacing': get_int(ui_vars.get('font_spacing_var'), 0),
            'exif': {
                'Make': str(get_val(exif_vars.get('Make'))).strip(),
                'Model': str(get_val(exif_vars.get('Model'))).strip(),
                'Lens': str(get_val(exif_vars.get('Lens'))).strip(),
                'Shutter': str(get_val(exif_vars.get('Shutter'))).strip(),
                'Aperture': str(get_val(exif_vars.get('Aperture'))).strip(),
                'ISO': str(get_val(exif_vars.get('ISO'))).strip(),
                'show_make': get_int(exif_vars.get('show_make'), 1),
                'show_model': get_int(exif_vars.get('show_model'), 1),
                'show_shutter': get_int(exif_vars.get('show_shutter'), 1),
                'show_aperture': get_int(exif_vars.get('show_aperture'), 1),
                'show_iso': get_int(exif_vars.get('show_iso'), 1),
                'show_lens': get_int(exif_vars.get('show_lens'), 1)
            }
        }
        self.state.set_config(path, params)

    def load_ui_state(self, path, ui_vars):
        """EN: Load UI variables state from BatchState / CN: 从BatchState加载UI变量状态"""
        cfg = self.state.get_config(path)
        if not cfg: return False
        
        # Helper to set variable value safely
        def set_val(var, val):
            if var and hasattr(var, 'set'):
                try: var.set(val)
                except: pass

        if 'left_px' in cfg: set_val(ui_vars.get('left_px_var'), cfg['left_px'])
        if 'right_px' in cfg: set_val(ui_vars.get('right_px_var'), cfg['right_px'])
        if 'top_px' in cfg: set_val(ui_vars.get('top_px_var'), cfg['top_px'])
        if 'bottom_px' in cfg: set_val(ui_vars.get('bottom_px_var'), cfg['bottom_px'])
        
        if 'font_scale' in cfg:
            val = cfg['font_scale']
            if val < 1.0: val = int(val * 4500) # Migration
            set_val(ui_vars.get('font_scale_var'), int(val))
            
        if 'font_sub_px' in cfg: 
            set_val(ui_vars.get('font_sub_px_var'), cfg['font_sub_px'])
        elif 'font_scale' in cfg:
            # EN: Dynamic fallback for old configs (CN: 为旧配置提供动态回退)
            scale = ui_vars.get('font_scale_var')
            scale_val = scale.get() if scale and hasattr(scale, 'get') else 144
            try: set_val(ui_vars.get('font_sub_px_var'), int(float(scale_val) * 0.78))
            except: set_val(ui_vars.get('font_sub_px_var'), 112)
            
        if 'theme' in cfg: set_val(ui_vars.get('theme_var'), cfg['theme'])
        if 'film_combo' in cfg: set_val(ui_vars.get('film_combo'), cfg['film_combo'])
        if 'font_v_offset' in cfg: set_val(ui_vars.get('font_offset_px_var'), cfg['font_v_offset'])
        if 'font_spacing' in cfg: set_val(ui_vars.get('font_spacing_var'), cfg['font_spacing'])
        if 'font_main_path' in cfg: set_val(ui_vars.get('font_main_path_var'), cfg['font_main_path'])
        if 'font_sub_path' in cfg: set_val(ui_vars.get('font_sub_path_var'), cfg['font_sub_path'])
        
        set_val(ui_vars.get('v_offset_var'), cfg.get('v_offset', 0))
        set_val(ui_vars.get('h_offset_var'), cfg.get('h_offset', 0))
        set_val(ui_vars.get('sync_lr_var'), cfg.get('sync_lr', True))
        set_val(ui_vars.get('target_ratio_var'), cfg.get('target_ratio', 'Original'))
        set_val(ui_vars.get('rotation_var'), cfg.get('rotation', 0))
        set_val(ui_vars.get('auto_detect_var'), cfg.get('auto_detect', True))
        
        exif = cfg.get('exif', {})
        exif_vars = ui_vars.get('exif_vars', {})
        if exif_vars:
            set_val(exif_vars.get('show_make'), exif.get('show_make', 1))
            set_val(exif_vars.get('show_model'), exif.get('show_model', 1))
            set_val(exif_vars.get('show_shutter'), exif.get('show_shutter', 1))
            set_val(exif_vars.get('show_aperture'), exif.get('show_aperture', 1))
            set_val(exif_vars.get('show_iso'), exif.get('show_iso', 1))
            set_val(exif_vars.get('show_lens'), exif.get('show_lens', 1))
            
            global_var = ui_vars.get('exif_global_var')
            is_global = global_var.get() if global_var and hasattr(global_var, 'get') else False
            if not is_global:
                set_val(exif_vars.get('Make'), exif.get('Make', ''))
                set_val(exif_vars.get('Model'), exif.get('Model', ''))
                set_val(exif_vars.get('Lens'), exif.get('Lens', ''))
                set_val(exif_vars.get('Shutter'), exif.get('Shutter', ''))
                set_val(exif_vars.get('Aperture'), exif.get('Aperture', ''))
                set_val(exif_vars.get('ISO'), exif.get('ISO', ''))
                
        return True

    def request_preview(self, img_path, is_digital, is_pure, manual_film, rotation, use_branding, success_callback, error_callback):
        """
        EN: Request async rendering of preview with Job ID and thread management.
        CN: 异步请求渲染预览图，支持 Job ID 校验与线程调度。
        """
        import threading
        
        # 1. EN: Get atomic job ID from BatchState
        # CN: 从 BatchState 获取原子性的 Job ID
        job_id = self.state.get_next_job_id()
        
        def worker():
            try:
                # EN: Call the synchronous preview image generator
                # CN: 调用同步预览图生成器
                final_pil, report = self.get_preview_image(
                    img_path=img_path,
                    is_digital=is_digital,
                    is_pure=is_pure,
                    manual_film=manual_film,
                    rotation=rotation,
                    use_branding=use_branding,
                    panel_job_id=job_id
                )
                
                # EN: Check if the job is still current
                # CN: 检查该渲染任务是否仍然是最新的
                if not self.state.is_job_current(job_id) or final_pil is None:
                    return
                
                # EN: Safe execution of success callback
                # CN: 安全回调成功函数
                success_callback(final_pil, report, job_id)
            except Exception as e:
                # EN: Check if still relevant before invoking error callback
                # CN: 触发错误回调前再次校验相关性
                if self.state.is_job_current(job_id):
                    error_callback(str(e), job_id)
                    
        # EN: Dispatch daemon worker thread
        # CN: 调度后台守护线程执行渲染
        threading.Thread(target=worker, daemon=True).start()

    def save_border_preset(self, name, ui_vars):
        """EN: Save current border settings as a preset / CN: 将当前边框设置保存为预设"""
        params = {
            "theme": ui_vars.get("theme_var").get(),
            "target_ratio": ui_vars.get("target_ratio_var").get(),
            "left_px": ui_vars.get("left_px_var").get(),
            "right_px": ui_vars.get("right_px_var").get(),
            "top_px": ui_vars.get("top_px_var").get(),
            "bottom_px": ui_vars.get("bottom_px_var").get(),
            "font_scale": ui_vars.get("font_scale_var").get(),
            "font_sub_px": ui_vars.get("font_sub_px_var").get(),
            "font_v_offset": ui_vars.get("font_offset_px_var").get(),
            "font_spacing": ui_vars.get("font_spacing_var").get(),
            "font_main_path": ui_vars.get("font_main_path_var").get(),
            "font_sub_path": ui_vars.get("font_sub_path_var").get(),
            "v_offset": ui_vars.get("v_offset_var").get(),
            "h_offset": ui_vars.get("h_offset_var").get(),
            "rotation": ui_vars.get("rotation_var").get(),
            "auto_detect": ui_vars.get("auto_detect_var").get(),
            "film_combo": ui_vars.get("film_combo").get() if ui_vars.get("film_combo") else "",
            "branding": ui_vars.get("branding").get() if ui_vars.get("branding") else True,
            "sync_lr": ui_vars.get("sync_lr_var").get()
        }
        self.add_border_preset(name, params)

    def load_border_preset(self, name, ui_vars):
        """EN: Apply saved border preset / CN: 应用保存的边框预设"""
        presets = self.get_border_presets()
        if name in presets:
            p = presets[name]
            def set_val(var, key, default):
                if var and hasattr(var, 'set'):
                    var.set(p.get(key, default))
            set_val(ui_vars.get("theme_var"), "theme", "light")
            set_val(ui_vars.get("target_ratio_var"), "target_ratio", "Original")
            set_val(ui_vars.get("left_px_var"), "left_px", "180")
            set_val(ui_vars.get("right_px_var"), "right_px", "180")
            set_val(ui_vars.get("top_px_var"), "top_px", "180")
            set_val(ui_vars.get("bottom_px_var"), "bottom_px", "585")
            set_val(ui_vars.get("font_scale_var"), "font_scale", "144")
            set_val(ui_vars.get("font_sub_px_var"), "font_sub_px", "112")
            set_val(ui_vars.get("font_offset_px_var"), "font_v_offset", "0")
            set_val(ui_vars.get("font_spacing_var"), "font_spacing", "180")
            set_val(ui_vars.get("font_main_path_var"), "font_main_path", "Default")
            set_val(ui_vars.get("font_sub_path_var"), "font_sub_path", "Default")
            set_val(ui_vars.get("v_offset_var"), "v_offset", 0)
            set_val(ui_vars.get("h_offset_var"), "h_offset", 0)
            set_val(ui_vars.get("rotation_var"), "rotation", 0)
            set_val(ui_vars.get("auto_detect_var"), "auto_detect", True)
            set_val(ui_vars.get("sync_lr_var"), "sync_lr", True)
            if "film_combo" in p and ui_vars.get("film_combo"):
                ui_vars.get("film_combo").set(p["film_combo"])
            if "branding" in p and ui_vars.get("branding"):
                ui_vars.get("branding").set(p["branding"])

    def save_metadata_preset(self, name, ui_vars):
        """EN: Save favorite EXIF model preset / CN: 收藏常用机型预设"""
        exif_vars = ui_vars.get("exif_vars", {})
        data = {
            "make": exif_vars.get("Make").get() if exif_vars.get("Make") else "",
            "model": exif_vars.get("Model").get() if exif_vars.get("Model") else "",
            "lens": exif_vars.get("Lens").get() if exif_vars.get("Lens") else ""
        }
        self.add_metadata_preset(name, data)

    def load_metadata_preset(self, name, ui_vars):
        """EN: Apply favorite EXIF model preset / CN: 应用收藏的常用机型预设"""
        presets = self.get_metadata_presets()
        if name in presets:
            p = presets[name]
            exif_vars = ui_vars.get("exif_vars", {})
            def set_val(var, val):
                if var and hasattr(var, 'set'): var.set(val)
            set_val(exif_vars.get("Make"), p.get("make", ""))
            set_val(exif_vars.get("Model"), p.get("model", ""))
            set_val(exif_vars.get("Lens"), p.get("lens", ""))

    def reset_to_json_layout(self, img_path, ui_vars):
        """EN: Reset border paddings dynamically matching aspect from layouts.json / CN: 根据 layouts.json 最佳配置动态重设边框"""
        try:
            aspect = self.state.get_width(img_path)
            if aspect is None:
                with Image.open(img_path) as img:
                    w, h = img.size
                    aspect = w / h
                    self.update_aspect_ratio_cache(img_path, aspect)

            is_portrait = aspect < 0.95
            best_cfg = None
            for name, entry in self.layout_config.items():
                r_min, r_max = entry.get("aspect_range", [0, 99])
                if is_portrait:
                    r_min, r_max = 1.0/r_max, 1.0/r_min
                if r_min <= aspect <= r_max:
                    best_cfg = entry.get("portrait" if is_portrait else "landscape", entry.get("all"))
                    break
            
            def set_val(var, val):
                if var and hasattr(var, 'set'): var.set(str(val))

            if best_cfg:
                ref = 4500.0
                set_val(ui_vars.get("left_px_var"), int(best_cfg.get("side_ratio", 0.04) * ref))
                set_val(ui_vars.get("right_px_var"), int(best_cfg.get("side_ratio", 0.04) * ref))
                set_val(ui_vars.get("top_px_var"), int(best_cfg.get("top_ratio", 0.04) * ref))
                set_val(ui_vars.get("bottom_px_var"), int(best_cfg.get("bottom_ratio", 0.13) * ref))
                if "font_scale" in best_cfg:
                    set_val(ui_vars.get("font_scale_var"), int(best_cfg["font_scale"] * ref))
            else:
                set_val(ui_vars.get("left_px_var"), "180")
                set_val(ui_vars.get("right_px_var"), "180")
                set_val(ui_vars.get("top_px_var"), "180")
                set_val(ui_vars.get("bottom_px_var"), "585")
        except Exception as e:
            self.log(f"CN: [!] 动态布局重置失败: {e}")

    def detect_layout_and_load_params(self, folder, ui_vars):
        """EN: Detect folder layout and assign parameters / CN: 匹配文件夹全局布局并写入参数"""
        layout_cfg = self.detect_layout_from_folder(folder)
        if layout_cfg:
            ref = 4500.0
            side = layout_cfg.get('side_ratio', 0.04)
            def set_val(var, val):
                if var and hasattr(var, 'set'): var.set(str(val))
            set_val(ui_vars.get('left_px_var'), int(layout_cfg.get('left_ratio', side) * ref))
            set_val(ui_vars.get('right_px_var'), int(layout_cfg.get('right_ratio', side) * ref))
            set_val(ui_vars.get('top_px_var'), int(layout_cfg.get('top_ratio', 0.04) * ref))
            set_val(ui_vars.get('bottom_px_var'), int(layout_cfg.get('bottom_ratio', 0.13) * ref))
            set_val(ui_vars.get('font_scale_var'), int(layout_cfg.get('font_scale', 0.032) * ref))

    def is_processing(self):
        """EN: Check if batch thread is active / CN: 检查批量线程是否正在运行"""
        return getattr(self, '_worker_thread', None) is not None and self._worker_thread.is_alive()

    def start_batch_processing(self, output_dir, ui_vars, film_list):
        """EN: Safe multi-threaded batch launch / CN: 安全的异步批量导出运行"""
        import threading
        
        def _get_int_safe(var, default=0):
            try:
                val = var.get()
                return int(float(val)) if val is not None and str(val).strip() != "" else default
            except: return default

        global_cfg = {
            'is_digital': ui_vars.get('mode_var').get() == "digital" if ui_vars.get('mode_var') else False,
            'is_pure': ui_vars.get('mode_var').get() == "pure" if ui_vars.get('mode_var') else False,
            'theme': ui_vars.get('theme_var').get(),
            'rotation': ui_vars.get('rotation_var').get() if ui_vars.get('rotation_var') else 0,
            'layout': {
                "left_px": _get_int_safe(ui_vars.get('left_px_var'), 180),
                "right_px": _get_int_safe(ui_vars.get('right_px_var'), 180),
                "top_px": _get_int_safe(ui_vars.get('top_px_var'), 180),
                "bottom_px": _get_int_safe(ui_vars.get('bottom_px_var'), 585),
                "font_sub_px": _get_int_safe(ui_vars.get('font_sub_px_var'), 112),
                "font_v_offset": _get_int_safe(ui_vars.get('font_offset_px_var'), 0)
            },
            'exif': {
                'Make': ui_vars.get('exif_vars', {}).get('Make').get().strip() if ui_vars.get('exif_vars', {}).get('Make') else '',
                'Model': ui_vars.get('exif_vars', {}).get('Model').get().strip() if ui_vars.get('exif_vars', {}).get('Model') else '',
                'LensModel': ui_vars.get('exif_vars', {}).get('Lens').get().strip() if ui_vars.get('exif_vars', {}).get('Lens') else '',
                'ExposureTimeStr': ui_vars.get('exif_vars', {}).get('Shutter').get().strip() if ui_vars.get('exif_vars', {}).get('Shutter') else '',
                'FNumber': ui_vars.get('exif_vars', {}).get('Aperture').get().strip() if ui_vars.get('exif_vars', {}).get('Aperture') else '',
                'ISO': ui_vars.get('exif_vars', {}).get('ISO').get().strip() if ui_vars.get('exif_vars', {}).get('ISO') else '',
                'show_make': ui_vars.get('exif_vars', {}).get('show_make').get() if ui_vars.get('exif_vars', {}).get('show_make') else 1,
                'show_model': ui_vars.get('exif_vars', {}).get('show_model').get() if ui_vars.get('exif_vars', {}).get('show_model') else 1,
                'show_shutter': ui_vars.get('exif_vars', {}).get('show_shutter').get() if ui_vars.get('exif_vars', {}).get('show_shutter') else 1,
                'show_aperture': ui_vars.get('exif_vars', {}).get('show_aperture').get() if ui_vars.get('exif_vars', {}).get('show_aperture') else 1,
                'show_iso': ui_vars.get('exif_vars', {}).get('show_iso').get() if ui_vars.get('exif_vars', {}).get('show_iso') else 1,
                'show_lens': ui_vars.get('exif_vars', {}).get('show_lens').get() if ui_vars.get('exif_vars', {}).get('show_lens') else 1,
            },
            'use_branding': ui_vars.get('branding').get() if ui_vars.get('branding') else True
        }
        
        manual_film = None
        if not global_cfg['is_digital'] and ui_vars.get('film_combo'):
            manual_film = ui_vars.get('film_combo').get()
        global_cfg['manual_film'] = manual_film

        def run_work():
            self.run_batch(output_dir=output_dir, global_cfg=global_cfg, film_list=film_list)
            
        self._worker_thread = threading.Thread(target=run_work, daemon=True)
        self._worker_thread.start()
