import time
import io
from PIL import Image, ImageDraw
from ..branding.logo_finder import LogoFinder
from .text_adjuster import TextAdjuster
from .engine import TypoEngine
from ..branding.lens_parser import LensParser

try:
    import cairosvg
except ImportError:
    cairosvg = None

class TextRenderer:
    """
    EN: High-level text and logo rendering engine.
    CN: 高层文字与 Logo 渲染引擎。
    """
    
    @staticmethod
    def draw_pro_text(draw, canvas_size, img_size, pad_info, text_info, data, colors, font_resolver, logo_dir, resolved_fonts=None, timings=None):
        if timings is None: timings = {}
        
        new_w, new_h = canvas_size
        w, h = img_size
        side_pad_left, side_pad_right, top_pad, bottom_splice = pad_info
        main_text, sub_text, m_size, s_size, v_offset_px = text_info
        m_color, s_color = colors
        
        is_sprocket = data.get('sprocket_enabled', False)
        
        # EN: Use pre-resolved fonts if provided, otherwise resolve
        # CN: 如果提供了预解析字体则直接使用，否则进行解析
        if resolved_fonts:
            resolved_main, resolved_sub = resolved_fonts
        else:
            manual_main = data.get('font_main_path', 'Default') if data else 'Default'
            manual_sub = data.get('font_sub_path', 'Default') if data else 'Default'
            resolved_main, resolved_sub = font_resolver.resolve(
                main_text, sub_text,
                custom_main=manual_main if manual_main != 'Default' else None,
                custom_sub=manual_sub if manual_sub != 'Default' else None
            )

        # --- EN: POSITIONING ---
        img_long_edge = max(w, h)
        spacing_px = int(data['layout'].get('font_spacing_scale', 0) * img_long_edge)

        if is_sprocket:
            px_per_mm = min(new_w - side_pad_left - side_pad_right, h) / 24.0
            main_draw_pos = (new_w // 2, int(1.0 * px_per_mm) + v_offset_px)
            sub_draw_pos = (new_w // 2, (top_pad + h + bottom_splice) - int(1.0 * px_per_mm) + v_offset_px)
            
            target_px = int(1.6 * px_per_mm)
            m_size = min(m_size, target_px)
            s_size = min(s_size, target_px)
        else:
            v_gap_ref = max(m_size, s_size)
            actual_gap = spacing_px if spacing_px > 0 else int(v_gap_ref * 1.3)
            base_y = top_pad + h + bottom_splice // 2 + v_offset_px
            main_draw_pos = (new_w // 2, base_y - int(actual_gap * 0.42))
            sub_draw_pos = (new_w // 2, base_y + int(actual_gap * 0.58))

        # --- EN: LOGO RENDERING ---
        logo_drawn = False
        if data.get('show_model', 1):
            make = str(data.get('Make') or "").strip()
            model = str(data.get('Model') or "").strip()
            logo_path = LogoFinder.find_logo_path(make, model, logo_dir)
            
            if logo_path:
                t_logo_start = time.perf_counter()
                try:
                    main_font = TextAdjuster._get_font(resolved_main, m_size)
                    ascent, descent = main_font.getmetrics()
                    target_h = ascent + descent
                    
                    if logo_path.lower().endswith(".svg") and cairosvg:
                        png_data = cairosvg.svg2png(url=logo_path, output_height=target_h * 2)
                        logo_img = Image.open(io.BytesIO(png_data))
                    else:
                        logo_img = Image.open(logo_path).convert("RGBA")
                    
                    bbox = logo_img.getbbox()
                    if bbox: logo_img = logo_img.crop(bbox)
                    
                    orig_w, orig_h = logo_img.size
                    if orig_h > 0:
                        scaled_w = int(orig_w * (target_h / orig_h))
                        logo_img = logo_img.resize((scaled_w, target_h), Image.Resampling.LANCZOS)

                    # EN: Intelligent Tinting
                    is_black_theme = (m_color[0] < 40 and m_color[1] < 40 and m_color[2] < 40)
                    if not is_black_theme:
                        pixels = list(logo_img.getdata())
                        new_pixels = []
                        for r, g, b, a in pixels:
                            if r < 180 and g < 180 and b < 180 and abs(r-g) < 40 and abs(g-b) < 40:
                                new_pixels.append((*m_color, a))
                            else:
                                new_pixels.append((r, g, b, a))
                        logo_img.putdata(new_pixels)

                    logo_x = (new_w - logo_img.width) // 2
                    logo_y = main_draw_pos[1] - logo_img.height // 2
                    draw._image.paste(logo_img, (logo_x, logo_y), logo_img)
                    logo_drawn = True
                    timings['logo_render'] = time.perf_counter() - t_logo_start
                except Exception as e:
                    print(f"CN: [!] Logo 渲染失败: {e}")

        # --- EN: TEXT DRAWING ---
        try:
            def draw_text_internal(text, pos, font_path, size, color, key):
                if "1050" in str(font_path).upper():
                    # EN: Apply Zeiss T* Red logic if applicable
                    # CN: 应用蔡司 T* 红逻辑
                    target_colors = LensParser._get_zeiss_colors(text, color) if "T*" in text else color
                    png_img = TypoEngine.draw_png_text(text, "assets/fonts/1050", spacing_ratio=0.15, color=target_colors)
                    if png_img.height > 0:
                        # EN: Scaling: png_img is now tightly cropped, so size/height is accurate
                        final_w = int(png_img.width * (size / png_img.height))
                        png_img = png_img.resize((final_w, int(size)), Image.Resampling.LANCZOS)
                    
                    max_w = int(new_w - side_pad_left - side_pad_right - 40)
                    if png_img.width > max_w:
                        png_img = png_img.resize((max_w, int(png_img.height * (max_w / png_img.width))), Image.Resampling.LANCZOS)
                        
                    draw._image.paste(png_img, (int(pos[0] - png_img.width // 2), int(pos[1] - png_img.height // 2)), png_img)
                else:
                    TypoEngine.draw_mixed_text(draw, pos, [{"type": "text", "content": text, "color": color}], font_path, size, color, timings=timings, key_prefix=key)

            if not logo_drawn:
                draw_text_internal(main_text, main_draw_pos, resolved_main, m_size, m_color, 'text_main')
            
            if "1050" in str(resolved_sub).upper():
                draw_text_internal(sub_text, sub_draw_pos, resolved_sub, s_size, s_color, 'text_sub')
            else:
                sub_segments = LensParser.prepare_segments(data, s_color)
                TypoEngine.draw_mixed_text(draw, sub_draw_pos, sub_segments, resolved_sub, s_size, s_color, timings=timings, key_prefix='text_sub')

        except Exception as e:
            import traceback
            traceback.print_exc()
            if not logo_drawn: draw.text(main_draw_pos, main_text, fill=m_color, anchor="mm")
            draw.text(sub_draw_pos, sub_text, fill=s_color, anchor="mm")
