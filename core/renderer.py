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
        self.logo_dir = bootstrap_logos(resolve_path)
        
        # EN: Handle dynamic fonts
        self.font_dir = bootstrap_fonts(resolve_path)
        self.font_resolver = FontResolver(self.font_dir, self.font_main, self.font_sub)
        
        self._setup_cairo_dll()

    def _setup_cairo_dll(self):
        """EN: Fix for cairosvg DLL loading on Windows."""
        if sys.platform == "win32":
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
        EN: Main entry point - Orchestrates the rendering pipeline.
        CN: 主渲染入口 - 调度渲染管线。
        """
        timings = kwargs.get('timing_results', {})
        t_start = time.perf_counter()
        
        try:
            # --- 阶段 0: 图像加载 ---
            if source_img:
                img = source_img
            else:
                img, load_timings = ImageLoader.load_and_preprocess(img_path, target_long_edge, manual_rotation)
                timings.update(load_timings)
            
            # --- 阶段 1: 数据准备 (上下文) ---
            ctx = self._prepare_context(img_path, data, theme, rainbow_index)
            
            # --- 阶段 2: 基础图层 (画布与主图) ---
            r_range = kwargs.get('rainbow_range', (0.0, 1.0))
            canvas, layout_results = self._draw_base_layer(img, ctx, v_offset, h_offset, rainbow_index, r_range)
            
            # --- 阶段 3: 排版与文字渲染 ---
            if not is_pure:
                if is_sample:
                    ctx["main_text"] = "SAMPLE SAMPLE"
                    ctx["sub_text"] = "SAMPLE SAMPLE | SAMPLE | SAMPLE"
                self._apply_typography(canvas, ctx, layout_results, timings)
            
            # --- 阶段 4: 后处理与导出 ---
            result = self._finalize_output(canvas, ctx, img_path, output_dir, theme, target_long_edge)
            
            timings['total'] = time.perf_counter() - t_start
            return result, timings

        except Exception as e:
            print(f"CN: [ERR] 渲染程序出错: {e}")
            import traceback
            traceback.print_exc()
            return None, {}

    def _prepare_context(self, img_path, data, theme, rainbow_index):
        """EN: Step 1 - Data Preparation / CN: 阶段 1 - 数据准备"""
        handler = MetadataHandler()
        data = handler.ensure_minimal_data(data, img_path)
        theme_obj = ThemeFactory.get_theme(theme, img_path=img_path)
        
        is_sprocket = data.get('sprocket_enabled', False)
        if is_sprocket:
            colors = SprocketEngine.get_sprocket_colors()
        else:
            colors = theme_obj.get_colors(index=rainbow_index)
            
        main_text, sub_text = LensParser.format_display_strings(data)
        data['main_text'], data['sub_text'] = main_text, sub_text
        
        return {
            'data': data, 
            'theme_obj': theme_obj, 
            'colors': colors, 
            'main_text': main_text, 
            'sub_text': sub_text, 
            'is_sprocket': is_sprocket
        }

    def _draw_base_layer(self, img, ctx, v_offset, h_offset, rainbow_index, rainbow_range):
        """EN: Step 2 - Geometry & Base Canvas / CN: 阶段 2 - 几何与基础图层"""
        w, h = img.size
        data, theme_obj = ctx['data'], ctx['theme_obj']
        layout_results = LayoutCalculator.calculate_layout(w, h, data, data.get('layout', {}), h_offset, v_offset, font_resolver=self.font_resolver)
        
        new_w, new_h = layout_results['new_w'], layout_results['new_h']
        side_pad_left, top_pad = layout_results['side_pad_left'], layout_results['top_pad']
        
        if ctx['is_sprocket']:
            canvas = Image.new('RGB', (new_w, new_h), (0, 0, 0))
            canvas.paste(img, (side_pad_left, top_pad))
            SprocketEngine.apply_sprocket_perfs(canvas, w, h, side_pad_left, top_pad)
        else:
            canvas = theme_obj.create_canvas(new_w, new_h, img=img, index=rainbow_index, t_start=rainbow_range[0], t_end=rainbow_range[1])
            theme_obj.draw_photo(canvas, img, side_pad_left, top_pad, ctx['colors'][3])
        return canvas, layout_results

    def _apply_typography(self, canvas, ctx, layout_results, timings):
        """EN: Step 3 - Typography Rendering / CN: 阶段 3 - 排版渲染"""
        draw = ImageDraw.Draw(canvas)
        data, theme_obj = ctx['data'], ctx['theme_obj']
        m_color, s_color = ctx['colors'][1], ctx['colors'][2]
        new_w, new_h = layout_results['new_w'], layout_results['new_h']
        bottom_splice = layout_results['bottom_splice']
        
        # Adaptive Color sensing
        m_color, s_color = theme_obj.resolve_adaptive_colors(canvas, [0, new_h - bottom_splice, new_w, new_h], m_color, s_color)
        
        # Font Sizing
        available_width = int(new_w * 0.95)
        actual_main_size, actual_sub_size, m_factor, s_factor = TextAdjuster.adjust(
            draw, ctx['main_text'], ctx['sub_text'], available_width, 
            layout_results['base_main_font_size'], layout_results['base_sub_font_size'], 
            self.font_resolver, main_path=layout_results['resolved_main'], sub_path=layout_results['resolved_sub']
        )
        
        ref_factor = layout_results['ref_factor']
        timings['max_font_px'] = {
            'main': int(layout_results['base_main_font_size'] * m_factor / ref_factor), 
            'sub': int(layout_results['base_sub_font_size'] * s_factor / ref_factor), 
            'main_overflow': m_factor < 0.9999, 
            'sub_overflow': s_factor < 0.9999
        }
        
        # Vertical Collision
        v_overflow, suggested_px = TextAdjuster.check_vertical_collision(
            actual_main_size, actual_sub_size, layout_results['resolved_main'], 
            layout_results['h'], layout_results['top_pad'], layout_results['inner_bottom_margin'], 
            bottom_splice, ref_factor
        )
        timings['max_font_px']['v_overflow'] = v_overflow
        if v_overflow: 
            timings['max_font_px']['main'] = min(timings['max_font_px']['main'], suggested_px)
            
        TextRenderer.draw_pro_text(
            draw, (new_w, new_h), (layout_results['w'], layout_results['h']), 
            (layout_results['side_pad_left'], 0, layout_results['top_pad'], bottom_splice), 
            (ctx['main_text'], ctx['sub_text'], actual_main_size, actual_sub_size, layout_results['font_v_offset_px']), 
            data, (m_color, s_color), self.font_resolver, self.logo_dir, 
            resolved_fonts=(layout_results['resolved_main'], layout_results['resolved_sub']), 
            timings=timings
        )

    def _finalize_output(self, canvas, ctx, img_path, output_dir, theme, target_long_edge):
        """EN: Step 4 - Post-processing & Save / CN: 阶段 4 - 后处理与保存"""
        if theme in ['dark', 'frosted', 'slate_teal']: 
            final_output = canvas.convert('RGBA')
        else: 
            final_output = ShadowEngine.apply_pro_shadow(canvas, radius=20)
            
        if target_long_edge <= 1200 and not output_dir:
            if final_output.mode == 'RGBA':
                bg = Image.new('RGB', final_output.size, (0, 0, 0) if theme in ['dark', 'slate_teal'] else (255, 255, 255))
                bg.paste(final_output, mask=final_output.split()[3])
                return bg
            return final_output
            
        if output_dir:
            save_name = f'GT_{os.path.basename(img_path)}'
            if not save_name.lower().endswith('.jpg'): 
                save_name = os.path.splitext(save_name)[0] + '.jpg'
            save_path = os.path.join(output_dir, save_name)
            exif_bytes = ExifEditor.build_exif_bytes(img_path, ctx['data'])
            out_name, _ = ImageSaver.flatten_and_save(final_output, save_path, exif_bytes, theme=theme)
            return out_name
            
        return final_output
