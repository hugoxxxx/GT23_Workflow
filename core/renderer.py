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
            
            bg_color, main_color, sub_color, line_color = self._apply_theme_colors(theme, index=rainbow_index)
            
            if data.get('sprocket_enabled', False):
                bg_color = (0, 0, 0)
                main_color = (245, 245, 245)
                sub_color = (210, 210, 210)
                line_color = (40, 40, 40)
            
            layout = data.get('layout', {})
            
            # --- EN: TYPOGRAPHY HIERARCHY ---
            t_draw_start = time.perf_counter()
            main_text, sub_text = self._prepare_strings(data)
            
            # EN: Injection for LayoutCalculator
            data['main_text'] = main_text
            data['sub_text'] = sub_text
            
            if is_sample:
                main_text = "SAMPLE SAMPLE"
                sub_text = "SAMPLE SAMPLE | SAMPLE | SAMPLE"
            
            # --- EN: CALCULATE LAYOUT (Refactored v2.4.1) / CN: 布局计算 (v2.4.1 重构) ---
            t_layout_start = time.perf_counter()
            layout_results = LayoutCalculator.calculate_layout(
                w, h, data, layout, h_offset, v_offset, font_resolver=self.font_resolver
            )
            
            side_pad_left = layout_results["side_pad_left"]
            side_pad_right = layout_results["side_pad_right"]
            top_pad = layout_results["top_pad"]
            bottom_splice = layout_results["bottom_splice"]
            new_w = layout_results["new_w"]
            new_h = layout_results["new_h"]
            inner_bottom_margin = layout_results["inner_bottom_margin"]
            
            # Typography metrics from calculator
            base_main_font_size = layout_results["base_main_font_size"]
            base_sub_font_size = layout_results["base_sub_font_size"]
            v_offset_px = layout_results["font_v_offset_px"]
            resolved_main = layout_results["resolved_main"]
            resolved_sub = layout_results["resolved_sub"]
            ref_factor = layout_results["ref_factor"]

            if data.get('sprocket_enabled', False):
                bg_color = (0, 0, 0)
            
            timings['layout_calc'] = time.perf_counter() - t_layout_start
            
            # --- EN: DRAWING ---
            t_canvas_start = time.perf_counter()
            if theme == "rainbow":
                t_range = kwargs.get('rainbow_range', (0.0, 1.0))
                canvas = self._create_fuji_rainbow_canvas(new_w, new_h, t_range[0], t_range[1])
            elif theme == "macaron":
                import hashlib
                c_idx = rainbow_index if rainbow_index >= 0 else int(hashlib.md5(img_path.encode()).hexdigest(), 16) % 9
                macaron_palette = [
                    (255, 180, 200), (210, 180, 255), (180, 220, 255), 
                    (180, 255, 220), (255, 250, 190), (255, 210, 180),
                    (200, 255, 255), (255, 220, 255), (220, 255, 180)
                ]
                c1 = macaron_palette[c_idx % 9]
                c2 = macaron_palette[(c_idx + 1) % 9]
                canvas = self._create_linear_gradient_canvas(new_w, new_h, c1, c2)
            elif theme == "sakura":
                import hashlib
                c_idx = rainbow_index if rainbow_index >= 0 else int(hashlib.md5(img_path.encode()).hexdigest(), 16) % 9
                sakura_palette = [
                    (255, 245, 247), (255, 203, 217), (255, 180, 200),
                    (255, 235, 240), (255, 190, 205), (255, 170, 190),
                    (255, 220, 235), (255, 185, 200), (255, 160, 180)
                ]
                c1 = sakura_palette[c_idx % 9]
                c2 = sakura_palette[(c_idx + 1) % 9]
                canvas = self._create_linear_gradient_canvas(new_w, new_h, c1, c2)
            elif theme == "frosted":
                canvas = self._create_frosted_canvas(img, new_w, new_h)
            elif theme == "slate_teal":
                c_top = (210, 222, 228)
                c_bottom = (125, 142, 152)
                canvas = self._create_linear_gradient_canvas(new_w, new_h, c_top, c_bottom, vertical=True, gamma=1.6)
                canvas = self._apply_matte_texture(canvas, intensity=0.06)
            else:
                canvas = Image.new("RGB", (new_w, new_h), bg_color)
            
            if theme in ["frosted", "slate_teal"]:
                self._draw_floating_photo(canvas, img, side_pad_left, top_pad, line_color)
            else:
                canvas.paste(img, (side_pad_left, top_pad))
                ImageDraw.Draw(canvas).rectangle([side_pad_left, top_pad, side_pad_left + w, top_pad + h], outline=line_color, width=1)
            
            draw = ImageDraw.Draw(canvas)
            timings['canvas_paste'] = time.perf_counter() - t_canvas_start

            # --- EN: RENDERING PIPELINE / CN: 渲染流水线 ---
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
                self._draw_pro_text(draw, new_w, w, h, side_pad_left, side_pad_right, top_pad, bottom_splice, 
                                main_text, sub_text, actual_main_size, actual_sub_size, 
                                data=data, main_color=main_color, sub_color=sub_color, 
                                use_lens_branding=use_lens_branding, timings=timings,
                                v_offset=v_offset_px)
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
                final_output = self._apply_pro_shadow(canvas, radius=20)
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
            return False

    def _apply_theme_colors(self, theme, index=0):
        """
        EN: Define theme color palettes with rainbow sequence index.
        CN: 定义调色板，支持彩虹序列索引。
        """
        if theme == "dark":
            # EN: Professional Cold Midnight Dark Mode / CN: 专业冷调蓝黑深色模式
            return (15, 16, 20), (245, 245, 245), (210, 210, 210), (45, 45, 45)
        elif theme == "macaron":
            # EN: Soft Macaron Palette / CN: 柔和马卡龙色库
            # EN: Logic handled by linear gradient canvas in process_image
            # CN: 实际方案由渲染入口的双色渐变引擎接管
            return (255, 255, 255), (32, 32, 32), (60, 60, 60), (235, 235, 235)
        elif theme == "sakura":
            # EN: Sakura Theme base colors (Refined Cherry/Rose Palette)
            # CN: 樱花主题文字：使用更柔和的“黛樱红”与“落暮粉”，以适应更淡的背景
            return (255, 245, 247), (125, 45, 65), (165, 95, 110), (255, 215, 225)
        elif theme == "rainbow":
            # EN: Saturated Fujifilm Instax Palette / CN: 高饱和富士拍立得色库
            palette = [
                (30, 50, 110), (30, 120, 200), (0, 200, 240), (140, 210, 50), 
                (255, 220, 0), (255, 140, 0), (255, 70, 60), (255, 70, 140), 
                (180, 50, 160), (100, 20, 120)
            ]
            bg = palette[index % len(palette)]
            # EN: Always use dark text (Light mode style) as requested / CN: 响应老大要求：始终使用深色文字（浅色模式审美）
            return bg, (26, 26, 26), (85, 85, 85), (255, 255, 255)
        elif theme == "frosted":
            # EN: Glassmorphism / CN: 磨砂玻璃（使用图片虚化背景，深色文字）
            return (240, 240, 240), (26, 26, 26), (85, 85, 85), (200, 200, 200)
        elif theme == "slate_teal":
            # EN: Premium Slate Gradient / CN: 石板青（极致通透石板青渐变，高对比冷白文字）
            return (210, 222, 228), (245, 245, 250), (215, 222, 228), (180, 190, 200)
        else:
            # Light
            return (255, 255, 255), (26, 26, 26), (85, 85, 85), (238, 238, 238)

    def _create_linear_gradient_canvas(self, w, h, c1, c2, vertical=False, gamma=1.3):
        """
        EN: Create high-precision linear gradient with optional gamma correction.
        CN: 创建支持伽态校正的高精度线性渐变 (支持横向/纵向)。
        gamma: >1.0 makes color transition slower at start, <1.0 makes it faster.
        """
        canvas = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(canvas)
        
        steps = h if vertical else w
        for i in range(steps):
            t = i / steps if steps > 0 else 0
            # EN: Apply gamma for organic transition / CN: 应用伽态以实现自然的模拟感过渡
            if gamma != 1.0:
                t = t ** gamma
                
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            if vertical:
                draw.line([(0, i), (w, i)], fill=(r, g, b))
            else:
                draw.line([(i, 0), (i, h)], fill=(r, g, b))
        return canvas

    def _create_frosted_canvas(self, source_img, w, h):
        """
        EN: Create glassmorphism background using blurred original.
        CN: 使用模糊后的原图生成磨砂玻璃质感背景。
        """
        from PIL import Image, ImageFilter, ImageEnhance
        
        # 1. EN: Scale and center-crop to fill target canvas / CN: 缩放并居中裁剪以填满画布
        iw, ih = source_img.size
        # EN: Avoid zero division / CN: 避免除以零
        if ih == 0 or h == 0: return source_img
        aspect = iw / ih
        target_aspect = w / h
        
        if aspect > target_aspect:
            # EN: Source is wider / CN: 原图过宽，裁剪两侧
            new_ih = h
            new_iw = int(h * aspect)
            # EN: Use cheaper resizing for background but keep quality / CN: 背景渲染可适当优化性能
            resized = source_img.resize((new_iw, new_ih), Image.Resampling.BILINEAR)
            left = (new_iw - w) // 2
            canvas = resized.crop((left, 0, left + w, h))
        else:
            # EN: Source is taller / CN: 原图过高，裁剪上下
            new_iw = w
            new_ih = int(w / aspect)
            resized = source_img.resize((new_iw, new_ih), Image.Resampling.BILINEAR)
            top = (new_ih - h) // 2
            canvas = resized.crop((0, top, w, top + h))
            
        # --- 2. EN: ENHANCED BLUR LOGIC / CN: 增强型模糊逻辑 ---
        # EN: Use proportional radius based on target size for consistent look
        # CN: 使用基于基准尺寸的比例半径，确保大图小图视觉一致
        long_edge = max(w, h)
        # EN: target ~380px blur for 4500px long edge (approx 8.5% of long edge)
        # CN: 针对 4500px 长边，应用约 380px 的模糊半径 (约 8.5% 长边)
        radius = int(long_edge * 0.085)
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=radius))
        
        # 3. EN: Brighten and add a white "frost" tint / CN: 提亮并添加白色磨砂蒙版
        canvas = ImageEnhance.Brightness(canvas).enhance(1.15)
        
        # 4. EN: Apply matte texture for premium grain feel / CN: 应用哑光纹理，增加高级感颗粒
        canvas = self._apply_matte_texture(canvas, intensity=0.05)
        
        return canvas

    def _apply_matte_texture(self, canvas, intensity=0.03):
        """
        EN: Add subtle paper-like/matte noise texture to a canvas
        CN: 为画布添加微细的纸质感/哑光磨砂噪点纹理
        """
        from PIL import Image, ImageDraw, ImageChops
        import random
        
        w, h = canvas.size
        # EN: Create a tileable noise block for performance (256x256)
        # CN: 为性能考虑，创建一个可平铺的噪点块
        tile_size = 256
        noise_tile = Image.new('L', (tile_size, tile_size))
        
        # EN: Fast noise generation / CN: 快速随机噪点生成
        pixels = [random.randint(110, 145) for _ in range(tile_size * tile_size)]
        noise_tile.putdata(pixels)
        
        # EN: Create full-size noise overlay / CN: 创建覆盖全画面的噪点层
        noise_overlay = Image.new('L', (w, h))
        for y in range(0, h, tile_size):
            for x in range(0, w, tile_size):
                noise_overlay.paste(noise_tile, (x, y))
        
        # EN: Blend noise with canvas using "Soft Light" style (manually here)
        # CN: 将噪点层以微弱比例叠加到原画布
        noise_rgb = Image.merge("RGB", (noise_overlay, noise_overlay, noise_overlay))
        return Image.blend(canvas, noise_rgb, intensity)

    def _draw_floating_photo(self, canvas, img, x, y, outline_color):
        """
        EN: Draw premium floating shadows using rounded masks and multi-layer composites.
        CN: 使用圆角遮罩和多层离屏复合绘制高级悬浮投影，彻底消除硬影边缘。
        """
        from PIL import Image, ImageFilter, ImageDraw
        
        # 0. EN: Calculate shadow scale factor
        long_edge = max(img.width, img.height)
        sf = long_edge / 2000.0
        
        # --- 1. EN: OFF-SCREEN SHADOW COMPOSITE / CN: 离屏阴影复合 ---
        # EN: Create a large RGBA buffer to composite ALL shadows first
        # CN: 创建一个大型 RGBA 缓冲区，先在这里复合所有投影层
        # EN: Increase margin to 4x blur to avoid hard-edge clipping on large offsets
        # CN: 将边距增加到 4 倍模糊半径，避免在大偏移量下出现阴影裁断硬边
        max_blur = int(200 * sf)
        margin = max_blur * 4
        shadow_buf = Image.new("RGBA", (img.width + margin * 2, img.height + margin * 2), (0, 0, 0, 0))
        
        def draw_layer(radius, opacity, off_x, off_y, spread_neg, fade_strength=0.0):
            """EN: Draw a rounded soft shadow layer with optional fading / CN: 绘制一层带可选消隐效果的圆角软阴影"""
            nonlocal shadow_buf
            from PIL import ImageChops
            # EN: Calculate mask size with Negative Spread / CN: 计算具有负扩张的遮罩尺寸
            s_w = max(10, img.width - int(spread_neg * sf) * 2)
            s_h = max(10, img.height - int(spread_neg * sf) * 2)
            
            # EN: Create a ROUNDED mask for the core shape
            mask_l = Image.new("L", (s_w, s_h), 0)
            d = ImageDraw.Draw(mask_l)
            r = int(60 * sf)
            d.rounded_rectangle([0, 0, s_w, s_h], radius=r, fill=255)
            
            # EN: Apply "Air Falloff" self-fading if requested
            # CN: 为阴影应用“空气衰减”自消隐渐变
            if fade_strength > 0:
                # EN: Generate 2D gradient via bilinear multiplication (Fast & Smooth)
                # CN: 通过双向线性相乘生成 2D 渐变 (快速且顺滑)
                h_grad = Image.new("L", (s_w, 1))
                for x_px in range(s_w): 
                    h_grad.putpixel((x_px, 0), int(255 * (1.0 - (x_px / s_w) * fade_strength)))
                h_grad = h_grad.resize((s_w, s_h))
                
                v_grad = Image.new("L", (1, s_h))
                for y_px in range(s_h):
                    v_grad.putpixel((0, y_px), int(255 * (1.0 - (y_px / s_h) * fade_strength)))
                v_grad = v_grad.resize((s_w, s_h))
                
                grad = ImageChops.multiply(h_grad, v_grad)
                mask_l = ImageChops.multiply(mask_l, grad)

            # EN: Convert L to RGBA with the specified base opacity
            mask_cv = Image.new("RGBA", (s_w, s_h), (0, 0, 0, 0))
            # EN: Use mask_l as alpha channel / CN: 使用 mask_l 作为 Alpha 通道
            mask_cv.putalpha(Image.eval(mask_l, lambda x: int(x * opacity / 255)))
            
            # EN: Position on buffer
            pos_x = margin + int(spread_neg * sf) + int(off_x * sf)
            pos_y = margin + int(spread_neg * sf) + int(off_y * sf)
            
            layer = Image.new("RGBA", shadow_buf.size, (0, 0, 0, 0))
            layer.paste(mask_cv, (pos_x, pos_y))
            layer = layer.filter(ImageFilter.GaussianBlur(radius=radius))
            
            shadow_buf = Image.alpha_composite(shadow_buf, layer)

        # --- 2. EN: STACK LAYERS (Refined Structured Stack) / CN: 堆叠投影层 (精细结构化模型) ---
        # Layer A: EN: Ambient Foundation (Soft but defined) / CN: 环境基底层 (柔和但有形)
        # EN: radius 180-220 for defined softness, moderate offset for gravity
        # CN: 中等模糊半径营造清晰的“空气感”，配合适度位移增加重力感
        draw_layer(radius=int(180 * sf), opacity=100, off_x=0, off_y=70, spread_neg=20, fade_strength=0.15)
        
        # Layer B: EN: Supporting Float / CN: 支撑悬浮层
        draw_layer(radius=int(80 * sf), opacity=140, off_x=0, off_y=40, spread_neg=10, fade_strength=0.0)
        
        # Layer C: EN: Tactile Core (Sharp Contact) / CN: 触控核心层（利落细节）
        draw_layer(radius=int(20 * sf), opacity=180, off_x=0, off_y=15, spread_neg=0, fade_strength=0.0)
        
        # --- 3. EN: PASTE TO CANVAS & FINAL PHOTO / CN: 粘贴至画布与最终照片 ---
        canvas.paste(shadow_buf, (x - margin, y - margin), shadow_buf)
        canvas.paste(img, (x, y))

    def _create_fuji_rainbow_canvas(self, w, h, t_start=0, t_end=1):
        """
        EN: Generate a global rainbow slice for the Rainbow theme using range [t_start, t_end].
        CN: 使用范围 [t_start, t_end] 为“彩虹”主题生成全局彩虹切片。
        """
        canvas = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(canvas)
        
        # EN: Vibrant & High-Saturation Fuji Rainbow palette (Recovered from "Grey" feedback)
        # CN: 高饱和度“真·鲜艳”富士彩虹色谱（针对“太灰”反馈的最终校准）
        colors = [
            (255, 110, 110),  # Vibrant Coral Red / 鲜珊瑚红
            (255, 180, 70),   # Vibrant Gold Orange / 鲜亮金橙
            (255, 230, 80),   # Vibrant Sunny Yellow / 鲜亮阳光黄
            (120, 240, 120),  # Vibrant Mint Green / 鲜嫩薄荷绿
            (100, 230, 245),  # Vibrant Sky Cyan / 鲜碧空青
            (100, 160, 255),  # Vibrant Ultramarine / 鲜亮群青
            (200, 100, 255)   # Vibrant Electric Violet / 鲜亮紫罗兰
        ]
        
        # EN: Range is now passed directly as floats / CN: 范围现在作为浮点数直接传入
        t_start = max(0.0, min(1.0, float(t_start)))
        t_end = max(0.0, min(1.0, float(t_end)))
        
        for x in range(w):
            # EN: Map the local pixel position to the global rainbow position
            # CN: 将局部像素位置映射到全局彩虹位置
            pos = t_start + (x / w) * (t_end - t_start)
            
            # EN: Find colors to interpolate
            # CN: 寻找插值颜色
            num_segments = len(colors) - 1
            scaled_pos = pos * num_segments
            idx = int(scaled_pos)
            next_idx = min(idx + 1, num_segments)
            inner_t = scaled_pos - idx
            
            c1 = colors[idx]
            c2 = colors[next_idx]
            
            r = int(c1[0] + (c2[0] - c1[0]) * inner_t)
            g = int(c1[1] + (c2[1] - c1[1]) * inner_t)
            b = int(c1[2] + (c2[2] - c1[2]) * inner_t)
            
            # EN: Draw horizontal gradient line by line
            # CN: 逐行绘制横向渐变
            draw.line([(x, 0), (x, h)], fill=(r, g, b))
            
        return canvas

    def _create_rainbow_canvas(self, w, h):
        """
        EN: Generate a premium Fujifilm Instax Wide style rainbow gradient.
        CN: 生成高级感富士拍立得 Wide 风格彩虹渐变。
        """
        canvas = Image.new("RGB", (w, h))
        
        # EN: Fujifilm Instax Wide Rainbow Palette (Soft Macaron tones)
        # CN: 富士拍立得 Wide 彩虹调色板（马卡龙色系）
        colors = [
            (255, 180, 200), # Soft Pink / 粉
            (210, 180, 255), # Lavender / 紫
            (180, 220, 255), # Sky Blue / 蓝
            (180, 255, 220), # Mint / 绿
            (255, 250, 190), # Soft Yellow / 黄
            (255, 210, 180)  # Peach / 橙
        ]
        
        draw = ImageDraw.Draw(canvas)
        
        # EN: Use 30-degree diagonal soft gradient for more dynamic look
        # CN: 使用 30 度斜向软渐变，增加动态感
        for y in range(h):
            # EN: Calculate gradient position based on X and Y to create diagonal effect
            # CN: 根据 X 和 Y 计算渐变位置，创建斜向效果
            # Formula: (y + x * tan(30)) / (h + w * tan(30))
            # simplified to (y + x*0.58)
            tan30 = 0.577
            max_val = h + w * tan30
            
            # Since we draw line by line, we interpolate along the line
            for x in [0, w-1]: # We only need to interpolate for the full width if needed
                pass
                
            # Optimized Horizontal-ish with slight shift
            pos = y / h
            idx = int(pos * (len(colors) - 1))
            next_idx = min(idx + 1, len(colors) - 1)
            inner_pos = (pos * (len(colors) - 1)) - idx
            
            c1 = colors[idx]
            c2 = colors[next_idx]
            
            r = int(c1[0] + (c2[0] - c1[0]) * inner_pos)
            g = int(c1[1] + (c2[1] - c1[1]) * inner_pos)
            b = int(c1[2] + (c2[2] - c1[2]) * inner_pos)
            
            draw.line([(0, y), (w, y)], fill=(r, g, b))
            
        # EN: Use a smaller radius to keep the "stripe" structure but soft
        # CN: 使用较小的模糊半径，保持“条纹感”且柔和
        return canvas.filter(ImageFilter.GaussianBlur(radius=15))



    def _prepare_strings(self, data):
        """EN: Legacy signature support / CN: 保留旧版签名支持"""
        # EN: Handle visibility toggles / CN: 处理显示开关
        show_make = data.get('show_make', 1)
        show_model = data.get('show_model', 1)

        make_raw = str(data.get('Make') or "").strip() if show_make else ""
        model_raw = str(data.get('Model') or "").strip() if show_model else ""
        make = make_raw.upper()
        model = model_raw.upper()

        # EN: Deduplicate brand prefix in model
        dedup_model = model
        if make and model and model.startswith(make):
            dedup_model = model[len(make):].lstrip(" -_/") or model

        if "HASSELBLAD" in make:
            main_text = f"HASSELBLAD {dedup_model or model or make}".strip()
        else:
            main_text = f"{make} {dedup_model}".strip() if make and dedup_model else (dedup_model or make)
        
        sub_segments = LensParser.prepare_segments(data, (0,0,0))
        sub_text = "".join([s["content"] for s in sub_segments if s["type"] == "text"])
        return main_text, sub_text

    def _draw_pro_text(self, draw, new_w, w, h, side_pad_left, side_pad_right, top_pad, bottom_splice, main_text, sub_text, m_size, s_size, data=None, main_color=None, sub_color=None, use_lens_branding=True, timings=None, v_offset=0):
        if timings is None: timings = {}
        
        # v2.4.1: Sprocket Mode Logic
        spkt_on = data.get('sprocket_enabled', False) if data else False
        
        # EN: Use provided colors or fallback to defaults
        # CN: 使用提供的颜色，或回退至默认值
        m_color = main_color or self.main_color
        s_color = sub_color or self.sub_color
        
        # EN: Force colors for Sprocket Mode (RGB for stability)
        if spkt_on:
            m_color = (255, 120, 0) # Exposure Orange
            s_color = (235, 235, 235) # Luminous White
        
        # EN: Detect CJK characters and resolve paths / CN: 检测 CJK 字符并解析路径
        # EN: v2.4.1 - Prioritize manual UI font selection over automatic resolution
        # CN: v2.4.1 - 优先使用 UI 手动选择的字体，若为 Default 则走自动识别
        resolved_main, resolved_sub = self.font_resolver.resolve(main_text, sub_text)
        
        if data:
            manual_main = data.get('font_main_path', 'Default')
            manual_sub = data.get('font_sub_path', 'Default')
            
            if manual_main != 'Default':
                resolved_main = manual_main
            if manual_sub != 'Default':
                resolved_sub = manual_sub

        # --- EN: TEXT SPACING RESOLUTION / CN: 文字间距解析 ---
        # EN: Scale spacing relative to image's long edge for resolution consistency
        # CN: 间距随照片长边等比缩放，确保在不同分辨率下观感一致
        img_long_edge = max(w, h)
        spacing_px = int(data['layout'].get('font_spacing_scale', 0) * img_long_edge)

        # EN: Positioning Logic
        inner_bottom_margin = 0
        if spkt_on:
            # EN: Physics-accurate 135 edge channel positioning (1.0mm from edge)
            # CN: 物理精确的 135 边缘通道定位：距离胶片边缘 1.0mm
            px_per_mm = min(new_w - side_pad_left - side_pad_right, h) / 24.0
            
            main_draw_pos = (new_w // 2, int(1.0 * px_per_mm) + v_offset)
            sub_draw_pos = (new_w // 2, (top_pad + h + bottom_splice) - int(1.0 * px_per_mm) + v_offset)
            
            # EN: Resize fonts for 2.0mm edge channel (Standard 1.6mm physical height)
            target_px = int(1.6 * px_per_mm)
            m_size = min(m_size, target_px)
            s_size = min(s_size, target_px)
        else:
            v_gap_ref = max(m_size, s_size)
            
            # EN: Fallback to dynamic default if 0 / CN: 如果为 0 则回退到动态默认值
            actual_gap = spacing_px if spacing_px > 0 else int(v_gap_ref * 1.3)
            
            base_y = top_pad + h + (inner_bottom_margin + bottom_splice) // 2 + v_offset
            main_draw_pos = (new_w // 2, base_y - int(actual_gap * 0.42))
            sub_draw_pos = (new_w // 2, base_y + int(actual_gap * 0.58))

        # --- EN: CAMERA LOGO RENDERING / CN: 相机 LOGO 渲染 ---
        logo_drawn = False
        # EN: Only draw logo if Model visibility is ON
        # CN: 仅在型号可见性开启时绘制 Logo
        if data and data.get('show_model', 1):
            make = str(data.get('Make') or "").strip()
            model = str(data.get('Model') or "").strip()
            logo_path = LogoFinder.find_logo_path(make, model, self.logo_dir)
            
            if logo_path:
                t_logo_sub_start = time.perf_counter()
                try:
                    # EN: cairosvg is now imported at top level or handled gracefully
                    # CN: cairosvg 现在在顶层导入
                    from .typography.engine import TypoEngine
                    resolved_main_font = TypoEngine._resolve_font_path(resolved_main)
                    main_font = TextAdjuster._get_font(resolved_main_font, m_size)
                    
                    # EN: Calculate typical font height for scaling / CN: 计算典型字体高度用于缩放
                    ascent, descent = main_font.getmetrics()
                    target_h = ascent + descent
                    
                    if logo_path.lower().endswith(".svg"):
                        # EN: Render SVG at high res first to find paths precisely
                        # CN: 先以较高分辨率渲染 SVG 以精准获取路径边界
                        png_data = cairosvg.svg2png(url=logo_path, output_height=target_h * 2)
                        logo_img = Image.open(io.BytesIO(png_data))
                    else:
                        # EN: Load PNG/other formats directly / CN: 直接加载 PNG 等其他格式
                        logo_img = Image.open(logo_path).convert("RGBA")
                    
                    # EN: Step 1 - Crop to actual content (Ink Area)
                    # CN: 第一步 - 裁剪至实际墨迹区域（去除所有周围留白）
                    bbox = logo_img.getbbox()
                    if bbox:
                        logo_img = logo_img.crop(bbox)
                    
                    # EN: Step 2 - Scale the "Ink" to match target text height
                    # CN: 第二步 - 将“墨迹”等比缩放至目标文字高度
                    orig_w, orig_h = logo_img.size
                    if orig_h > 0:
                        scaled_w = int(orig_w * (target_h / orig_h))
                        logo_img = logo_img.resize((scaled_w, target_h), Image.Resampling.LANCZOS)

                    # --- EN: LOGO INTELLIGENT TINTING (v2.4.0 Original) / CN: LOGO 智能着色 ---
                    # EN: If theme color is NOT black, adapt dark parts to match while preserving brand colors
                    # CN: 如果文字颜色不是黑色，则将 Logo 暗部适配为该颜色，同时保留其品牌特有色彩
                    is_black_theme = (m_color[0] < 40 and m_color[1] < 40 and m_color[2] < 40)
                    if not is_black_theme:
                        if logo_img.mode != 'RGBA': logo_img = logo_img.convert('RGBA')
                        # EN: Pixel-level scan to protect color brands while tinting "ink" parts
                        # CN: 像素级扫描，在染色“墨迹”部分的同时保护徕卡红等专业标识
                        pixels = list(logo_img.getdata())
                        new_pixels = []
                        for r, g, b, a in pixels:
                            # EN: Identify dark neutral pixels (potential candidates for theme tinting)
                            # CN: 识别暗中性色像素（可能是黑色文字或线条）
                            is_dark = (r < 180 and g < 180 and b < 180) # EN: Wider range / CN: 更宽的识别范围
                            is_neutral = (abs(r-g) < 40 and abs(g-b) < 40)
                            if is_dark and is_neutral:
                                # EN: Tint to theme color / CN: 染色为主题色
                                new_pixels.append((*m_color, a))
                            else:
                                # EN: Preserve brand colors (e.g. Leica Red, Nikon Yellow)
                                # CN: 保留品牌特有色彩
                                new_pixels.append((r, g, b, a))
                        logo_img.putdata(new_pixels)

                    # EN: Center horizontally, align vertically with text pos
                    # CN: 水平居中，垂直与文字位置对齐
                    logo_x = (new_w - logo_img.width) // 2
                    logo_y = main_draw_pos[1] - logo_img.height // 2
                    
                    # EN: Paste with alpha mask / CN: 带透明蒙版粘贴
                    draw._image.paste(logo_img, (logo_x, logo_y), logo_img)
                    
                    logo_drawn = True
                    timings['logo_render'] = time.perf_counter() - t_logo_sub_start
                except Exception as e:
                    print(f"CN: [!] Logo 渲染失败 fallback to text: {e}")

        # EN: Text drawing / CN: 文字绘制
        t_text_sub_start = time.perf_counter()
        try:
            from .typography.engine import TypoEngine
            
            def draw_advanced_text(text, target_pos, font_path, size, color, key_prefix, spacing=0):
                if "LEICA-1050" in str(font_path).upper():
                    # EN: Generate raw PNG composite
                    # For PNG fonts, we use default spacing
                    png_img = TypoEngine.draw_png_text(text, "assets/fonts/1050", spacing_ratio=0.15, color=color)
                    
                    # EN: Scaling: The PNG engine uses its own ref_h. We need to match it to 'size'
                    # CN: 缩放：PNG 引擎有自己的参考高度，我们需要将其缩放至 UI 指定的 'size'
                    current_canvas_h = png_img.height
                    target_canvas_h = int(size)
                    
                    if current_canvas_h > 0:
                        final_w = int(png_img.width * (target_canvas_h / current_canvas_h))
                        png_img = png_img.resize((final_w, target_canvas_h), Image.Resampling.LANCZOS)
                    
                    # --- EN: WIDTH CONSTRAINT REINFORCEMENT (v2.4.1) / CN: 宽度约束补强 ---
                    # EN: Calculate safe width and shrink if necessary
                    # CN: 计算安全宽度，如果超标则强制二次缩放
                    max_allowed_w = int(new_w - side_pad_left - side_pad_right - 40) # 40px buffer
                    if png_img.width > max_allowed_w:
                        shrink_ratio = max_allowed_w / png_img.width
                        new_h = int(png_img.height * shrink_ratio)
                        png_img = png_img.resize((max_allowed_w, new_h), Image.Resampling.LANCZOS)

                    # EN: Paste centered / CN: 居中粘贴
                    paste_x = int(target_pos[0] - png_img.width // 2)
                    paste_y = int(target_pos[1] - png_img.height // 2)
                    draw._image.paste(png_img, (paste_x, paste_y), png_img)
                else:
                    # EN: Standard Vector Rendering / CN: 标准矢量渲染
                    TypoEngine.draw_mixed_text(draw, target_pos, [{"type": "text", "content": text, "color": color}], font_path, size, color, timings=timings, key_prefix=key_prefix)

            # EN: Draw Main Text (Camera) / CN: 绘制主标题（相机）
            if not logo_drawn:
                draw_advanced_text(main_text, main_draw_pos, resolved_main, m_size, m_color, 'text_main')
            
            # EN: Draw Sub Text (Lens + Info) / CN: 绘制副标题（镜头+参数）
            # EN: We handle Zeiss T* highlighting by passing segments to draw_mixed_text or handling it in draw_advanced
            if "LEICA-1050" in str(resolved_sub).upper():
                # EN: PNG engine doesn't support mixed colors yet, use sub_text
                draw_advanced_text(sub_text, sub_draw_pos, resolved_sub, s_size, s_color, 'text_sub')
            else:
                sub_segments = LensParser.prepare_segments(data, s_color, use_lens_branding=use_lens_branding)
                TypoEngine.draw_mixed_text(draw, sub_draw_pos, sub_segments, resolved_sub, s_size, s_color, timings=timings, key_prefix='text_sub')

        except Exception as e:
            import traceback
            traceback.print_exc()
            if not logo_drawn:
                draw.text(main_draw_pos, main_text, fill=m_color, anchor="mm")
            # Fallback for sub_text
            try:
                draw.text(sub_draw_pos, sub_text, fill=s_color, anchor="mm")
            except:
                pass
        timings['text_render_pure'] = time.perf_counter() - t_text_sub_start




    def _apply_pro_shadow(self, canvas, radius=20):
        shadow_margin = 80
        # EN: Use transparent black (0,0,0,0) to avoid white corners on compression
        # CN: 使用透明黑 (0,0,0,0) 作为基色，防止压缩后出现白角
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (0, 0, 0, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 140))
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 10)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.GaussianBlur(radius=radius))
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas

    def _apply_pro_shadow_fast(self, canvas, radius=5):
        # EN: Fast version for preview using BoxBlur
        # CN: 预览专用快速版，使用 BoxBlur
        shadow_margin = 60
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (0, 0, 0, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 120))
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 6)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.BoxBlur(radius=radius))
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas






