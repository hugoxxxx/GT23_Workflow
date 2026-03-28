# core/renderers/renderer_135hf.py
# EN: Renderer for 135 Half-Frame format (18x24mm) - v1.0
# CN: 135 半格画幅渲染器 (18x24mm) - v1.0

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

        # 2. EN: Physical Parameters (mm) / CN: 物理参数 (mm)
        STRIP_W_MM = 35.0
        GAP_MM = 1.0  
        SPROC_W_MM, SPROC_H_MM = 2.0, 2.8
        INFO_ZONE_MM = 5.5
        
        m_x, m_y_t = final_cfg.get('margin_x', 150), final_cfg.get('margin_y_top', 500)
        usable_w_px = (new_w - 2 * m_x)
        px_per_mm = usable_w_px / 228.0 # EN: Baseline 228mm / CN: 基准 228mm
        
        gap_w = int(GAP_MM * px_per_mm)
        strip_h_w = int(STRIP_W_MM * px_per_mm)
        info_h_w = int(INFO_ZONE_MM * px_per_mm)
        sp_w, sp_h = int(SPROC_W_MM * px_per_mm), int(SPROC_H_MM * px_per_mm)
        row_gap = final_cfg.get('row_gap', 100)

        # 4. EN: Font variants / CN: 字体变体
        em_font = self.led_font.font_variant(size=int(1.3 * px_per_mm))
        db_font = self.seg_font.font_variant(size=int(1.3 * px_per_mm))

        # 5. EN: Roll-level metadata / CN: 全卷元数据
        standard_data = sample_data if sample_data else meta_handler.get_data(img_list[0])
        film_text = standard_data.get('EdgeCode') or standard_data.get('Film') or user_emulsion or "FILM"
        prefix = f"{user_emulsion.strip()}  " if user_emulsion and user_emulsion.strip() != film_text else ""
        display_code_from_standard = f"{prefix}{film_text}"
        cur_color = standard_data.get("ContactColor", (245, 130, 35, 210))

        # 6. EN: Rendering Logic based on Orientation / CN: 基于方向的渲染逻辑
        if orientation == 'L':
            # EN: L Mode - Vertical Strips, Landscape Photos (Like 645_L)
            # CN: L 模式 - 垂直底片条，横向照片 (对齐 645_L 逻辑)
            PHOTO_W_MM, PHOTO_H_MM = 24.0, 18.0
            cols, rows = 6, 12
            photo_w, photo_h = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)
            
            # EN: Calculate column pitch / CN: 计算列间距
            col_pitch_px = (photo_w + 3 * gap_w + 2 * info_h_w) # Simple approx
            col_pitch_px = usable_w_px // cols
            
            for c in range(cols):
                sx = m_x + c * col_pitch_px + (col_pitch_px - strip_h_w) // 2
                draw.rectangle([sx, m_y_t, sx + strip_h_w, m_y_t + rows * (photo_h + gap_w)], fill=(12, 12, 12))
                # EN: Render Vertical Sprocket Info (Left & Right)
                # CN: 渲染垂直齿孔信息 (左和右)
                # Note: For simplicity, we reuse the vector drawer but with rotation if needed.
                # Actually, 645L draws vertical strips. I will follow that aesthetic.
                
                for r in range(rows):
                    idx = c * rows + r # Column-major for vertical strips
                    if idx >= len(img_list): break
                    
                    curr_y = m_y_t + r * (photo_h + gap_w)
                    px = sx + info_h_w
                    self._paste_photo_for_hf(canvas, img_list[idx], px, curr_y, photo_w, photo_h)
                    
                    # Numbering and branding on the right margin of vertical strip
                    if r % 2 == 0:
                        num_idx = (c * (rows // 2)) + (r // 2) + 1
                        num_layer = self.create_rotated_text(str(num_idx), 90, color=cur_color)
                        nx = sx + strip_h_w - info_h_w//2 - num_layer.width//2
                        canvas.paste(num_layer, (int(nx), int(curr_y + (photo_h - num_layer.height)//2)), num_layer)
        else:
            # EN: P Mode - Horizontal Strips, Portrait Photos (Original P logic)
            # CN: P 模式 - 水平底片条，竖向照片 (原 P 逻辑)
            PHOTO_W_MM, PHOTO_H_MM = 18.0, 24.0
            cols, rows = 12, 6 
            photo_w, photo_h = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)

            for r in range(rows):
                sy = m_y_t + r * (strip_h_w + row_gap)
                strip_start_x = m_x - gap_w // 2
                strip_end_x = m_x + (cols * (photo_w + gap_w)) - gap_w // 2
                
                draw.rectangle([strip_start_x, sy, strip_end_x, sy + strip_h_w], fill=(12, 12, 12))
                self._draw_iso_sprockets_vector(canvas, strip_start_x, strip_end_x, sy, info_h_w, strip_h_w, sp_w, sp_h, px_per_mm, display_code_from_standard)

                for c in range(cols):
                    idx = r * cols + c
                    if idx >= len(img_list): break
                    
                    curr_x = m_x + c * (photo_w + gap_w)
                    py = sy + info_h_w
                    self._paste_photo_for_hf(canvas, img_list[idx], curr_x, py, photo_w, photo_h)

                    if c % 2 == 0:
                        thirteen_five_idx = (r * (cols // 2)) + (c // 2) + 1
                        top_label = f"{thirteen_five_idx}"
                        tw = draw.textlength(top_label, font=em_font)
                        draw.text((curr_x + (photo_w - tw)//2, sy + int(0.2 * px_per_mm)), top_label, font=em_font, fill=cur_color)

                    if (c % 4 == 1):
                        brand_text = display_code_from_standard
                        bw = draw.textlength(brand_text, font=em_font)
                        brand_x = curr_x + (photo_w - bw) // 2
                        self._draw_single_glowing_text(canvas, brand_text, (brand_x, sy + int(0.2 * px_per_mm)), em_font, cur_color)

                # EN: Render data back (EXIF) per frame / CN: 每帧渲染数据背 (EXIF)
                sample_data_for_back = meta_handler.get_data(img_list[idx])
                date_font = self.into_dot_font.font_variant(size=int(1.2 * px_per_mm))
                exif_font = self.seg_font.font_variant(size=int(1.2 * px_per_mm))
                
                self._draw_glowing_data_back(
                    canvas, sample_data_for_back, curr_x, py, photo_w, photo_h,
                    cur_color, date_font, exif_font, px_per_mm,
                    show_date=show_date, show_exif=show_exif
                )

        # 7. EN: Right-side cutoff cleanup / CN: 右侧截断清理
        max_photo_right = m_x + cols * (photo_w + gap_w) - gap_w
        final_cutoff_x = max_photo_right + int(1.0 * px_per_mm)
        if final_cutoff_x < new_w:
            draw.rectangle([final_cutoff_x, 0, new_w, new_h], fill=(235, 235, 235))

        return canvas

    def _paste_photo_for_hf(self, canvas, path, x, y, w, h):
        """EN: Paste photo and adapt to slot orientation (L or P)"""
        with Image.open(path) as img:
            # EN: Handle rotation based on target slot aspect
            # CN: 根据目标槽位宽高比处理旋转
            if w > h: # EN: Landscape slot / CN: 横向槽位 (24x18)
                if img.height > img.width: # EN: Portrait photo -> Rotate / CN: 竖向照片 -> 旋转
                    img = img.rotate(-90, expand=True)
            else: # EN: Portrait slot / CN: 竖向槽位 (18x24)
                if img.width > img.height: # EN: Landscape photo -> Rotate / CN: 横向照片 -> 旋转
                    img = img.rotate(-90, expand=True)
            
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))
