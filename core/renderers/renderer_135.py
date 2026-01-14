# core/renderers/renderer_135.py
import os
from PIL import Image, ImageDraw, ImageFont
from .base_renderer import BaseFilmRenderer

class Renderer135(BaseFilmRenderer):
    """
    EN: 135 Format - Dynamic EdgeCode & Precision Positioning (v9.2)
    CN: 135 画幅 - 动态喷码修正版：解决写死字符串问题、数据后背极低位压低。
    """
    
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion):
        print("\n" + "="*65)
        print("CN: [135 9.2] 动态喷码：修复 EdgeCode 读取逻辑，压低右下角 EXIF")
        print("="*65)
        
        final_cfg = meta_handler.get_contact_layout("135")
        new_w, new_h = final_cfg.get('canvas_w', 4800), final_cfg.get('canvas_h', 6000)
        canvas = canvas.resize((new_w, new_h)) 
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235)) 
        
        # --- 1. ISO 1007 物理参数 (mm) ---
        STRIP_W_MM, PHOTO_W_MM, PHOTO_H_MM = 35.0, 36.0, 24.0
        GAP_MM = 2.0           # 2mm 过片间隙
        SPROC_W_MM, SPROC_H_MM = 2.0, 2.8 
        INFO_ZONE_MM = 5.5     
        
        cols, rows = final_cfg.get('cols', 6), final_cfg.get('rows', 6)
        m_x, m_y_t = final_cfg.get('margin_x', 150), final_cfg.get('margin_y_top', 500)
        
        # px_per_mm 计算
        col_pitch_px = (new_w - 2 * m_x) // cols
        px_per_mm = (col_pitch_px * (PHOTO_W_MM / (PHOTO_W_MM + GAP_MM))) / PHOTO_W_MM
        
        photo_w, photo_h = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)
        gap_w, strip_h, info_h = int(GAP_MM * px_per_mm), int(STRIP_W_MM * px_per_mm), int(INFO_ZONE_MM * px_per_mm)
        sp_w, sp_h = int(SPROC_W_MM * px_per_mm), int(SPROC_H_MM * px_per_mm)
        rg = final_cfg.get('row_gap', 150)
        
        # 统一缩小的喷码字号 (1.6mm 物理高度)
        em_font = ImageFont.truetype(self.led_font.path, int(1.6 * px_per_mm)) 
        db_font = ImageFont.truetype(self.seg_font.path, int(1.6 * px_per_mm)) 
        
        for r in range(rows):
            sy = m_y_t + r * (strip_h + rg)
            strip_start_x, strip_end_x = m_x - gap_w // 2, m_x + (cols * (photo_w + gap_w)) - gap_w // 2
            
            draw.rectangle([strip_start_x, sy, strip_end_x, sy + strip_h], fill=(12, 12, 12))
            self._draw_iso_sprockets(draw, strip_start_x, strip_end_x, sy, info_h, strip_h, sp_w, sp_h, px_per_mm)

            for c in range(cols):
                idx = r * cols + c
                if idx >= len(img_list): break
                
                curr_x, py = m_x + c * (photo_w + gap_w), sy + info_h 
                data = meta_handler.get_data(img_list[idx])
                cur_color = data['ContactColor']
                
                self._paste_photo_auto_rotate(canvas, img_list[idx], curr_x, py, photo_w, photo_h)
                
                # --- [修正逻辑] 动态 EdgeCode ---
                # EN: Prioritize EdgeCode, fallback to Film name, then Emulsion
                # CN: 优先级：EdgeCode > 胶卷名称 > 用户填写的乳剂名
                display_code = data.get('EdgeCode') or data.get('Film') or user_emulsion
                top_label = f"{idx + 1}  {display_code}"
                
                tw = draw.textlength(top_label, font=em_font)
                # 顶部 2mm 缝隙垂直居中
                draw.text((curr_x + (photo_w - tw)//2, sy + int(0.2 * px_per_mm)), top_label, font=em_font, fill=cur_color)
                
                # 底部过片间隙帧号
                gap_center_x = curr_x + photo_w + (gap_w // 2)
                frame_label = f"{idx + 1}A"
                fw = draw.textlength(frame_label, font=em_font)
                # 底部 2mm 缝隙垂直居中
                draw.text((gap_center_x - fw//2, sy + strip_h - int(1.8 * px_per_mm)), frame_label, font=em_font, fill=cur_color)
                
                # 压低的数据后背 (极靠右下角)
                self._draw_glowing_data_back(canvas, data, curr_x, py, photo_w, photo_h, cur_color, db_font, px_per_mm)

        return canvas

    def _draw_iso_sprockets(self, draw, x_start, x_end, sy, info_h, strip_h, sw, sh, px_mm):
        # 物理对齐：外边 2mm + 齿孔 2.8mm + 内边 0.7mm = 5.5mm
        y_top = sy + int(2.0 * px_mm) 
        y_bottom = sy + strip_h - int(2.0 * px_mm) - sh
        step_px = 4.75 * px_mm 
        curr_x = x_start + (step_px / 4)
        while curr_x < x_end - sw:
            for base_y in [y_top, y_bottom]:
                draw.rounded_rectangle([curr_x, base_y, curr_x + sw, base_y + sh], radius=5, fill=(235, 235, 235))
            curr_x += step_px

    def _paste_photo_auto_rotate(self, canvas, path, x, y, w, h):
        with Image.open(path) as img:
            if img.height > img.width: img = img.rotate(-90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))

    def _draw_single_glowing_text(self, canvas, text, pos, font, color):
        draw = ImageDraw.Draw(canvas)
        glow_color = (color[0], color[1], color[2], 75)
        draw.text((pos[0]+1, pos[1]+1), text, font=font, fill=glow_color)
        draw.text(pos, text, font=font, fill=color)

    def _draw_glowing_data_back(self, canvas, data, px, py, pw, ph, color, font, px_mm):
        """ CN: 极低位对齐：距离照片边缘仅 1mm (约 0.1mm 物理安全距离) """
        # 1. 日期 (最底层)
        dt = data.get("DateTime", "")
        if dt and len(dt) >= 10:
            date_str = dt[2:10].replace(":", " ")
            tw_d = ImageDraw.Draw(canvas).textlength(date_str, font=font)
            # 边距压到 1mm (px_mm * 1.0)
            self._draw_single_glowing_text(canvas, date_str, (px + pw - tw_d - int(1.0 * px_mm), py + ph - int(2.0 * px_mm)), font, color)
        
        # 2. EXIF (日期上方)
        if data.get('FNumber') != '--':
            exif_s = f"f/{data['FNumber']} {data['ExposureTimeStr']}"
            tw_e = ImageDraw.Draw(canvas).textlength(exif_s, font=font)
            self._draw_single_glowing_text(canvas, exif_s, (px + pw - tw_e - int(1.0 * px_mm), py + ph - int(4.0 * px_mm)), font, color)