# core/renderers/renderer_matin.py
# EN: Renderer for Matin-Style slide archival sheets (V6 Physics Engine)
# CN: Matin 风格幻灯片活页渲染器 (V6 物理引擎)

import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageChops
from handright import Template, handwrite
from .base_renderer import BaseFilmRenderer

class RendererMatin(BaseFilmRenderer):
    """
    EN: Renders images as mounted slides in a grid with V6 physical simulation.
    CN: 使用 V6 物理仿真引擎将图片渲染为带卡槽的幻灯片网格布局。
    """
    
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None, 
               orientation=None, show_date=True, show_exif=True, progress_callback=None, preview_mode=False, 
               manual_format=None, overrides=None, global_l1=None, global_l2=None, font_path=None):
        
        draw = ImageDraw.Draw(canvas)
        
        # EN: Localized message / CN: 本地化消息
        lang = "zh" if "胶片" in str(progress_callback) or "正在" in str(progress_callback) else "en"
        
        # EN: Background - Scientific Lightboard Simulation
        # CN: 背景 - 科学灯箱仿真
        w, h = canvas.size
        
        if preview_mode:
            # EN: Simple flat background for preview
            draw.rectangle([0, 0, w, h], fill=(240, 240, 240))
        else:
            # EN: Lightbox surface: #F5F5F5 (Center) to #EBEBEB (Edges)
            base_grad = Image.new('RGB', (1, 2))
            base_grad.putpixel((0, 0), (245, 245, 245)) 
            base_grad.putpixel((0, 1), (235, 235, 235)) 
            grad_img = base_grad.resize((w, h), Image.Resampling.BILINEAR)
            canvas.paste(grad_img, (0, 0))
            
            # EN: Background Texture - 1.5% Monochromatic Gaussian Noise
            noise_size = 512
            noise_img = Image.new('L', (noise_size, noise_size), 0)
            n_draw = ImageDraw.Draw(noise_img)
            for _ in range(int(noise_size * noise_size * 0.15)):
                nx, ny = random.randint(0, noise_size-1), random.randint(0, noise_size-1)
                n_draw.point((nx, ny), fill=random.randint(1, 3))
            
            noise_overlay = Image.new('RGBA', (w, h), (0,0,0,0))
            for ty in range(0, h, noise_size):
                for tx in range(0, w, noise_size):
                    temp_tile = Image.new('RGBA', (noise_size, noise_size), (0, 0, 0, 30)) 
                    noise_overlay.paste(temp_tile, (tx, ty), noise_img)
            canvas.paste(noise_overlay, (0, 0), noise_overlay)
        
        cols = cfg.get('cols', 4)
        rows = cfg.get('rows', 5)
        cell_w = cfg.get('cell_w', 1181) 
        cell_h = cfg.get('cell_h', 1181)
        col_gap = cfg.get('col_gap', 40)
        row_gap = cfg.get('row_gap', 40)
        m_x = cfg.get('margin_x', 150)
        m_y_t = cfg.get('margin_y_top', 500)
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(img_list):
                    break
                
                if progress_callback:
                    msg = f"[{idx+1}/{len(img_list)}] {os.path.basename(img_list[idx])}"
                    progress_callback(msg)
 
                # Calculate top-left of the mount
                x = m_x + c * (cell_w + col_gap)
                y = m_y_t + r * (cell_h + row_gap)
                
                # Resolve Custom Text per Image
                fname = os.path.basename(img_list[idx])
                ov = overrides.get(fname, {}) if overrides else {}
                c_l1 = ov.get('l1') if ov.get('l1') is not None else global_l1
                c_l2 = ov.get('l2') if ov.get('l2') is not None else global_l2
                
                self._draw_mounted_slide(canvas, img_list[idx], x, y, cell_w, cell_h, 
                                         meta_handler, show_date, show_exif, cfg, preview_mode, 
                                         forced_format=manual_format,
                                         custom_l1=c_l1, custom_l2=c_l2,
                                         font_path=font_path)
        
        return canvas

    def _get_handwritten_img(self, txt, font_size=28, color=(20, 30, 80), font_path=None, bold=True):
        """
        EN: Generate realistic handwritten text with jitter using handright library.
        CN: 使用 handright 库生成带抖动的逼真手写文字。
        """
        if not txt:
            return None
            
        try:
            # 1. Resolve Font
            # (same font logic)
            font = None
            if font_path and os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except: pass
            
            if not font:
                try:
                    f_path = r"C:\Windows\Fonts\segoepr.ttf"
                    if not os.path.exists(f_path):
                        f_path = "arial.ttf"
                    font = ImageFont.truetype(f_path, font_size)
                except:
                    font = ImageFont.load_default()

            # 2. Handright Template
            template = Template(
                background=Image.new("RGBA", (2000, 200), (255, 255, 255, 0)),
                font=font,
                line_spacing=font_size + 10,
                fill=color,
                left_margin=10,
                top_margin=10,
                right_margin=10,
                bottom_margin=10,
                word_spacing=int(font_size * 0.15),
                line_spacing_sigma=1,
                font_size_sigma=1,
                word_spacing_sigma=1,
                perturb_x_sigma=0.5,
                perturb_y_sigma=0.5,
                perturb_theta_sigma=0.03,
            )
            
            images = list(handwrite(txt, template))
            if not images:
                return None
                
            txt_img = images[0]
            
            # 3. Bold (Thickening) - Simulates oil marker
            if bold:
                alpha = txt_img.getchannel('A')
                # MaxFilter expands pixels. size=3 is 1px expansion in each direction
                alpha = alpha.filter(ImageFilter.MaxFilter(size=3))
                txt_img.putalpha(alpha)
            
            # 4. Crop to content transparency
            bbox = txt_img.getbbox()
            if bbox:
                txt_img = txt_img.crop((bbox[0]-5, bbox[1]-5, bbox[2]+5, bbox[3]+5))
            
            return txt_img
            
        except Exception as e:
            # print(f"Handwrite failed: {e}")
            return None

    def _draw_mounted_slide(self, canvas, img_path, x, y, cw, ch, meta, show_date, show_exif, cfg, preview_mode=False, forced_format=None, custom_l1=None, custom_l2=None, font_path=None):
        """
        EN: Draw Accurate Slide Master V6 (Physics Engine)
        CN: 绘制幻灯片大师 V6 (物理仿真引擎)
        """
        
        # --- 1. Format Detection & Physics Constants ---
        # EN: Detect format based on cell width (cw) and aspect ratio
        # CN: 根据单元格宽度 (cw) 和纵横比检测画幅
        
        cw_int = int(cw)
        # aspect = cw / ch  # This was unreliable if ch varies slightly or user swaps w/h
        
        # aperture aspect ratio is more reliable for distinguishing 645 vs 6x6
        ap_w = cfg.get('inner_w', 850)
        ap_h = cfg.get('inner_h', 567)
        ap_ratio = ap_w / ap_h
        
        format_name = "135" # Default
        
        if forced_format:
            # EN: Force format if manually specified (bypass auto-detection)
            # CN: 如果手动指定了画幅，强制使用（绕过自动检测）
            ff = str(forced_format).upper().replace("MATIN_", "")
            if ff == "66": format_name = "6x6"
            elif ff == "67": format_name = "6x7"
            elif ff in ["645", "135"]: format_name = ff
            else: format_name = "135" # Fallback
        else:
            # EN: Auto-detect based on dimensions (Legacy / Fallback)
            if abs(cw_int - 2126) < 50:
                 format_name = "6x7"
            elif abs(cw_int - 1724) < 50:
                 if 0.9 < ap_ratio < 1.1:
                     format_name = "6x6"
                 else:
                     format_name = "645"
            elif abs(cw_int - 1252) < 50:
                 format_name = "135"
        
        # EN: Get aperture dimensions from config or defaults
        # CN: 从配置获取开口尺寸 (inner_w/h)
        ap_w = cfg.get('inner_w', 850)
        ap_h = cfg.get('inner_h', 567)
        
        # --- 2. Physics Parameters ---
        COLOR_MOUNT = (230, 230, 230)
        CORNER = 10
        seam_p = 20
        if_p = 60 # Inner Frame padding
        margin_x = 100 # Margin for text
        
        draw = ImageDraw.Draw(canvas)

        if preview_mode:
            # --- Simplified Render for Preview ---
            # 1. Mount Body (Flat) - No Outline
            draw.rectangle([x, y, x+cw-1, y+ch-1], fill=COLOR_MOUNT)
            
            # 2. Key Structure Lines (Optional, simpler)
            # Only draw the aperture frame for reference
            ax, ay = x + (cw - ap_w) // 2, y + (ch - ap_h) // 2
            
            # 3. Inner Frame area (Skipped for cleaner look)
            
            # 4. Image Place (Solid white background first)
            # Aperture Mask (Rounded Corners) logic is slightly expensive, maybe just rect?
            # User wants visual accuracy, so we keep image processing but skip shadows
            
            # --- Image Processing (Keep logic same for layout accuracy) ---
            if os.path.exists(img_path):
                 with Image.open(img_path) as img:
                    img = img.convert('RGB')
                    try: img = ImageOps.autocontrast(img, cutoff=1)
                    except: pass
                    
                    # Adaptive Crop Logic
                    ir = img.width / img.height
                    ar = ap_w / ap_h
                    if ir > ar: nw, nh = int(ap_h * ir), ap_h
                    else: nw, nh = ap_w, int(ap_w / ir)
                    
                    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                    cx, cy = nw // 2, nh // 2
                    img = img.crop((cx - ap_w//2, cy - ap_h//2, cx - ap_w//2 + ap_w, cy - ap_h//2 + ap_h))
                    
                    # Skip Gamma Correction for preview speed? Or keep for accuracy? Keep for accuracy.
                    
                    # Simple paste without rounded corners if faster? 
                    # Rounded corners are cheap enough for preview usually.
                    f_mask = Image.new('L', (ap_w, ap_h), 0)
                    ImageDraw.Draw(f_mask).rounded_rectangle([0, 0, ap_w-1, ap_h-1], radius=CORNER, fill=255)
                    canvas.paste(img, (ax, ay), f_mask)
            else:
                # White placeholder
                draw.rounded_rectangle([ax, ay, ax+ap_w, ay+ap_h], radius=CORNER, fill=(255, 255, 255))
            
            # EN: In detailed preview mode (Wireframe), we STOP here. No labels.
            # CN: 在极简预览模式下，到此为止。不渲染标签。
            return
        
        else:
            # --- Full V6 Physics Render ---
            # --- 3. Mount Shadow (Outer) ---
            # EN: Dynamic shadow padding
            ds_pad = 50
            ds = Image.new('RGBA', (cw + ds_pad*2, ch + ds_pad*2), (0, 0, 0, 0))
            ImageDraw.Draw(ds).rectangle([ds_pad, ds_pad, ds_pad+cw-1, ds_pad+ch-1], fill=(0, 0, 0, 64))
            ds = ds.filter(ImageFilter.GaussianBlur(radius=8))
            canvas.paste(ds, (x - ds_pad + 3, y - ds_pad + 3), ds)

            # --- 4. Mount Body ---
            draw.rectangle([x, y, x+cw-1, y+ch-1], fill=COLOR_MOUNT)

            # --- 5. Structural Details (Seams & Pins) ---
            # Outer Seam
            draw.rectangle([x+seam_p, y+seam_p, x+cw-seam_p-1, y+ch-seam_p-1], outline=(200, 200, 200), width=1)
            draw.rectangle([x+seam_p+1, y+seam_p+1, x+cw-seam_p, y+ch-seam_p], outline=(255, 255, 255, 120), width=1)
            
            ax, ay = x + (cw - ap_w) // 2, y + (ch - ap_h) // 2
            
            # Inner Frame
            if_rect = [ax-if_p, ay-if_p, ax+ap_w+if_p-1, ay+ap_h+if_p-1]
            draw.rectangle(if_rect, outline=(210, 210, 210), width=2)
            # Bevel highlights for inner frame
            draw.line([if_rect[0]+1, if_rect[3], if_rect[2], if_rect[3]], fill=(255, 255, 255, 180), width=1)
            draw.line([if_rect[2], if_rect[1]+1, if_rect[2], if_rect[3]], fill=(255, 255, 255, 180), width=1)

            # Registration Pins
            pin_r, pin_off = 10, 50
            # If dimensions are small (e.g. preview), scale down pin offset? keeping fixed for physics accuracy normally.
            pins = [(x+pin_off, y+pin_off), (x+cw-pin_off, y+pin_off), (x+pin_off, y+ch-pin_off), (x+cw-pin_off, y+ch-pin_off)]
            for px, py in pins:
                draw.ellipse([px-pin_r, py-pin_r, px+pin_r, py+pin_r], fill=(210, 210, 210))
                draw.ellipse([px-pin_r+1, py-pin_r+1, px+pin_r-1, py+pin_r-1], fill=COLOR_MOUNT)
                draw.arc([px-pin_r, py-pin_r, px+pin_r, py+pin_r], start=0, end=180, fill=(255, 255, 255, 200))

            # --- 6. Image Processing & Mounting ---
            if os.path.exists(img_path):
                 with Image.open(img_path) as img:
                    img = img.convert('RGB')
                    try:
                        img = ImageOps.autocontrast(img, cutoff=1)
                    except: pass # Handle potential errors with empty images
                    
                    # V6 Adaptive Crop Logic (No Black Borders)
                    # Check orientation match
                    img_is_portrait = img.height > img.width
                    ap_is_portrait = ap_h > ap_w
                    
                    ir = img.width / img.height
                    ar = ap_w / ap_h
                    
                    # Stretch strategy: Cover the aperture fully (Bleed)
                    if ir > ar: 
                        nw, nh = int(ap_h * ir), ap_h
                    else: 
                        nw, nh = ap_w, int(ap_w / ir)
                    
                    # Resize and Align Center
                    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                    cx, cy = nw // 2, nh // 2
                    img = img.crop((cx - ap_w//2, cy - ap_h//2, cx - ap_w//2 + ap_w, cy - ap_h//2 + ap_h))
                    
                    # Gamma Correction (Simulate Lightbox Transmission)
                    img = img.point(lambda i: int(pow(i/255.0, 0.8) * 255))
                    
                    # Aperture Mask (Rounded Corners)
                    f_mask = Image.new('L', (ap_w, ap_h), 0)
                    ImageDraw.Draw(f_mask).rounded_rectangle([0, 0, ap_w-1, ap_h-1], radius=CORNER, fill=255)
                    
                    # Paste Image
                    canvas.paste(img, (ax, ay), f_mask)

            # --- 7. Inner Shadow (Physical Depth) ---
            is_pad = 60
            is_c = Image.new('L', (ap_w + is_pad*2, ap_h + is_pad*2), 120) 
            ImageDraw.Draw(is_c).rounded_rectangle([is_pad, is_pad, is_pad+ap_w-1, is_pad+ap_h-1], radius=CORNER, fill=0)
            is_c = is_c.filter(ImageFilter.GaussianBlur(radius=10))
            is_mask = is_c.crop((is_pad, is_pad, is_pad+ap_w, is_pad+ap_h))
            is_layer = Image.new('RGBA', (ap_w, ap_h), (0, 0, 0, 255))
            canvas.paste(is_layer, (ax, ay), is_mask)

        # --- 8. Handwritten Labels (Shared Logic for Both Modes to ensure layout match) ---
        # Get metadata
        data = meta.get_data(img_path)
        date_str, exif_str = self.get_clean_exif(data) # Inherited from BaseFilmRenderer
        
        # --- Label Logic ---
        # Line 1: Title / Date
        l_txt = ""
        if custom_l1:
            l_txt = custom_l1
            if show_date and date_str:
                l_txt += f" / {date_str}"
        else:
             # Default: Empty implies NO Format Name. 
             # Only show date if enabled.
             if show_date and date_str:
                 l_txt = date_str
             else:
                 l_txt = "" # Empty

        # Line 2: Info / EXIF
        r_txt = ""
        if custom_l2:
            r_txt = custom_l2
            if show_exif and exif_str:
                r_txt += f"  {exif_str}"
        else:
             if show_exif:
                 r_txt = exif_str if exif_str else "No Data"
             else:
                 r_txt = ""

        # Dynamic Font Size
        # removing hardcoded minimums (30, 22) to allow thumbnail scaling
        if format_name == "135":
            l_fs = int(0.04 * cw)
        else:
            # EN: Unified 0.035 scale for medium formats (645, 6x6, 6x7) as per reference
            l_fs = int(0.035 * cw)
             
        r_fs = int(0.03 * cw)
        
        # Safe minimum of 8px to assume readable rendering
        # Safe minimum of 8px to assume readable rendering
        l_img = self._get_handwritten_img(l_txt, font_size=max(8, l_fs), font_path=font_path, bold=True)
        r_img = self._get_handwritten_img(r_txt, font_size=max(8, r_fs), color=(40, 40, 40), font_path=font_path, bold=True)

        if l_img and r_img:
            # EN: Disable jitter in preview mode for cleaner alignment
            if preview_mode:
                l_jx, l_jy = 0, 0
                r_jx, r_jy = 0, 0
            else:
                l_jx, l_jy = random.randint(-12, 12), random.randint(-12, 12)
                r_jx, r_jy = random.randint(-12, 12), random.randint(-12, 12)
            
            if format_name == "6x6":
                # --- 6x6 Special: Split Layout (Top/Bottom Seam Zones) ---
                # Use local relative coordinates
                ay_rel = (ch - ap_h) // 2
                
                # Top Zone: Outer Seam -> Inner Frame Top
                top_zone_start = seam_p
                top_zone_end = ay_rel - if_p
                top_safe_h = top_zone_end - top_zone_start
                
                # Bottom Zone: Inner Frame Bottom -> Outer Seam Bottom
                bottom_zone_start = ay_rel + ap_h + if_p
                bottom_zone_end = ch - seam_p
                bottom_safe_h = bottom_zone_end - bottom_zone_start
                
                # Center vertically in zones
                l1_y_base = top_zone_start + (top_safe_h - l_img.height) // 2
                l2_y_base = bottom_zone_start + (bottom_safe_h - r_img.height) // 2 - 5 # Slight lift for safety
                
                # EN: Apply Multiply Blending for realism
                # 1. Create a white paper layer of slide size
                paper = Image.new("RGB", (cw, ch), (255, 255, 255))
                if l_img: paper.paste(l_img, (margin_x + l_jx, l1_y_base + l_jy), l_img)
                if r_img: paper.paste(r_img, (cw - margin_x - r_img.width + r_jx, l2_y_base + r_jy), r_img)
                
                # 2. Multiply with background
                slide_area = canvas.crop((x, y, x + cw, y + ch)).convert("RGB")
                multiplied = ImageChops.multiply(slide_area, paper)
                canvas.paste(multiplied, (x, y))
                
            else:
                # --- Unified Layout (135/645/6x7): Golden Ratio (bottom based) ---
                # Labels between aperture bottom and outer seam
                ap_bottom = (ch + ap_h) // 2
                seam_bottom = ch - seam_p
                safe_h = seam_bottom - ap_bottom
                
                # L1: 26% of safe zone
                l1_y_base = ap_bottom + int(safe_h * 0.26)
                # L2: 46% of safe zone
                l2_y_base = ap_bottom + int(safe_h * 0.46)
                
                # EN: Apply Multiply Blending for realism
                paper = Image.new("RGB", (cw, ch), (255, 255, 255))
                if l_img: paper.paste(l_img, (margin_x + l_jx, l1_y_base + l_jy), l_img)
                if r_img: paper.paste(r_img, (cw - margin_x - r_img.width + r_jx, l2_y_base + r_jy), r_img)
                
                slide_area = canvas.crop((x, y, x + cw, y + ch)).convert("RGB")
                multiplied = ImageChops.multiply(slide_area, paper)
                canvas.paste(multiplied, (x, y))

    def render_single_slide(self, img_path, cfg, meta_handler, show_date=True, show_exif=True, manual_format=None, custom_l1=None, custom_l2=None, font_path=None):
        """
        EN: Cleanly render a single slide in high fidelity (V6 Physics).
        CN: 以高保真 (V6 物理) 渲染单张幻灯片。
        """
        cell_w = cfg.get('cell_w', 1181) 
        cell_h = cfg.get('cell_h', 1181)
        
        # Extra padding for shadows to breathe
        pad = 60
        w, h = cell_w + pad*2, cell_h + pad*2
        
        # Transparent canvas
        canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        
        # Draw slide at center
        self._draw_mounted_slide(canvas, img_path, pad, pad, cell_w, cell_h, 
                                 meta_handler, show_date, show_exif, cfg, preview_mode=False, 
                                 forced_format=manual_format,
                                 custom_l1=custom_l1, custom_l2=custom_l2,
                                 font_path=font_path)
        
        return canvas
