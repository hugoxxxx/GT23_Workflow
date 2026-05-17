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

from core.layout.calculator import LayoutCalculator
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

    def save_ui_state(self, path, cfg):
        """EN: Save UI DTO state into BatchState / CN: 将纯数据 DTO 存入 BatchState"""
        if not path: return
        self.state.set_config(path, cfg)

    def load_ui_state(self, path):
        """EN: Load UI state DTO from BatchState / CN: 从 BatchState 加载纯数据 DTO"""
        return self.state.get_config(path)

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

    def save_border_preset(self, name, cfg):
        """EN: Save current border settings as a preset / CN: 将当前边框设置保存为预设"""
        self.add_border_preset(name, cfg)

    def load_border_preset(self, name):
        """EN: Apply saved border preset / CN: 应用保存的边框预设"""
        presets = self.get_border_presets()
        return presets.get(name)

    def save_metadata_preset(self, name, cfg):
        """EN: Save favorite EXIF model preset / CN: 收藏常用机型预设"""
        exif = cfg.get("exif", {})
        data = {
            "make": exif.get("Make", ""),
            "model": exif.get("Model", ""),
            "lens": exif.get("Lens", "")
        }
        self.add_metadata_preset(name, data)

    def load_metadata_preset(self, name):
        """EN: Apply favorite EXIF model preset / CN: 应用收藏的常用机型预设"""
        presets = self.get_metadata_presets()
        return presets.get(name)

    def get_layout_from_aspect(self, img_path):
        """EN: Reset border paddings dynamically matching aspect from layouts.json / CN: 根据 layouts.json 最佳配置动态计算边框"""
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
            
            if best_cfg:
                ref = 4500.0
                return {
                    "left_px": int(best_cfg.get("side_ratio", 0.04) * ref),
                    "right_px": int(best_cfg.get("side_ratio", 0.04) * ref),
                    "top_px": int(best_cfg.get("top_ratio", 0.04) * ref),
                    "bottom_px": int(best_cfg.get("bottom_ratio", 0.13) * ref),
                    "font_scale": int(best_cfg.get("font_scale", 0.032) * ref) if "font_scale" in best_cfg else 144
                }
        except Exception as e:
            self.log(f"CN: [!] 动态布局重置失败: {e}")
        return None

    def detect_layout_from_folder_as_dict(self, folder):
        """EN: Detect folder layout and assign parameters as DTO / CN: 匹配文件夹全局布局并返回 DTO 字典"""
        layout_cfg = self.detect_layout_from_folder(folder)
        if layout_cfg:
            ref = 4500.0
            side = layout_cfg.get('side_ratio', 0.04)
            return {
                'left_px': int(layout_cfg.get('left_ratio', side) * ref),
                'right_px': int(layout_cfg.get('right_ratio', side) * ref),
                'top_px': int(layout_cfg.get('top_ratio', 0.04) * ref),
                'bottom_px': int(layout_cfg.get('bottom_ratio', 0.13) * ref),
                'font_scale': int(layout_cfg.get('font_scale', 0.032) * ref)
            }
        return None

    def is_processing(self):
        """EN: Check if batch thread is active / CN: 检查批量线程是否正在运行"""
        return getattr(self, '_worker_thread', None) is not None and self._worker_thread.is_alive()

    def start_batch_processing_from_dict(self, output_dir, cfg, film_list):
        """EN: Safe multi-threaded batch launch using clean DTO / CN: 安全的异步批量导出运行"""
        import threading
        
        exif = cfg.get('exif', {})
        global_cfg = {
            'is_digital': cfg.get('mode') == "digital",
            'is_pure': cfg.get('mode') == "pure",
            'theme': cfg.get('theme', 'light'),
            'rotation': cfg.get('rotation', 0),
            'layout': {
                "left_px": cfg.get("left_px", 180),
                "right_px": cfg.get("right_px", 180),
                "top_px": cfg.get("top_px", 180),
                "bottom_px": cfg.get("bottom_px", 585),
                "font_sub_px": cfg.get("font_sub_px", 112),
                "font_v_offset": cfg.get("font_v_offset", 0)
            },
            'exif': {
                'Make': exif.get('Make', '').strip(),
                'Model': exif.get('Model', '').strip(),
                'LensModel': exif.get('Lens', '').strip(),
                'ExposureTimeStr': exif.get('Shutter', '').strip(),
                'FNumber': exif.get('Aperture', '').strip(),
                'ISO': exif.get('ISO', '').strip(),
                'show_make': exif.get('show_make', 1),
                'show_model': exif.get('show_model', 1),
                'show_shutter': exif.get('show_shutter', 1),
                'show_aperture': exif.get('show_aperture', 1),
                'show_iso': exif.get('show_iso', 1),
                'show_lens': exif.get('show_lens', 1),
            },
            'use_branding': cfg.get('branding', True)
        }
        
        manual_film = None
        if not global_cfg['is_digital']:
            manual_film = cfg.get('film_combo')
        global_cfg['manual_film'] = manual_film

        def run_work():
            self.run_batch(output_dir=output_dir, global_cfg=global_cfg, film_list=film_list)
            
        self._worker_thread = threading.Thread(target=run_work, daemon=True)
        self._worker_thread.start()

    def resolve_ratio_locked_sync(self, img_path, ratio_str, current_cfg, param_shadow, is_offset, sync_lr):
        """
        EN: Auto-calculate paddings via centralized LayoutCalculator to maintain target ratio.
        CN: 比例锁定联动逻辑：调用统一解算器自动计算并补齐其余边际并返回更新后的边距 DTO。
        """
        try:
            path_norm = os.path.normcase(os.path.normpath(img_path))
            img_ratio = self.state.get_width(path_norm)
            if not img_ratio: return None
            
            ref_w = 4000.0
            ref_h = ref_w / img_ratio
            
            def get_int_safe(val, default=180):
                try: return int(float(val)) if val is not None and str(val).strip() != "" else default
                except: return default

            if is_offset:
                base_p = {
                    "l": get_int_safe(param_shadow.get("left", "180"), 180),
                    "r": get_int_safe(param_shadow.get("right", "180"), 180),
                    "t": get_int_safe(param_shadow.get("top", "180"), 180),
                    "b": get_int_safe(param_shadow.get("bottom", "585"), 585)
                }
            else:
                base_p = {
                    "l": get_int_safe(current_cfg.get("left_px"), 0),
                    "r": get_int_safe(current_cfg.get("right_px"), 0),
                    "t": get_int_safe(current_cfg.get("top_px"), 0),
                    "b": get_int_safe(current_cfg.get("bottom_px"), 0)
                }
                
                changed = []
                if str(current_cfg.get("left_px")) != str(param_shadow.get("left")): changed.append("w")
                if str(current_cfg.get("right_px")) != str(param_shadow.get("right")): changed.append("w")
                if str(current_cfg.get("top_px")) != str(param_shadow.get("top")): changed.append("h")
                if str(current_cfg.get("bottom_px")) != str(param_shadow.get("bottom")): changed.append("h")
                
                is_free_mode = "Original" in ratio_str or "原图" in ratio_str
                if not is_free_mode and changed:
                    parts = ratio_str.split(':')
                    target_r = 1.0
                    if len(parts) == 2:
                        try: target_r = float(parts[0]) / float(parts[1])
                        except: pass
                    
                    l, r, t, b = base_p["l"], base_p["r"], base_p["t"], base_p["b"]
                    
                    if "w" in changed and "h" not in changed:
                        total_w = ref_w + l + r
                        needed_h_total = total_w / target_r
                        needed_paddings_h = needed_h_total - ref_h
                        new_b = max(10, int(needed_paddings_h - t))
                        base_p["b"] = new_b
                    elif "h" in changed and "w" not in changed:
                        total_h = ref_h + t + b
                        needed_w_total = total_h * target_r
                        needed_paddings_w = needed_w_total - ref_w
                        if sync_lr:
                            new_side = max(10, int(needed_paddings_w / 2))
                            base_p["l"] = new_side
                            base_p["r"] = new_side
                        else:
                            new_r = max(10, int(needed_paddings_w - l))
                            base_p["r"] = new_r
            
            prediction = LayoutCalculator.preview_ui_paddings(
                ref_w, ref_h, ratio_str, base_p, 
                current_cfg.get("h_offset", 0), current_cfg.get("v_offset", 0)
            )
            return {
                "left_px": str(prediction["left"]),
                "right_px": str(prediction["right"]),
                "top_px": str(prediction["top"]),
                "bottom_px": str(prediction["bottom"])
            }
        except Exception as e:
            print(f"DEBUG: Controller Ratio sync failed: {e}")
        return None

    def format_preview_specs(self, preview_w, preview_h, is_zh=True):
        """EN: Format specs / CN: 格式化预览参数"""
        scale = 4500.0 / 1200.0
        final_w = int(preview_w * scale)
        final_h = int(preview_h * scale)
        
        actual_ratio = final_w / final_h
        ratio_str = None
        for r_name, r_val in [("3:2", 3/2), ("2:3", 2/3), ("4:3", 4/3), ("3:4", 3/4), 
                             ("16:9", 16/9), ("9:16", 9/16), ("1:1", 1.0), ("4:5", 4/5), ("5:4", 5/4)]:
            if abs(actual_ratio - r_val) < 0.02:
                ratio_str = r_name
                break
        
        if not ratio_str:
            if actual_ratio >= 1:
                ratio_str = f"{actual_ratio:.2f}:1"
            else:
                ratio_str = f"1:{1/actual_ratio:.2f}"
        
        prefix = "规格: " if is_zh else "Specs: "
        return f"{prefix}{final_w} x {final_h} px ({ratio_str})"

    def format_font_overflow_warnings(self, report, is_zh=True):
        """EN: Format font overflow warnings / CN: 格式化字体溢出警告"""
        if 'render_breakdown' not in report or 'max_font_px' not in report['render_breakdown']:
            return ""
        max_info = report['render_breakdown']['max_font_px']
        main_max = max_info.get('main', 0)
        sub_max = max_info.get('sub', 0)
        
        main_overflow = max_info.get('main_overflow', False)
        sub_overflow = max_info.get('sub_overflow', False)
        v_overflow = max_info.get('v_overflow', False)
        
        warnings = []
        if main_overflow or v_overflow:
            if v_overflow:
                msg = f"⚠️ 型号压图！建议 ≤{main_max}px" if is_zh else f"⚠️ Model on photo! Max ≤{main_max}px"
            else:
                msg = f"⚠️ 型号溢出，建议 ≤{main_max}px" if is_zh else f"⚠️ Model overflow, suggest ≤{main_max}px"
            warnings.append(msg)

        if sub_overflow:
            warnings.append(f"⚠️ 参数溢出，建议 ≤{sub_max}px" if is_zh else f"⚠️ Param overflow, suggest ≤{sub_max}px")
        
        return " | ".join(warnings) if warnings else ""
