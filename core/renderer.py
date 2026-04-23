import os
import io
import sys
import shutil
import time
from fractions import Fraction
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
try:
    import piexif
except ImportError:
    piexif = None
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
                    theme="light", is_pure=False, use_lens_branding=True, rainbow_index=0, rainbow_total=1, is_sample=False, 
                    source_img=None, output_prefix="", comp_v_offset=0, comp_h_offset=0, **kwargs):
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
            
            # EN: Support asymmetrical side padding
            # CN: 支持非对称侧边距调节 (左/右独立)
            left_ratio = layout.get('left', layout.get('side', 0.04))
            right_ratio = layout.get('right', layout.get('side', 0.04))
            top_ratio = layout.get('top', 0.04)
            bottom_ratio = layout.get('bottom', 0.13)
            font_base_scale = layout.get('font_scale', 0.032)
            
            # --- EN: CALCULATE SPACING ---
            # EN: Use long_edge as a stable reference for all paddings to ensure consistent border thickness
            # CN: 使用长边作为所有边距计算的稳定基准，确保 UI 输入的像素值具有一致的物理含义
            long_edge = max(w, h)
            side_pad_left = int(long_edge * left_ratio)
            side_pad_right = int(long_edge * right_ratio)
            top_pad = int(long_edge * top_ratio)
            bottom_splice = int(long_edge * bottom_ratio)
            
            # EN: The "inner bottom margin" between image and text area. 
            # CN: 图像与底部文字区之间的间隙，置 0 以实现底部参数的完全解耦
            inner_bottom_margin = 0
            
            new_w = w + side_pad_left + side_pad_right
            new_h = h + top_pad + inner_bottom_margin + bottom_splice
            
            # --- EN: TARGET ASPECT RATIO ADAPTATION / CN: 目标画幅比例自适应 ---
            target_ratio_str = data.get('target_ratio', 'Original')
            if target_ratio_str and 'Original' not in target_ratio_str and '原图' not in target_ratio_str:
                # EN: Parse ratio (e.g., "4:5 (LRB)" -> 0.8) / CN: 解析比例字符串
                import re
                match = re.search(r'(\d+):(\d+)', target_ratio_str)
                if match:
                    tr_w, tr_h = int(match.group(1)), int(match.group(2))
                    tr = tr_w / tr_h
                    
                    current_ratio = new_w / new_h
                    
                    # EN: Use epsilon (0.1%) to avoid redundant padding from precision errors
                    # CN: 增加 0.1% 的容错率，避免因浮点误差导致的二次留白修正
                    if abs(current_ratio - tr) / tr > 0.001:
                        if current_ratio < tr:
                            # EN: Canvas too tall, add side padding
                            target_new_w = int(new_h * tr)
                            diff_w = target_new_w - new_w
                            if diff_w > 0:
                                # EN: Horizontal distribution (0.5 center by default)
                                h_off = comp_h_offset / 100.0
                                dist_h = 0.5 + (h_off / 2.0) # -1 -> 0, 0 -> 0.5, 1 -> 1.0
                                l_extra = int(diff_w * dist_h)
                                side_pad_left += l_extra
                                side_pad_right += (diff_w - l_extra)
                                new_w = target_new_w
                        elif current_ratio > tr:
                            # EN: Canvas too wide, add vertical padding
                            target_new_h = int(new_w / tr)
                            diff_h = target_new_h - new_h
                            if diff_h > 0:
                                # EN: Use Text Safety Buffer during redistribution
                                # CN: 在再分配过程中保留文字安全区
                                TEXT_RESERVE = 550
                                v = comp_v_offset / 100.0
                                shift_budget = max(0, diff_h - TEXT_RESERVE)
                                
                                dist_v = (0.3 * (1 + v)) if v < 0 else (0.3 + 0.7 * v)
                                top_extra = int(shift_budget * dist_v)
                                
                                top_pad += top_extra
                                bottom_splice += (diff_h - top_extra)
                                new_h = target_new_h
            
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
            elif theme == "frosted":
                # EN: Glassmorphism (Blurred Original) / CN: 磨砂玻璃（基于原图的高斯模糊背景）
                canvas = self._create_frosted_canvas(img, new_w, new_h)
            elif theme == "slate_teal":
                # EN: Premium Slate-Teal Gradient (Ultimate Luminous Replica)
                # CN: 石板青（终极通透版：复刻福伦达“空明石板青”模拟渐变）
                c_top = (210, 222, 228)    # Luminous Air / 空明青灰
                c_bottom = (125, 142, 152) # Breathable Slate / 通透石板
                # EN: Use gamma 1.6 for expansive highlight falloff / CN: 使用伽态 1.6 引导大范围高光衰减
                canvas = self._create_linear_gradient_canvas(new_w, new_h, c_top, c_bottom, vertical=True, gamma=1.6)
                # EN: Apply matte texture for "Fine Art Paper" feel
                # CN: 应用磨砂纹理，模拟“艺术纸”质感
                canvas = self._apply_matte_texture(canvas, intensity=0.06)
            else:
                canvas = Image.new("RGB", (new_w, new_h), bg_color)
            
            if theme in ["frosted", "slate_teal"]:
                # EN: Floating Photo Effect (Inner Shadow + Image + Border)
                self._draw_floating_photo(canvas, img, side_pad_left, top_pad, line_color)
            else:
                canvas.paste(img, (side_pad_left, top_pad))
                # EN: 1px inner border
                ImageDraw.Draw(canvas).rectangle([side_pad_left, top_pad, side_pad_left + w, top_pad + h], outline=line_color, width=1)
            
            draw = ImageDraw.Draw(canvas)
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
                
                # EN: Resolve independent main/sub font scales (CN: 解决独立的主副标题比例)
                font_main_scale = layout.get('font_main_scale', font_base_scale) if layout else font_base_scale
                font_sub_scale = layout.get('font_sub_scale', font_main_scale * 0.78) if layout else font_base_scale * 0.78
                
                base_main_font_size = int(long_edge * font_main_scale)
                base_sub_font_size = int(long_edge * font_sub_scale)

                # EN: Available width for text (Allow 95% of canvas width, no longer squeezed by side borders)
                # CN: 文字可用宽度（允许占用画布总宽度的 95%，不再受侧边框宽度的双倍挤压）
                available_width = int(new_w * 0.95)
                
                # EN: Adaptive Text Coloring for Frosted Mode
                # CN: 磨砂模式下的文字颜色自适应逻辑 (强化对比度版)
                if theme == "frosted":
                    from PIL import ImageStat
                    # EN: Sample the footer area where text is drawn
                    # CN: 采样底部文字绘制区域的亮度
                    footer_rect = [0, new_h - bottom_splice, new_w, new_h]
                    footer_rect = [max(0, int(v)) for v in footer_rect]
                    footer_sample = canvas.crop(footer_rect).convert("L")
                    avg_lum = ImageStat.Stat(footer_sample).mean[0]
                    
                    # EN: Dynamic 5-level Grayscale Palette logic
                    # CN: 动态五阶灰阶调色板逻辑
                    if avg_lum > 180: # Very Light
                        main_color, sub_color = (0, 0, 0), (45, 45, 45)
                    elif avg_lum > 135: # Fairly Light
                        main_color, sub_color = (15, 15, 15), (70, 70, 70)
                    elif avg_lum > 90: # Neutral/Mid
                        main_color, sub_color = (255, 255, 255), (190, 190, 190)
                    else: # Dark
                        main_color, sub_color = (255, 255, 255), (210, 210, 210)
                
                actual_main_size, actual_sub_size, m_factor, s_factor = self._adjust_font_sizes_to_fit(
                    draw, main_text, sub_text, available_width, 
                    base_main_font_size, base_sub_font_size
                )

                # EN: High-precision calculation of overflow-free max in reference pixels (4500px)
                # CN: 在 4500px 基准下进行高精度不溢出最大像素值计算 (避开预览图整数舍入误差)
                timings['max_font_px'] = {
                    'main': int(font_main_scale * m_factor * 4500),
                    'sub': int(font_sub_scale * s_factor * 4500),
                    'main_overflow': m_factor < 0.9999,
                    'sub_overflow': s_factor < 0.9999
                }

                # EN: Vertical collision detection (CN: 垂直重叠/压图检测)
                ref_factor = long_edge / 4500.0
                resolved_main, resolved_sub = self._resolve_font_paths(main_text, sub_text)
                m_font = self._get_font(resolved_main, actual_main_size)
                m_ascent, m_descent = m_font.getmetrics()
                # EN: Anchor text proportionally to image bottom (38% of space) for tighter visual gestalt
                # CN: 文字锚点调整至底部留白的 38% 处（微调），让文字与照片的“呼吸感”更紧密，避免在大画幅下显得疏离
                total_bottom_space = inner_bottom_margin + bottom_splice
                base_y = top_pad + h + int(total_bottom_space * 0.38)
                v_gap_ref = max(actual_main_size, actual_sub_size)
                main_y = base_y - int(v_gap_ref * 0.55)
                photo_bottom = top_pad + h
                
                # Check height overflow (Overlap with photo area)
                v_overflow = (main_y - m_ascent) < photo_bottom
                timings['max_font_px']['v_overflow'] = v_overflow
                
                if v_overflow:
                    # EN: Approximate max font size that fits vertically (CN: 估算垂直方向能容纳的最大字号)
                    # Calculation: m_ascent(0.8) + offset(0.55) = 1.35 * font_size < center_gap
                    center_gap = (inner_bottom_margin + bottom_splice) // 2
                    max_v_size = int(center_gap / 1.35 / ref_factor)
                    # EN: Update suggest if hit vertical limit (CN: 如果垂直溢出，取宽度与高度限制的最小值)
                    timings['max_font_px']['main'] = min(timings['max_font_px']['main'], max_v_size)

                t_logo_start = time.perf_counter()
                v_offset_ratio = layout.get('font_v_offset', 0) if layout else 0
                v_offset_px = int(long_edge * v_offset_ratio)
                
                self._draw_pro_text(draw, new_w, h, side_pad_left, side_pad_right, top_pad, bottom_splice, 
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

                # EN: Flatten before saving / CN: 保存前进行底色复合处理
                flatten_bg_color = (0, 0, 0) if theme in ["dark", "slate_teal"] else (255, 255, 255)
                bg = Image.new("RGB", final_output.size, flatten_bg_color)
                if final_output.mode == 'RGBA':
                    bg.paste(final_output, mask=final_output.split()[3])
                else:
                    bg.paste(final_output)
                bg.save(save_path, quality=95, subsampling=0)
                timings['save'] = time.perf_counter() - t_save_start
                final_output = bg

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

    def _prepare_lens_segments(self, data, sub_color, use_lens_branding=True):
        """EN: Parse lens string into styled segments / CN: 将镜头字符串解析为带样式的片段"""
        lens = str(data.get('LensModel') or "").strip()
        make = str(data.get('Make') or "").strip().upper()
        
        # EN: Basic info parts / CN: 基础信息部分
        info_parts = []
        is_digi = data.get('is_digital', False)
        
        focal = data.get('FocalLength')
        if is_digi and focal: info_parts.append(focal)
        aperture = data.get('FNumber')
        if aperture: info_parts.append(f"f/{aperture}")
        shutter = data.get('ExposureTimeStr')
        if shutter: info_parts.append(f"{shutter}s")
        iso = data.get('ISO')
        if is_digi and iso: info_parts.append(f"ISO {iso}")
        
        # EN: Digital systems should not display film info
        # CN: 数码系统不展示胶片信息
        if not is_digi:
            film_name = str(data.get('Film') or "").upper()
            if film_name: info_parts.append(film_name)
        
        base_info = "  |  ".join(info_parts)
        
        segments = []
        
        # EN: Early return if branding is disabled / CN: 如果禁用标识则提前返回
        if not use_lens_branding:
            segments.append({"type": "text", "content": lens + "  |  " + base_info, "color": sub_color})
            return segments

        # --- EN: Brand Specific Logic / CN: 品牌特定逻辑 ---
        
        # 1. CANON L (Red L)
        if "CANON" in make:
            import re
            # EN: Match standalone "L" (Luxury series) - Not surrounded by letters
            # CN: 匹配独立的 "L" 红圈标识 - 前后不能是字母（允许数字/符号）
            match = re.search(r'(?<![a-zA-Z])L(?![a-zA-Z])', lens)
            if match:
                start, end = match.span()
                segments.append({"type": "text", "content": lens[:start], "color": sub_color})
                segments.append({"type": "text", "content": lens[start:end], "color": (196, 30, 58)}) # Pantone 186 C
                segments.append({"type": "text", "content": lens[end:] + "  |  " + base_info, "color": sub_color})
                return segments

        # 2. NIKON GOLD (Gold N)
        if "NIKON" in make:
            import re
            # EN: Match standalone "N" (Nano Coating) - Not surrounded by letters
            match = re.search(r'(?<![a-zA-Z])N(?![a-zA-Z])', lens, re.IGNORECASE)
            if match:
                start, end = match.span()
                segments.append({"type": "text", "content": lens[:start], "color": sub_color})
                # EN: Refined Gold for better visibility / CN: 优化金色的可见度
                segments.append({"type": "text", "content": lens[start:end], "color": (172, 147, 78)}) # Brighter Pantone 871 C
                segments.append({"type": "text", "content": lens[end:] + "  |  " + base_info, "color": sub_color})
                return segments

        # 3. SONY GM (Token)
        if "SONY" in make:
            import re
            # EN: Use word boundaries for GM to avoid partial matches within "SIGMA"
            if re.search(r'\bGM\b', lens.upper()):
                token_path = self._resolve_path(os.path.join("assets", "lenses", "SONY-GM.png"))
                if os.path.exists(token_path):
                    clean_lens = re.sub(r'\bGM\b', '', lens, flags=re.IGNORECASE).strip()
                    segments.append({"type": "text", "content": clean_lens + " ", "color": sub_color})
                    segments.append({"type": "image", "path": token_path})
                    segments.append({"type": "text", "content": "  |  " + base_info, "color": sub_color})
                    return segments

        # 4. SIGMA (Art/S/C Token)
        # EN: More lenient check to capture Sigma series even if brand string is missing
        # CN: 更宽泛的检测逻辑，捕获即便没有 "SIGMA" 字样的适马系列
        keywords_art = ["ART", "| A", "(A)"]
        keywords_sport = ["SPORT", "| S", "(S)"]
        keywords_contemp = ["CONTEMP", "| C", "(C)"]
        
        upper_lens = lens.upper()
        token_file = None
        if any(k in upper_lens for k in keywords_art):
            token_file = "SIGMA-ART.png"
        elif any(k in upper_lens for k in keywords_sport):
            token_file = "SIGMA-SPORTS.png"
        elif any(k in upper_lens for k in keywords_contemp):
            token_file = "SIGMA-CONTEMPORARY.png"
        
        if token_file:
            token_path = self._resolve_path(os.path.join("assets", "lenses", token_file))
            if os.path.exists(token_path):
                    import re
                    # EN: Dynamic cleaning for Sigma series markers / CN: 动态清洗适马系列标识
                    all_k = ["ART", "SPORTS", "SPORT", "CONTEMPORARY", "CONTEMP"]
                    pattern = r'\b(?:' + r'|'.join([re.escape(k) for k in all_k]) + r')\b|\|\s*[ASC]\b|\([ASC]\)'
                    clean_lens = re.sub(pattern, '', lens, flags=re.IGNORECASE)
                    clean_lens = re.sub(r'\|\s*$', '', clean_lens.strip()).strip()
                    clean_lens = re.sub(r'\s{2,}', ' ', clean_lens)
                    
                    segments.append({"type": "text", "content": clean_lens + " ", "color": sub_color})
                    segments.append({"type": "image", "path": token_path})
                    segments.append({"type": "text", "content": "  |  " + base_info, "color": sub_color})
                    return segments

        # EN: Default Fallback
        full_text = lens + "  |  " + base_info
        if "T*" in full_text:
            segments.append({"type": "text", "content": full_text, "color": self._get_zeiss_colors(full_text, sub_color)})
        else:
            segments.append({"type": "text", "content": full_text, "color": sub_color})
            
        return segments

    def _get_zeiss_colors(self, text, base_color):
        colors = [base_color] * len(text)
        zeiss_red = (237, 31, 37)
        i = 0
        while i < len(text) - 1:
            if text[i:i+2] == "T*":
                colors[i] = zeiss_red
                colors[i+1] = zeiss_red
                i += 2
            else:
                i += 1
        return colors

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
        
        sub_segments = self._prepare_lens_segments(data, (0,0,0))
        sub_text = "".join([s["content"] for s in sub_segments if s["type"] == "text"])
        return main_text, sub_text

    def _draw_pro_text(self, draw, new_w, h, side_pad_left, side_pad_right, top_pad, bottom_splice, main_text, sub_text, m_size, s_size, data=None, main_color=None, sub_color=None, use_lens_branding=True, timings=None, v_offset=0):
        if timings is None: timings = {}
        # EN: Use provided colors or fallback to defaults
        # CN: 使用提供的颜色，或回退至默认值
        m_color = main_color or self.main_color
        s_color = sub_color or self.sub_color
        
        # EN: Detect CJK characters and resolve paths / CN: 检测 CJK 字符并解析路径
        resolved_main, resolved_sub = self._resolve_font_paths(main_text, sub_text)

        # EN: Vertical center of the white area with optional offset / CN: 白色区域垂直中心，支持可选偏移
        inner_bottom_margin = 0
        base_y = top_pad + h + (inner_bottom_margin + bottom_splice) // 2 + v_offset
        
        # EN: Dynamic vertical offset based on font sizes to ensure relative spacing
        # CN: 基于字号的动态垂直偏移，确保间距随字体放大而自动“弹开”
        v_gap_ref = max(m_size, s_size)
        main_draw_pos = (new_w // 2, base_y - int(v_gap_ref * 0.55))
        sub_draw_pos = (new_w // 2, base_y + int(v_gap_ref * 0.75))

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
            # EN: Draw Main Text (Camera) / CN: 绘制主标题（相机）
            if not logo_drawn:
                # EN: Construct segments for main text / CN: 为主标题构建片段
                main_segments = [{"type": "text", "content": main_text, "color": m_color}]
                TypoEngine.draw_mixed_text(draw, main_draw_pos, main_segments, resolved_main, m_size, m_color, timings=timings, key_prefix='text_main')
            
            # EN: Draw Sub Text (Lens + Info) using structured segments / CN: 使用结构化片段绘制副标题（镜头+参数）
            sub_segments = self._prepare_lens_segments(data, s_color, use_lens_branding=use_lens_branding)
            TypoEngine.draw_mixed_text(draw, sub_draw_pos, sub_segments, resolved_sub, s_size, s_color, timings=timings, key_prefix='text_sub')
        except Exception as e:
            import traceback
            traceback.print_exc()
            if not logo_drawn:
                draw.text(main_draw_pos, main_text, fill=m_color, anchor="mm")
            # Fallback for sub_text: try to extract plain text from segments
            try:
                sub_segments = self._prepare_lens_segments(data, s_color, use_lens_branding=use_lens_branding)
                plain_sub = "".join([s["content"] for s in sub_segments if s["type"] == "text"])
                draw.text(sub_draw_pos, plain_sub, fill=s_color, anchor="mm")
            except:
                draw.text(sub_draw_pos, str(data.get('LensModel')), fill=s_color, anchor="mm")
        timings['text_render_pure'] = time.perf_counter() - t_text_sub_start


    def _find_logo_path(self, make, model):
        """EN: Universal case-insensitive logo lookup.
           CN: 通用的不区分大小写 Logo 检索逻辑。支持多路径（源码 + dist）搜索。"""
        # EN: Multi-path search (Source + Dist fallback)
        search_dirs = [self.logo_dir]
        dist_logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", "GT23_Assets", "logos")
        if os.path.exists(dist_logo_path) and dist_logo_path not in search_dirs:
            search_dirs.append(dist_logo_path)
        
        # 1. EN: Normalize input / CN: 正则化输入
        make_u = str(make or "").upper().strip()
        model_u = str(model or "").upper().strip()
        if not model_u: return None

        def _norm(s): return "".join(c for c in s if c.isalnum())
        norm_model = _norm(model_u)

        search_stems = []
        if make_u:
            search_stems.append(f"{make_u}-{model_u}")
            search_stems.append(f"{make_u}_{model_u}")
            search_stems.append(f"{make_u}{model_u}")
        search_stems.append(model_u)

        for l_dir in search_dirs:
            if not os.path.exists(l_dir): continue
            try:
                files = os.listdir(l_dir)
                supported_exts = [".svg", ".png", ".jpg", ".jpeg"]
                file_map = {f.upper(): f for f in files if any(f.lower().endswith(ext) for ext in supported_exts)}
                
                # EN: First pass - strict matching with candidate stems
                for stem in search_stems:
                    for ext in [".svg", ".png", ".jpg"]:
                        target_key = f"{stem}{ext.upper()}"
                        if target_key in file_map:
                            return os.path.join(l_dir, file_map[target_key])
                
                # EN: Second pass - Suffix matching
                for file_key, actual_name in file_map.items():
                    name_stem = os.path.splitext(file_key)[0]
                    if name_stem.endswith(f"-{model_u}") or name_stem.endswith(f"_{model_u}"):
                        return os.path.join(l_dir, actual_name)
                    if _norm(name_stem) == norm_model:
                        return os.path.join(l_dir, actual_name)
            except:
                continue
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

    def _save_with_limit(self, img, original_path, output_dir, data, current_res, layout_name, output_prefix="", theme="light"):
        # EN: Default to JPG for better social media compatibility, fallback to PNG if requested
        # CN: 默认输出 JPG 以获得更好的社交平台兼容性（自动硬化阴影）
        ext = ".jpg"
        out_name = f"GT23_{output_prefix}{os.path.splitext(os.path.basename(original_path))[0]}{ext}"
        save_path = os.path.join(output_dir, out_name)
        
        try:
            if img.mode == 'RGBA':
                # EN: Flatten onto matching background color for JPEG
                # CN: 为 JPG 复合底色，强制“硬化”阴影效果（深色模式用黑底，其余用白底）
                flatten_bg_color = (0, 0, 0) if theme == "dark" else (255, 255, 255)
                background = Image.new("RGB", img.size, flatten_bg_color)
                background.paste(img, mask=img.split()[3]) # Use alpha channel as mask
                img_to_save = background
            else:
                img_to_save = img

            # EN: Build updated EXIF bytes / CN: 构建更新后的 EXIF 字节流
            exif_bytes = self._build_exif_bytes(original_path, data)

            img_to_save.save(save_path, "JPEG", quality=98, subsampling=0, exif=exif_bytes)
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
            img_to_save.save(save_path, "JPEG", quality=92, subsampling=0, exif=exif_bytes)
        
        # EN: Log the identified format clearly / CN: 明确记录识别出的画幅
        print(f"CN: [OK] 渲染完成: {out_name} | 画幅: {layout_name}")
        return out_name

    def _build_exif_bytes(self, original_path, data):
        """
        EN: Extract original EXIF and patch it with manual UI overrides.
        CN: 提取原始 EXIF 并根据 UI 手动覆盖参数进行 Patch。
        """
        raw_fallback = b""
        try:
            with Image.open(original_path) as test_img:
                raw_fallback = test_img.info.get("exif", b"")
        except: pass

        if not piexif:
            return raw_fallback
        
        try:
            # 1. EN: Load original EXIF / CN: 加载原始 EXIF
            exif_dict = piexif.load(original_path)
            
            # 2. EN: Patch 0th IFD (Make, Model) / CN: 更新 0th IFD (品牌、型号)
            # ... (lines 740-784) ...
            # (Note: I'll use a larger block to ensure correct context)
            if data.get('Make'):
                exif_dict["0th"][piexif.ImageIFD.Make] = data['Make'].encode('utf-8')
            if data.get('Model'):
                exif_dict["0th"][piexif.ImageIFD.Model] = data['Model'].encode('utf-8')
                
            if "Exif" not in exif_dict: exif_dict["Exif"] = {}
            if data.get('LensModel'):
                exif_dict["Exif"][piexif.ExifIFD.LensModel] = data['LensModel'].encode('utf-8')
            if data.get('ISO'):
                try: exif_dict["Exif"][piexif.ExifIFD.ISOSpeedRatings] = int(float(data['ISO']))
                except: pass
            
            shutter = data.get('ExposureTimeStr')
            if shutter:
                try:
                    if "/" in shutter:
                        num, den = map(int, shutter.split("/"))
                        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (num, den)
                    else:
                        val = float(shutter)
                        f = Fraction(val).limit_denominator(1000000)
                        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (f.numerator, f.denominator)
                except: pass
            
            aperture = data.get('FNumber')
            if aperture:
                try:
                    val = float(aperture)
                    exif_dict["Exif"][piexif.ExifIFD.FNumber] = (int(val * 100), 100)
                except: pass

            if "thumbnail" in exif_dict: del exif_dict["thumbnail"]

            return piexif.dump(exif_dict)
        except Exception as e:
            print(f"CN: [!] EXIF 处理失败 (降级回退): {e}")
            return raw_fallback
    
    def _adjust_font_sizes_to_fit(self, draw, main_text, sub_text, available_width, base_main_size, base_sub_size):
        """
        调整字体大小使其适应可用宽度
        """
        if available_width <= 0: return 10, 8
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
        
        # EN: Decouple scaling to allow main title to grow even if subtitle is long
        # CN: 解耦主副标题缩放，允许型号名在参数行较长时依然保持独立增长（响应老大反馈）
        final_main_size = max(10, int(base_main_size * main_scale_factor))
        final_sub_size = max(8, int(base_sub_size * sub_scale_factor))
        
        return final_main_size, final_sub_size, main_scale_factor, sub_scale_factor

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
