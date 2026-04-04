import os
import io
import sys
import shutil
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from utils.config_manager import config_manager

try:
    import cairosvg
except ImportError:
    cairosvg = None

class FilmRenderer:
    """
    EN: Pro-grade renderer with dynamic typography hierarchy.
    CN: 中英双语：具备动态字号层级感的高级渲染器。
    """
    def __init__(self, font_main="assets/fonts/palab.ttf", font_sub="assets/fonts/gara.ttf"):
        self.font_main = self._resolve_path(font_main)
        self.font_sub = self._resolve_path(font_sub)
        self.bg_color = (255, 255, 255)
        self.main_color = (26, 26, 26)   
        self.sub_color = (85, 85, 85)
        self.border_line_color = (238, 238, 238)
        
        # EN: Handle external logos (next to EXE) vs internal assets (dev/MEIPASS)
        # CN: 处理外置 Logo 资源（EXE 同级目录）与内置资源（开发环境/MEIPASS）
        self.logo_dir = bootstrap_logos(self._resolve_path)
        
        self._setup_cairo_dll()

    def _resolve_path(self, relative_path):
        """EN: Resolves relative paths for both source and bundled EXE (PyInstaller).
           CN: 兼容源码模式与 PyInstaller 一项打包模式的路径解析。"""
        if os.path.isabs(relative_path):
            return relative_path
            
        # 1. EN: Check PyInstaller temporary extraction folder / CN: 检查 PyInstaller 临时解压目录
        if hasattr(sys, '_MEIPASS'):
            bundle_path = os.path.join(sys._MEIPASS, relative_path)
            if os.path.exists(bundle_path):
                return bundle_path
        
        # 2. EN: Check project root (for standard script run or onedir)
        # CN: 检查项目根目录（标准脚本运行或单文件夹打包模式）
        # EN: We assume renderer.py is in project_root/core/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_path = os.path.join(base_dir, relative_path)
        if os.path.exists(source_path):
            return source_path
            
        # 3. EN: Fallback to relative to CWD / CN: 降级回退至 CWD 相对路径
        return relative_path

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
                    theme="light", is_pure=False, rainbow_index=0, rainbow_total=1, is_sample=False, 
                    source_img=None, output_prefix="", **kwargs):
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
                t_load_start = time.perf_counter()
                # EN: Use draft mode for faster loading if it's a preview
                # CN: 如果是预览模式，使用 draft 模式加速加载
                img = Image.open(img_path)
                if target_long_edge <= 1200 and img.format == 'JPEG':
                    # EN: Target approx 2x preview size for draft to keep some head room
                    # CN: 为 draft 设置约 2 倍预览尺寸的目标，保留一定的余量
                    img.draft(img.mode, (target_long_edge * 2, target_long_edge * 2))
                
                # EN: Handle EXIF orientation automatically / CN: 自动处理 EXIF 旋转信息
                img = ImageOps.exif_transpose(img)
                
                # EN: Apply manual rotation (0, 90, 180, 270) / CN: 应用手动旋转
                if manual_rotation != 0:
                    img = img.rotate(-manual_rotation, expand=True)

                if img.mode != "RGB": img = img.convert("RGB")
                timings['load_rotate'] = time.perf_counter() - t_load_start

                t_resize_start = time.perf_counter()
                img = self._smart_resize(img, target_long_edge)
                timings['resize'] = time.perf_counter() - t_resize_start
            
            w, h = img.size
            
            # --- EN: THEME SETUP / CN: 主题颜色设置 ---
            t_layout_start = time.perf_counter()
            # EN: Support rainbow_index for sequential coloring
            bg_color, main_color, sub_color, line_color = self._apply_theme_colors(theme, index=rainbow_index)
            
            # --- EN: DATA INTEGRITY CHECK ---
            layout = data.get('layout', {})
            layout_name = layout.get('name', 'CUSTOM')
            side_ratio = layout.get('side', 0.04)
            top_ratio = layout.get('top', side_ratio)
            bottom_ratio = layout.get('bottom', 0.13)
            font_base_scale = layout.get('font_scale', 0.032)
            
            # --- EN: CALCULATE SPACING ---
            side_pad = int(w * side_ratio)
            top_pad = int(w * top_ratio)
            bottom_splice = int(h * bottom_ratio)
            
            new_w, new_h = w + (side_pad * 2), h + top_pad + side_pad + bottom_splice
            timings['layout_calc'] = time.perf_counter() - t_layout_start
            
            # --- EN: DRAWING ---
            t_canvas_start = time.perf_counter()
            # EN: Rainbow mode uses a global sliced gradient canvas
            # CN: 彩虹模式使用全局分段横向渐变画布
            # EN: Rainbow modes (Macaron/Rainbow) use different gradient engines
            # CN: 彩虹模式：区分长卷系统（彩虹）与随机渐变系统（马卡龙）
            if theme == "rainbow":
                # EN: Pass specific t_start/t_end for physical continuity / CN: 传递具体的起始/结束比例以实现物理连贯
                t_range = kwargs.get('rainbow_range', (0.0, 1.0))
                canvas = self._create_fuji_rainbow_canvas(new_w, new_h, t_range[0], t_range[1])
            elif theme == "macaron":
                # EN: Dynamic 2-color gradient for Macaron / CN: 马卡龙系统：动态双色随机渐变
                macaron_palette = [
                    (255, 180, 200), (210, 180, 255), (180, 220, 255), 
                    (180, 255, 220), (255, 250, 190), (255, 210, 180),
                    (200, 255, 255), (255, 220, 255), (220, 255, 180)
                ]
                # EN: Resolve color index (Must be deterministic)
                if rainbow_index >= 0:
                    c_idx = rainbow_index
                else:
                    import hashlib
                    c_idx = int(hashlib.md5(img_path.encode()).hexdigest(), 16) % len(macaron_palette)

                c1 = macaron_palette[c_idx % len(macaron_palette)]
                c2 = macaron_palette[(c_idx + 1) % len(macaron_palette)]
                canvas = self._create_linear_gradient_canvas(new_w, new_h, c1, c2)
            elif theme == "sakura":
                # EN: Sakura Pink Palette (Varying intensities for better visual distinction)
                # CN: 樱花粉色库：优化明度，让整体色调更轻盈（响应老大反馈：调淡左侧和暗部）
                sakura_palette = [
                    # EN: Interleaved shades (Pale, Soft, Classic) - Lightened for better blending
                    # CN: 交织色序 (淡妆 -> 柔粉 -> 经典)，整体上移明度，确保背景轻盈
                    (255, 245, 247), (255, 203, 217), (255, 180, 200),
                    (255, 235, 240), (255, 190, 205), (255, 170, 190),
                    (255, 220, 235), (255, 185, 200), (255, 160, 180)
                ]
                # EN: Resolve color index (Deterministic based on position/path)
                if rainbow_index >= 0:
                    c_idx = rainbow_index
                else:
                    import hashlib
                    c_idx = int(hashlib.md5(img_path.encode()).hexdigest(), 16) % len(sakura_palette)

                # EN: Use a step of 2 to ensure we jump between distinctive shades
                # CN: 使用跨步采样，确保渐变色对具备明显的明度或色相差
                base_idx = c_idx % len(sakura_palette)
                next_idx = (base_idx + 1) % len(sakura_palette)
                
                c1 = sakura_palette[base_idx]
                c2 = sakura_palette[next_idx]
                canvas = self._create_linear_gradient_canvas(new_w, new_h, c1, c2)
            else:
                canvas = Image.new("RGB", (new_w, new_h), bg_color)
            
            canvas.paste(img, (side_pad, top_pad))
            draw = ImageDraw.Draw(canvas)
            
            # EN: 1px inner border
            draw.rectangle([side_pad, top_pad, side_pad + w, top_pad + h], outline=line_color, width=1)
            timings['canvas_paste'] = time.perf_counter() - t_canvas_start
            
            # --- EN: TYPOGRAPHY HIERARCHY ---
            t_draw_start = time.perf_counter()
            main_text, sub_text = self._prepare_strings(data)
            
            if is_sample:
                main_text = "SAMPLE SAMPLE"
                sub_text = "SAMPLE SAMPLE | SAMPLE | SAMPLE"
            
            # --- EN: RENDERING PIPELINE / CN: 渲染流水线 ---
            if is_pure:
                pass
            else:
                long_edge = max(new_w, new_h)
                base_main_font_size = int(long_edge * font_base_scale)
                base_sub_font_size = int(base_main_font_size * 0.78)

                available_width = new_w - (side_pad * 4)
                actual_main_size, actual_sub_size = self._adjust_font_sizes_to_fit(
                    draw, main_text, sub_text, available_width, 
                    base_main_font_size, base_sub_font_size
                )

                t_logo_start = time.perf_counter()
                self._draw_pro_text(draw, new_w, h, side_pad, top_pad, bottom_splice, 
                                main_text, sub_text, actual_main_size, actual_sub_size, 
                                data=data, main_color=main_color, sub_color=sub_color, timings=timings)
                timings['text_logo_total'] = time.perf_counter() - t_logo_start
            timings['draw_text_outer'] = time.perf_counter() - t_draw_start
            
            # --- EN: FINAL POLISH ---
            t_shadow_start = time.perf_counter()
            # EN: Restore high-quality shadow for preview as requested / CN: 按要求还原预览图的高质量阴影
            final_output = self._apply_pro_shadow(canvas, radius=20)
            timings['shadow'] = time.perf_counter() - t_shadow_start

            if target_long_edge <= 1200 and not output_dir:
                timings['total'] = time.perf_counter() - t_start
                # EN: Flatten onto white background to match legacy JPG preview look
                # CN: 复合纯白底色，以匹配旧版 JPG 预览图的视觉效果
                if final_output.mode == 'RGBA':
                    bg = Image.new("RGB", final_output.size, (255, 255, 255))
                    bg.paste(final_output, mask=final_output.split()[3])
                    return bg
                return final_output

            t_save_start = time.perf_counter()
            result = self._save_with_limit(final_output, img_path, output_dir, data, target_long_edge, layout_name, output_prefix=output_prefix)
            timings['save'] = time.perf_counter() - t_save_start

            timings['total'] = time.perf_counter() - t_start
            return result

        except Exception as e:
            print(f"CN: [ERR] 渲染程序出错: {e}")
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
        else:
            # Light
            return (255, 255, 255), (26, 26, 26), (85, 85, 85), (238, 238, 238)

    def _create_linear_gradient_canvas(self, w, h, c1, c2):
        """
        EN: Simple 2-color horizontal gradient for Macaron Mode.
        CN: 马卡龙模式专用的双色线性渐变画布。
        """
        canvas = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(canvas)
        for x in range(w):
            t = x / w
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            draw.line([(x, 0), (x, h)], fill=(r, g, b))
        return canvas

    def _create_fuji_rainbow_canvas(self, w, h, t_start, t_end):
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
        """EN: Dual-Engine Typography / CN: 胶片/数码双引擎排版"""
        # EN: Handle visibility toggles / CN: 处理显示开关
        show_make = data.get('show_make', 1)
        show_model = data.get('show_model', 1)

        make_raw = str(data.get('Make') or "").strip() if show_make else ""
        model_raw = str(data.get('Model') or "").strip() if show_model else ""
        make = make_raw.upper()
        model = model_raw.upper()

        # EN: Deduplicate brand prefix in model (e.g., CANON CANON EOS R6 -> CANON EOS R6)
        # CN: 去重型号里的品牌前缀
        dedup_model = model
        if make and model and model.startswith(make):
            dedup_model = model[len(make):].lstrip(" -_/") or model

        if "HASSELBLAD" in make:
            camera_text = f"HASSELBLAD {dedup_model or model or make}".strip()
        else:
            if make and dedup_model:
                camera_text = f"{make} {dedup_model}".strip()
            else:
                camera_text = dedup_model or make
        
        info_parts = []
        is_digi = data.get('is_digital', False)
        
        # 1. EN: Lens / CN: 镜头
        if data.get('show_lens', 1) and data.get('LensModel'): 
            info_parts.append(data['LensModel'])
        
        # 2. EN: Focal Length (Digital only) / CN: 焦距 (仅数码)
        if data.get('show_lens', 1) and is_digi and data.get('FocalLength'):
            info_parts.append(data['FocalLength'])
        
        # 3. EN: Exposure (Shutter + Aperture + ISO for Digital)
        # CN: 曝光组件 (快门 + 光圈 + 数码模式下的 ISO)
        params = []
        if data.get('show_shutter', 1) and data.get('ExposureTimeStr'): params.append(f"{data['ExposureTimeStr']}s")
        if data.get('show_aperture', 1) and data.get('FNumber'): params.append(f"f/{data['FNumber']}")
        if data.get('show_iso', 1) and is_digi and data.get('ISO'): params.append(f"ISO {data['ISO']}")
        if params: info_parts.append(" ".join(params))
        
        # 4. EN: Film (Film mode only) / CN: 胶片名称 (仅胶片模式)
        if not is_digi:
            film_name = str(data.get('Film') or "").upper()
            if film_name: info_parts.append(film_name)
        
        return camera_text, "  |  ".join(info_parts)

    def _draw_pro_text(self, draw, new_w, h, side_pad, top_pad, bottom_splice, main_text, sub_text, m_size, s_size, data=None, main_color=None, sub_color=None, timings=None):
        if timings is None: timings = {}
        # EN: Use provided colors or fallback to defaults
        # CN: 使用提供的颜色，或回退至默认值
        m_color = main_color or self.main_color
        s_color = sub_color or self.sub_color
        
        # EN: Detect CJK characters and resolve paths / CN: 检测 CJK 字符并解析路径
        resolved_main, resolved_sub = self._resolve_font_paths(main_text, sub_text)

        # EN: Vertical center of the white area / CN: 白色区域垂直中心
        base_y = top_pad + h + (side_pad + bottom_splice) // 2
        
        main_draw_pos = (new_w // 2, base_y - int(bottom_splice * 0.15))
        sub_draw_pos = (new_w // 2, base_y + int(bottom_splice * 0.28))

        # --- EN: CAMERA LOGO RENDERING / CN: 相机 LOGO 渲染 ---
        logo_drawn = False
        # EN: Only draw logo if Model visibility is ON
        # CN: 仅在型号可见性开启时绘制 Logo
        if data and data.get('show_model', 1):
            make = str(data.get('Make') or "").strip()
            model = str(data.get('Model') or "").strip()
            logo_path = self._find_logo_path(make, model)
            
            if logo_path:
                t_logo_sub_start = time.perf_counter()
                try:
                    # EN: cairosvg is now imported at top level or handled gracefully
                    # CN: cairosvg 现在在顶层导入
                    from .typo_engine import TypoEngine
                    resolved_main_font = TypoEngine._resolve_font_path(resolved_main)
                    main_font = self._get_font(resolved_main_font, m_size)
                    
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

                    # --- EN: LOGO INTELLIGENT TINTING / CN: LOGO 智能着色 ---
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
                            is_dark = (r < 100 and g < 100 and b < 100)
                            is_neutral = (abs(r-g) < 30 and abs(g-b) < 30)
                            if is_dark and is_neutral:
                                # EN: Tint to theme color but keep original alpha / CN: 染色为主题色，保留原始透明度
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
                    
                    # DEBUG: Draw center line
                    # draw.line([(new_w // 2, top_pad + h), (new_w // 2, new_h)], fill="red", width=2)

                    logo_drawn = True
                    timings['logo_render'] = time.perf_counter() - t_logo_sub_start
                except Exception as e:
                    print(f"CN: [!] Logo 渲染失败 fallback to text: {e}")

        # --- EN: ZEISS T* HIGHLIGHT / CN: 蔡司 T* 红色高亮 ---
        # Zeiss red color: #ed1f25 -> (237, 31, 37)
        sub_colors = s_color
        if "T*" in sub_text:
            sub_colors = [s_color] * len(sub_text)
            zeiss_red = (237, 31, 37)
            i = 0
            while i < len(sub_text) - 1:
                if sub_text[i:i+2] == "T*":
                    sub_colors[i] = zeiss_red
                    sub_colors[i+1] = zeiss_red
                    i += 2
                else:
                    i += 1

        # EN: Text drawing / CN: 文字绘制
        t_text_sub_start = time.perf_counter()
        try:
            from .typo_engine import TypoEngine
            if not logo_drawn:
                TypoEngine.draw_text(draw, main_draw_pos, main_text, resolved_main, m_size, m_color, timings=timings, key_prefix='text_main')
            TypoEngine.draw_text(draw, sub_draw_pos, sub_text, resolved_sub, s_size, sub_colors, timings=timings, key_prefix='text_sub')
        except Exception as e:
            if not logo_drawn:
                draw.text(main_draw_pos, main_text, fill=m_color, anchor="mm")
            # Fallback for sub_text: just use the base sub_color as a single fill
            draw.text(sub_draw_pos, sub_text, fill=s_color, anchor="mm")
        timings['text_render_pure'] = time.perf_counter() - t_text_sub_start


    def _find_logo_path(self, make, model):
        """EN: Universal case-insensitive logo lookup.
           CN: 通用的不区分大小写 Logo 检索逻辑。支持“品牌-型号”自动识别。"""
        if not os.path.exists(self.logo_dir):
            return None
        
        # 1. EN: Prepare and normalize search metadata / CN: 准备并正则化搜索信息
        make_u = str(make or "").upper().strip()
        model_u = str(model or "").upper().strip()
        if not model_u: return None

        # EN: Function to strip non-alphanumeric for extreme fuzzy matching
        # CN: 定义简单的正则化函数，去除空格和符号，用于极端模糊匹配
        def _norm(s): return "".join(c for c in s if c.isalnum())
        norm_model = _norm(model_u)

        search_stems = []
        if make_u:
            search_stems.append(f"{make_u}-{model_u}")
            search_stems.append(f"{make_u}_{model_u}")
            search_stems.append(f"{make_u}{model_u}")
        search_stems.append(model_u)
            
        try:
            files = os.listdir(self.logo_dir)
            supported_exts = [".svg", ".png", ".jpg", ".jpeg"]
            file_map = {f.upper(): f for f in files if any(f.lower().endswith(ext) for ext in supported_exts)}
            
            # 2. EN: First pass - strict matching with candidate stems
            # CN: 第一轮：基于候选名的严格匹配
            for stem in search_stems:
                for ext in [".svg", ".png", ".jpg"]:
                    target_key = f"{stem}{ext.upper()}"
                    if target_key in file_map:
                        return os.path.join(self.logo_dir, file_map[target_key])
            
            # 3. EN: Second pass - Suffix matching for "BRAND-MODEL" pattern
            # CN: 第二轮：针对“品牌-型号”规则的后缀匹配
            for file_key, actual_name in file_map.items():
                name_stem = os.path.splitext(file_key)[0]
                if name_stem.endswith(f"-{model_u}") or name_stem.endswith(f"_{model_u}"):
                    return os.path.join(self.logo_dir, actual_name)

            # 4. EN: Third pass - Extreme fuzzy (Normalized) match
            # CN: 第三轮：极端模糊（正则化）匹配，忽略空格和横杠，但要求完全相等以防止子串误伤 (例如 TVS -> TVSII)
            for file_key, actual_name in file_map.items():
                name_stem = os.path.splitext(file_key)[0]
                # EN: Extract the model part if it contains a brand prefix separated by dash
                # CN: 如果文件名包含带横杠的品牌前缀，尝试只提取型号部分进行正则化对比
                parts = name_stem.split('-')
                potential_model_str = parts[-1] if len(parts) > 1 else name_stem
                
                # Check 1: Does the normalized full name end with the normalized model? (Safer suffix check)
                if _norm(name_stem).endswith(norm_model):
                    # Check 2: ensure it's an exact match of the model part to prevent 67 -> 67ii
                    if _norm(potential_model_str) == norm_model:
                        return os.path.join(self.logo_dir, actual_name)
                
                # Check 3: Absolute exact match of the entire normalized string (e.g. user just named file "TVS.svg")
                if _norm(name_stem) == norm_model:
                    return os.path.join(self.logo_dir, actual_name)
                    
        except Exception as e:
            pass
        return None

    def _smart_resize(self, img, target):
        w, h = img.size
        scale = target / max(w, h)
        # EN: Use BILINEAR for fast preview, LANCZOS for high-quality production
        # CN: 预览使用 BILINEAR 加速，正式输出使用 LANCZOS 保证质量
        algo = Image.Resampling.BILINEAR if target <= 1200 else Image.Resampling.LANCZOS
        return img.resize((int(w * scale), int(h * scale)), algo)

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

    def _save_with_limit(self, img, original_path, output_dir, data, current_res, layout_name, output_prefix=""):
        # EN: Default to JPG for better social media compatibility, fallback to PNG if requested
        # CN: 默认输出 JPG 以获得更好的社交平台兼容性（自动硬化阴影）
        ext = ".jpg"
        out_name = f"GT23_{output_prefix}{os.path.splitext(os.path.basename(original_path))[0]}{ext}"
        save_path = os.path.join(output_dir, out_name)
        
        try:
            if img.mode == 'RGBA':
                # EN: Flatten onto white background for JPEG
                # CN: 为 JPG 复合纯白底色，强制“硬化”阴影效果
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3]) # Use alpha channel as mask
                img_to_save = background
            else:
                img_to_save = img

            img_to_save.save(save_path, "JPEG", quality=98, subsampling=0)
        except Exception as e:
            print(f"CN: [!] JPG 保存失败，回退至 PNG: {e}")
            save_path = save_path.replace(".jpg", ".png")
            out_name = out_name.replace(".jpg", ".png")
            img.save(save_path, "PNG", optimize=True)

        f_size = os.path.getsize(save_path) / (1024 * 1024)
        # EN: 10MB limit is generous for JPG, only slight adjustment if exceeded
        # CN: 对于 JPG，10MB 限制非常充裕，若超标仅需微调质量
        if f_size > 10.0:
            print(f"CN: [!] 文件较大 ({f_size:.1f}MB)，正尝试以 Quality 92 重新保存...")
            img_to_save.save(save_path, "JPEG", quality=92, subsampling=0)
        
        # EN: Log the identified format clearly / CN: 明确记录识别出的画幅
        print(f"CN: [OK] 渲染完成: {out_name} | 画幅: {layout_name}")
        return out_name
    
    def _adjust_font_sizes_to_fit(self, draw, main_text, sub_text, available_width, base_main_size, base_sub_size):
        """
        调整字体大小使其适应可用宽度
        """
        # EN: Resolve font paths including CJK fallback / CN: 解析字体路径，包含中文字库回退
        resolved_main, resolved_sub = self._resolve_font_paths(main_text, sub_text)

        # 创建临时绘图对象来测量文本宽度
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 检查主文本宽度
        main_font = self._get_font(resolved_main, base_main_size)
        main_bbox = temp_draw.textbbox((0, 0), main_text, font=main_font)
        main_text_width = main_bbox[2] - main_bbox[0]
        
        main_scale_factor = min(1.0, available_width / main_text_width) if main_text_width > 0 else 1.0
        
        # 检查副文本宽度（使用与 TypoEngine.draw_text 相同的 textlength 累加）
        sub_font = self._get_font(resolved_sub, base_sub_size)
        sub_text_width = sum(temp_draw.textlength(c, font=sub_font) for c in list(sub_text))
        
        sub_scale_factor = min(1.0, available_width / sub_text_width) if sub_text_width > 0 else 1.0
        
        # 使用最小缩放因子确保两个文本都不会超出边界
        final_scale_factor = min(main_scale_factor, sub_scale_factor)
        
        final_main_size = max(10, int(base_main_size * final_scale_factor))  # 最小字体大小为10
        final_sub_size = max(8, int(base_sub_size * final_scale_factor))   # 最小字体大小为8
        
        return final_main_size, final_sub_size

    def _get_font(self, font_path, size):
        """
        获取字体对象，如果指定字体不存在则使用默认字体
        """
        try:
            actual_path = self._resolve_path(font_path)
            if os.path.exists(actual_path):
                if actual_path.lower().endswith(".ttc"):
                    return ImageFont.truetype(actual_path, size, index=0)
                return ImageFont.truetype(actual_path, size)
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()

    def _contains_chinese(self, text):
        """EN: Detect if text contains CJK characters. / CN: 检测文本是否包含中文字符。"""
        import re
        if not text: return False
        return bool(re.search(r'[\u4e00-\u9fff]', str(text)))

    def _resolve_font_paths(self, main_text, sub_text):
        """
        EN: Resolve final font paths including CJK fallback.
        CN: 解析最终字体路径，包括中文字体降级逻辑。
        """
        # EN: Default paths / CN: 默认路径
        resolved_main = self.font_main
        resolved_sub  = self.font_sub
        
        # EN: Detect Chinese / CN: 检查中文并降级字库
        if self._contains_chinese(main_text) or self._contains_chinese(sub_text):
            cjk_path = self._get_system_cjk_font()
            if cjk_path:
                resolved_main = cjk_path
                resolved_sub  = cjk_path
        
        # EN: Resolve to absolute paths / CN: 解析为绝对路径
        from .typo_engine import TypoEngine
        return TypoEngine._resolve_font_path(resolved_main), TypoEngine._resolve_font_path(resolved_sub)

    def _get_system_cjk_font(self):
        """EN: Find Microsoft YaHei or similar on Windows. / CN: 在 Windows 上寻找微软雅黑。"""
        if sys.platform == "win32":
            paths = [
                "C:\\Windows\\Fonts\\msyh.ttc",    # Microsoft YaHei
                "C:\\Windows\\Fonts\\msyhbd.ttc",  # YaHei Bold
                "C:\\Windows\\Fonts\\simhei.ttf"   # SimHei
            ]
            for p in paths:
                if os.path.exists(p): return p
        return None

