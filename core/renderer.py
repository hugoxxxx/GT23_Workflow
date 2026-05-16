import os
import io
import sys
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from utils.config_manager import config_manager

try:
    import cairosvg
except ImportError:
    cairosvg = None

try:
    import svgwrite
except ImportError:
    svgwrite = None

from .io.image_loader import ImageLoader
from .io.exif_editor import ExifEditor
from .io.saver import ImageSaver
from .utils.path import resolve_path
from .utils.bootstrapper import bootstrap_logos, bootstrap_fonts
from .typography.font_resolver import FontResolver
from .typography.text_adjuster import TextAdjuster
from .branding.lens_parser import LensParser
from .branding.logo_finder import LogoFinder
from .layout.calculator import LayoutCalculator
from .layout.sprocket import SprocketEngine
from .typography.text_renderer import TextRenderer
from .effects.shadow import ShadowEngine
from .effects.texture import TextureEngine
from .theme.factory import ThemeFactory
from .metadata import MetadataHandler

class FilmRenderer:
    """
    EN: Pro-grade renderer with dynamic typography hierarchy.
    CN: 中英双语：具备动态字号层级感的高级渲染器。
    """
    def __init__(self, font_main="assets/fonts/palab.ttf", font_sub="assets/fonts/gara.ttf"):
        self.font_main = resolve_path(font_main)
        self.font_sub = resolve_path(font_sub)
        self.bg_color = (255, 255, 255)
        self.main_color = (26, 26, 26)   
        self.sub_color = (85, 85, 85)
        self.border_line_color = (238, 238, 238)
        
        # EN: Handle external logos (next to EXE) vs internal assets (dev/MEIPASS)
        # CN: 处理外置 Logo 资源（EXE 同级目录）与内置资源（开发环境/MEIPASS）
        self.logo_dir = bootstrap_logos(resolve_path)
        
        # EN: Handle dynamic fonts / CN: 处理动态字体解耦
        self.font_dir = bootstrap_fonts(resolve_path)
        self.font_resolver = FontResolver(self.font_dir, self.font_main, self.font_sub)
        
        
        self._setup_cairo_dll()



    def _setup_cairo_dll(self):
        """EN: Fix for cairosvg DLL loading on Windows. / CN: 修复 Windows 上 cairosvg 的 DLL 加载。"""
        if sys.platform == "win32":
            # EN: Try to find cairo.dll in conda env Library/bin
            # CN: 尝试在 conda 环境的 Library/bin 中寻找 cairo.dll
            conda_prefix = os.environ.get("CONDA_PREFIX")
            if conda_prefix:
                bin_dir = os.path.join(conda_prefix, "Library", "bin")
                if os.path.isdir(bin_dir) and hasattr(os, "add_dll_directory"):
                    try:
                        os.add_dll_directory(bin_dir)
                    except:
                        pass


    def process_image(self, img_path, data, output_dir, target_long_edge=4500, manual_rotation=0, 
                    theme="light", is_pure=False, use_lens_branding=True, rainbow_index=0, rainbow_total=1, is_sample=False, 
                    source_img=None, output_prefix="", v_offset=0, h_offset=0, **kwargs):
        """
        EN: Main entry point with theme, global rainbow sequence, and sample mode.
        CN: 主渲染入口，增强主题、全局彩虹长卷与 SAMPLE 样品模式支持。
        """
        timings = kwargs.get('timing_results', {})
        t_start = time.perf_counter()
        
        try:
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if source_img:
                img = source_img
                # EN: Skip rotation and initial resize as it's assumed pre-processed
                # CN: 跳过旋转和初始缩放，假定已预处理
            else:
                img, load_timings = ImageLoader.load_and_preprocess(img_path, target_long_edge, manual_rotation)
                timings.update(load_timings)
            
            w, h = img.size
            
            # --- EN: AUTO-IDENTIFY METADATA (v2.4.1 Parity) ---
            # CN: 自动识别元数据（确保与 v2.4.1 逻辑对齐）
            if not data.get('Make') or not data.get('Model'):
                handler = MetadataHandler()
                auto_data = handler.get_data(img_path)
                
                for k, v in auto_data.items():
                    if k not in data or not data[k] or data[k] == "Unknown":
                        data[k] = v
            
            # --- EN: THEME & COLOR RESOLUTION ---
            is_sprocket = data.get('sprocket_enabled', False)
            theme_obj = ThemeFactory.get_theme(theme, img_path=img_path)
            
            if is_sprocket:
                bg_color, main_color, sub_color, line_color = SprocketEngine.get_sprocket_colors()
            else:
                bg_color, main_color, sub_color, line_color = theme_obj.get_colors(index=rainbow_index)
            
            layout = data.get('layout', {})
            
            # --- EN: TYPOGRAPHY HIERARCHY ---
            t_draw_start = time.perf_counter()
            main_text, sub_text = self._prepare_strings(data)
            data['main_text'] = main_text
            data['sub_text'] = sub_text
            
            if is_sample:
                main_text = "SAMPLE SAMPLE"
                sub_text = "SAMPLE SAMPLE | SAMPLE | SAMPLE"
            
            # --- EN: CALCULATE LAYOUT ---
            t_layout_start = time.perf_counter()
            layout_results = LayoutCalculator.calculate_layout(
                w, h, data, layout, h_offset, v_offset, font_resolver=self.font_resolver
            )
            
            side_pad_left = layout_results["side_pad_left"]
            top_pad = layout_results["top_pad"]
            bottom_splice = layout_results["bottom_splice"]
            new_w = layout_results["new_w"]
            new_h = layout_results["new_h"]
            inner_bottom_margin = layout_results["inner_bottom_margin"]
            
            base_main_font_size = layout_results["base_main_font_size"]
            base_sub_font_size = layout_results["base_sub_font_size"]
            v_offset_px = layout_results["font_v_offset_px"]
            resolved_main = layout_results["resolved_main"]
            resolved_sub = layout_results["resolved_sub"]
            ref_factor = layout_results["ref_factor"]

            timings['layout_calc'] = time.perf_counter() - t_layout_start
            
            # --- EN: CANVAS & PHOTO DRAWING ---
            t_canvas_start = time.perf_counter()
            t_range = kwargs.get('rainbow_range', (0.0, 1.0))
            
            canvas = theme_obj.create_canvas(new_w, new_h, img=img, index=rainbow_index, t_start=t_range[0], t_end=t_range[1])
            if is_sprocket:
                canvas = Image.new("RGB", (new_w, new_h), (0, 0, 0)) # Sprocket always black
                canvas.paste(img, (side_pad_left, top_pad))
                SprocketEngine.apply_sprocket_perfs(canvas, w, h, side_pad_left, top_pad)
            else:
                theme_obj.draw_photo(canvas, img, side_pad_left, top_pad, line_color)
            
            draw = ImageDraw.Draw(canvas)
            timings['canvas_paste'] = time.perf_counter() - t_canvas_start
            
            # --- EN: RENDERING PIPELINE ---
            if is_pure:
                pass
            else:
                # EN: Available width for text (Allow 95% of canvas width)
                available_width = int(new_w * 0.95)
                
                # EN: Adaptive Text Coloring for Frosted Mode
                if theme == "frosted":
                    from PIL import ImageStat
                    footer_rect = [0, new_h - bottom_splice, new_w, new_h]
                    footer_rect = [max(0, int(v)) for v in footer_rect]
                    footer_sample = canvas.crop(footer_rect).convert("L")
                    avg_lum = ImageStat.Stat(footer_sample).mean[0]
                    if avg_lum > 180:
                        main_color, sub_color = (0, 0, 0), (45, 45, 45)
                    elif avg_lum > 135:
                        main_color, sub_color = (15, 15, 15), (70, 70, 70)
                    elif avg_lum > 90:
                        main_color, sub_color = (255, 255, 255), (225, 225, 225)
                    else:
                        main_color, sub_color = (255, 255, 255), (242, 242, 242)
                
                # EN: Calculate optimal font sizes to fit available width
                actual_main_size, actual_sub_size, m_factor, s_factor = TextAdjuster.adjust(
                    draw, main_text, sub_text, available_width, 
                    base_main_font_size, base_sub_font_size, self.font_resolver,
                    main_path=resolved_main, sub_path=resolved_sub
                )

                # EN: Store metrics for UI feedback / CN: 存储用于 UI 反馈的度量信息
                timings['max_font_px'] = {
                    'main': int(base_main_font_size * m_factor / ref_factor),
                    'sub': int(base_sub_font_size * s_factor / ref_factor),
                    'main_overflow': m_factor < 0.9999,
                    'sub_overflow': s_factor < 0.9999
                }

                # EN: Vertical collision detection (CN: 垂直重叠/压图检测)
                m_font = TextAdjuster._get_font(resolved_main, actual_main_size)
                m_ascent, m_descent = m_font.getmetrics()
                
                # EN: Anchor text proportionally to image bottom (38% of space)
                total_bottom_space = inner_bottom_margin + bottom_splice
                base_y = top_pad + h + int(total_bottom_space * 0.38)
                v_gap_ref = max(actual_main_size, actual_sub_size)
                main_y = base_y - int(v_gap_ref * 0.55)
                photo_bottom = top_pad + h
                
                # Check height overflow (Overlap with photo area)
                v_overflow = (main_y - m_ascent) < photo_bottom
                timings['max_font_px']['v_overflow'] = v_overflow
                
                if v_overflow:
                    # EN: Approximate max font size that fits vertically
                    center_gap = (inner_bottom_margin + bottom_splice) // 2
                    max_v_size = int(center_gap / 1.35 / ref_factor)
                    timings['max_font_px']['main'] = min(timings['max_font_px']['main'], max_v_size)

                t_logo_start = time.perf_counter()
                TextRenderer.draw_pro_text(
                    draw, (new_w, new_h), (w, h), 
                    (side_pad_left, 0, top_pad, bottom_splice),
                    (main_text, sub_text, actual_main_size, actual_sub_size, v_offset_px),
                    data, (main_color, sub_color), self.font_resolver, self.logo_dir, timings=timings
                )
                timings['text_logo_total'] = time.perf_counter() - t_logo_start
            timings['draw_text_outer'] = time.perf_counter() - t_draw_start
            
            # --- EN: FINAL POLISH ---
            t_shadow_start = time.perf_counter()
            # EN: Disable shadow for Dark/Slate-Teal Mode to avoid edge artifacts and match user's clean aesthetic
            # CN: 深色/石板青模式下不加阴影，避免边缘白边产生（黑色阴影在暗色底色上效果不佳）
            if theme in ["dark", "frosted", "slate_teal"]:
               final_output = canvas.convert("RGBA")
            else:
                # EN: Restore high-quality shadow for preview as requested
                final_output = ShadowEngine.apply_pro_shadow(canvas, radius=20)
            timings['shadow'] = time.perf_counter() - t_shadow_start

            if target_long_edge <= 1200 and not output_dir:
                timings['total'] = time.perf_counter() - t_start
                # EN: Flatten onto matching background color
                # CN: 复合底色，避免阴影产生边缘白边（深色模式用黑底，其余用白底）
                if final_output.mode == 'RGBA':
                    flatten_bg_color = (0, 0, 0) if theme in ["dark", "slate_teal"] else (255, 255, 255)
                    bg = Image.new("RGB", final_output.size, flatten_bg_color)
                    bg.paste(final_output, mask=final_output.split()[3])
                    return bg, timings
                return final_output, timings

            if output_dir:
                t_save_start = time.perf_counter()
                os.makedirs(output_dir, exist_ok=True)
                save_name = f"GT_{os.path.basename(img_path)}"
                if not save_name.lower().endswith('.jpg'):
                    save_name = os.path.splitext(save_name)[0] + ".jpg"
                save_path = os.path.join(output_dir, save_name)

                # EN: Modular Save / CN: 模块化保存（自动处理打平与 EXIF）
                exif_bytes = ExifEditor.build_exif_bytes(img_path, data)
                out_name, f_size = ImageSaver.flatten_and_save(final_output, save_path, exif_bytes, theme=theme)
                
                timings['save'] = time.perf_counter() - t_save_start
                final_output = out_name

            timings['total'] = time.perf_counter() - t_start
            return final_output, timings

        except Exception as e:
            print(f"CN: [ERR] 渲染程序出错: {e}")
            import traceback
            traceback.print_exc()
            return None, {}

    def _prepare_strings(self, data):
        """EN: Legacy signature support (Calls Parser directly) / CN: 保留旧版签名支持"""
        show_make = data.get('show_make', 1)
        show_model = data.get('show_model', 1)
        make = str(data.get('Make') or "").strip().upper() if show_make else ""
        model = str(data.get('Model') or "").strip().upper() if show_model else ""
        
        dedup_model = model
        if make and model and model.startswith(make):
            dedup_model = model[len(make):].lstrip(" -_/") or model
            
        main_text = f"{make} {dedup_model}".strip() if make and dedup_model else (dedup_model or make)
        if "HASSELBLAD" in make: main_text = f"HASSELBLAD {dedup_model or model or make}".strip()
        
        from .branding.lens_parser import LensParser
        sub_segments = LensParser.prepare_segments(data, (0,0,0))
        sub_text = "".join([s["content"] for s in sub_segments if s["type"] == "text"])
        return main_text, sub_text






