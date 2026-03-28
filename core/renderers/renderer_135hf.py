# core/renderers/renderer_135hf.py
# EN: Renderer for 135 Half-Frame format (18x24mm) - v2.0
# CN: 135 半格画幅渲染器 (18x24mm) - v2.0

import os
from PIL import Image, ImageDraw, ImageFont
from .renderer_135 import Renderer135

class Renderer135HF(Renderer135):
    """
    EN: 135 Half-Frame Format - Precision spacing (1.0mm) for 72 frames
    CN: 135 半格画幅 - 1.0mm 精准间距，适配 72 张超大容量预览
    """
    
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None, orientation=None, show_date=True, show_exif=True):
        print("\n" + "="*65)
        print(f"EN: [135HF] Rendering Half-Frame Contact Sheet (Orientation: {orientation or 'P'})")
        print(f"CN: [135HF] 正在渲染半格索引页 (方向: {orientation or 'P'})")
        print("="*65)
        
        # 1. EN: Load 135HF configuration / CN: 加载 135HF 配置
        final_cfg = meta_handler.get_contact_layout("135HF")
        new_w, new_h = final_cfg.get('canvas_w', 4800), final_cfg.get('canvas_h', 6000)
        canvas = canvas.resize((new_w, new_h))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235))

        # 2. EN: Physical Constants (mm) / CN: 物理常数 (mm)
        STRIP_W_MM = 35.0
        GAP_MM = 1.0  
        SPROC_W_MM, SPROC_H_MM = 2.0, 2.8
        INFO_ZONE_MM = 5.5
        
        m_x, m_y_t = final_cfg.get('margin_x', 150), final_cfg.get('margin_y_top', 500)
        usable_w_px = (new_w - 2 * m_x)
        px_per_mm = usable_w_px / 228.0 # EN: Baseline 228mm for parity / CN: 对齐基准 228mm
        
        # Derived pixel dimensions
        gap_px = int(GAP_MM * px_per_mm)
        strip_px = int(STRIP_W_MM * px_per_mm)
        info_px = int(INFO_ZONE_MM * px_per_mm)
        sp_w, sp_h = int(SPROC_W_MM * px_per_mm), int(SPROC_H_MM * px_per_mm)
        
        # 3. EN: Branding & Meta Prep / CN: 品牌与元数据准备
        standard_data = sample_data if sample_data else meta_handler.get_data(img_list[0])
        film_text = standard_data.get('EdgeCode') or standard_data.get('Film') or user_emulsion or "FILM"
        prefix = f"{user_emulsion.strip()}  " if user_emulsion and user_emulsion.strip() != film_text else ""
        display_name = f"{prefix}{film_text}"
        cur_color = standard_data.get("ContactColor", (245, 130, 35, 210))
        
        em_font = self.led_font.font_variant(size=int(1.3 * px_per_mm))
        date_font = self.into_dot_font.font_variant(size=int(1.2 * px_per_mm))
        exif_font = self.seg_font.font_variant(size=int(1.2 * px_per_mm))

        # 4. EN: Orientation Branching / CN: 方向分支
        if orientation == 'L':
            # EN: L-Mode: Vertical strips (6 columns), Landscape Photos (24x18)
            # CN: L 模式：垂直底片条 (6 列)，横向照片 (24x18)
            PHOTO_W_MM, PHOTO_H_MM = 24.0, 18.0
            cols, rows = 6, 12
            pw, ph = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)
            col_pitch = usable_w_px // cols
            
            for c in range(cols):
                sx = m_x + c * col_pitch + (col_pitch - strip_px) // 2
                strip_len = rows * (ph + gap_px)
                draw.rectangle([sx, m_y_t, sx + strip_px, m_y_t + strip_len], fill=(12, 12, 12))
                
                # EN: Draw vertical sprockets / CN: 绘制垂直齿孔
                self._draw_vertical_sprockets_vector(canvas, sx, m_y_t, m_y_t + strip_len, info_px, strip_px, sp_w, sp_h, px_per_mm, display_name)
                
                for r in range(rows):
                    idx = c * rows + r # Vertical column-major
                    if idx >= len(img_list): break
                    
                    curr_y = m_y_t + r * (ph + gap_px)
                    px = sx + info_px
                    self._paste_photo_for_hf(canvas, img_list[idx], px, curr_y, pw, ph)
                    
                    # Numbering/Branding on RIGHT edge (90deg Rotated)
                    if r % 2 == 0:
                        num_idx = (idx // 2) + 1 # Logic: Continuous sequence
                        num_layer = self.create_rotated_text(str(num_idx), 90, color=cur_color)
                        nx = sx + strip_px - info_px//2 - num_layer.width//2
                        canvas.paste(num_layer, (int(nx), int(curr_y + (ph - num_layer.height)//2)), num_layer)
                    
                    if r % 4 == 1:
                        brand_layer = self.create_rotated_seg_text(display_name, 90, cur_color)
                        bx = sx + strip_px - info_px//2 - brand_layer.width//2
                        canvas.paste(brand_layer, (int(bx), int(curr_y + (ph - brand_layer.height)//2)), brand_layer)
                    
                    # Data Back (EXIF)
                    p_data = meta_handler.get_data(img_list[idx])
                    self._draw_glowing_data_back(canvas, p_data, px, curr_y, pw, ph, cur_color, date_font, exif_font, px_per_mm, show_date=show_date, show_exif=show_exif)
        else:
            # EN: P-Mode: Horizontal strips (6 rows), Portrait Photos (18x24)
            # CN: P 模式：水平底片条 (6 行)，竖向照片 (18x24)
            PHOTO_W_MM, PHOTO_H_MM = 18.0, 24.0
            cols, rows = 12, 6
            pw, ph = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)
            rg = final_cfg.get('row_gap', 100)
            
            for r in range(rows):
                sy = m_y_t + r * (strip_px + rg)
                strip_w = cols * (pw + gap_px)
                draw.rectangle([m_x, sy, m_x + strip_w, sy + strip_px], fill=(12, 12, 12))
                
                # EN: Draw horizontal sprockets / CN: 绘制水平齿孔
                self._draw_iso_sprockets_vector(canvas, m_x, m_x + strip_w, sy, info_px, strip_px, sp_w, sp_h, px_per_mm, display_name)
                
                for c in range(cols):
                    idx = r * cols + c
                    if idx >= len(img_list): break
                    
                    curr_x = m_x + c * (pw + gap_px)
                    py = sy + info_px
                    self._paste_photo_for_hf(canvas, img_list[idx], curr_x, py, pw, ph)
                    
                    # Numbering/Branding on TOP edge (Normal)
                    if c % 2 == 0:
                        num_idx = (idx // 2) + 1
                        val_str = str(num_idx)
                        tw = draw.textlength(val_str, font=em_font)
                        draw.text((curr_x + (pw - tw)//2, sy + int(0.2 * px_per_mm)), val_str, font=em_font, fill=cur_color)
                        
                    if c % 4 == 1:
                        bw = draw.textlength(display_name, font=em_font)
                        bx = curr_x + (pw - bw)//2
                        self._draw_single_glowing_text(canvas, display_name, (bx, sy + int(0.2 * px_per_mm)), em_font, cur_color)
                        
                    # Data Back (EXIF)
                    p_data = meta_handler.get_data(img_list[idx])
                    self._draw_glowing_data_back(canvas, p_data, curr_x, py, pw, ph, cur_color, date_font, exif_font, px_per_mm, show_date=show_date, show_exif=show_exif)

            # Cleanup right side for P-mode
            cutoff_x = m_x + cols * (pw + gap_px) + int(1.0 * px_per_mm)
            if cutoff_x < new_w:
                draw.rectangle([cutoff_x, 0, new_w, new_h], fill=(235, 235, 235))

        return canvas

    def _draw_vertical_sprockets_vector(self, canvas, sx, start_y, end_y, info_px, strip_px, sp_w, sp_h, px_per_mm, film_name):
        """EN: Draw vertical sprockets for L-mode"""
        draw = ImageDraw.Draw(canvas)
        pitch_px = 4.75 * px_per_mm
        is_mov = any(x in film_name.lower() for x in ['vision', '500t', '250d', 'movie', 'cinema', '52', '72'])
        
        curr_y = start_y + pitch_px / 2
        while curr_y < end_y:
            # Left
            lx = sx + (info_px - sp_w) // 2
            self._draw_single_sprocket(draw, lx, curr_y - sp_h//2, sp_w, sp_h, is_mov)
            # Right
            rx = sx + strip_px - (info_px - sp_w) // 2 - sp_w
            self._draw_single_sprocket(draw, rx, curr_y - sp_h//2, sp_w, sp_h, is_mov)
            curr_y += pitch_px

    def _draw_single_sprocket(self, draw, x, y, w, h, is_movie=False):
        if is_movie:
            path = self.make_custom_sprocket_path(x, y, w, h)
            draw.polygon(path, fill=(220, 220, 220, 200))
        else:
            draw.rounded_rectangle([x, y, x + w, y + h], radius=int(0.5 * (w / 2.0)), fill=(220, 220, 220, 200))

    def _paste_photo_for_hf(self, canvas, path, x, y, w, h):
        """EN: Paste and rotate photo intelligently"""
        with Image.open(path) as img:
            if w > h: # Landscape slot
                if img.height > img.width: img = img.rotate(-90, expand=True)
            else: # Portrait slot
                if img.width > img.height: img = img.rotate(-90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))