def bootstrap_logos(resolver_func=None):
    """
    EN: Setup external logo directory if running as EXE.
    CN: 引导程序：如果作为 EXE 运行，设置外部 Logo 目录并释放默认资源。
    """
    # 0. EN: Try User-Defined Path first / CN: 极高优先级：尝试用户自定义路径
    custom_path = config_manager.get("custom_asset_path")
    if custom_path and os.path.exists(custom_path):
        # Check for logos subfolder or use direct
        logo_sub = os.path.join(custom_path, "logos")
        if os.path.exists(logo_sub): return logo_sub
        return custom_path

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    decoupled_path = os.path.join(base_dir, "GT23_Assets", "logos")
    
    # 1. EN: Try decoupled Assets Repo (Priority) / CN: 优先尝试解耦的资产仓库
    if os.path.exists(decoupled_path) and os.path.isdir(decoupled_path):
        internal_logo_path = decoupled_path
    elif resolver_func:
        # 2. EN: Use provided resolver / CN: 使用提供的路径解析函数
        internal_logo_path = resolver_func("assets/logo")
    else:
        # 3. EN: Fallback resolver for early bootstrap in main.py
        # CN: main.py 早期引导使用的路径解析方案
        if hasattr(sys, '_MEIPASS'):
            internal_logo_path = os.path.join(sys._MEIPASS, "assets/logo")
        else:
            internal_logo_path = os.path.join(base_dir, "assets", "logo")
    
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # EN: Prioritize GT23_Assets folder next to EXE / CN: 优先使用 EXE 旁的 GT23_Assets 目录
        external_logo_path = os.path.join(exe_dir, "GT23_Assets", "logos")
        # EN: Fallback to simple 'logos' for backward compatibility / CN: 备选：直接在 EXE 旁的 'logos' 目录
        if not os.path.exists(external_logo_path):
            legacy_path = os.path.join(exe_dir, "logos")
            if os.path.exists(legacy_path):
                return legacy_path
        return external_logo_path
    else:
        return internal_logo_path
