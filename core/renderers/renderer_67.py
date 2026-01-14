# core/renderers/renderer_67.py
import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer67(BaseFilmRenderer):
    """
    EN: 6x7 Renderer (645-step edge markings & left-aligned jitter)
    CN: 6x7 画幅渲染器 (645 物理喷码步进 + 左对齐随机抖动版)
    """
    
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion):
        print("\n" + "="*65)
        print("CN: [67 3.2] 喷码逻辑校准 (步进: 645物理长度, 对齐: 左侧随机抖动)")
        print("="*65)
        
        final_cfg = meta_handler.get_contact_layout("67")
        new_w, new_h = final_cfg['canvas_w'], final_cfg['canvas_h']
        canvas = canvas.resize((new_w, new_h)) 
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235)) 
        
        c_w, c_h = new_w, new_h
        bg_color = (235, 235, 235)

        # 1. 物理常数与缩放字号
        MARGIN_RATIO = 2.75 / 56.0 
        PHOTO_ASPECT = 70.0 / 56.0 
        scaled_seg_font = self.seg_font.font_variant(size=32)
        
        sample_data = meta_handler.get_data(img_list[0])
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        raw_text = self.get_marking_str(sample_data, user_emulsion)

        m_x, m_y_t = final_cfg['margin_x'], final_cfg['margin_y_top']
        cg, rg = final_cfg['col_gap'], final_cfg['row_gap']
        cols, rows = final_cfg['cols'], final_cfg['rows']

        # 2. 物理尺寸精准计算
        col_pitch = (c_w - 2 * m_x) // cols
        photo_w = col_pitch - 150 
        photo_h = int(photo_w / PHOTO_ASPECT)
        side_margin = int(photo_h * MARGIN_RATIO)
        strip_h = photo_h + 2 * side_margin

        # --- 3. 喷码步进预设 (模拟 645 物理长度) ---
        # EN: 645 width is roughly 0.85x of 67 width
        # CN: 645 的物理宽度大约是 67 宽度的 0.85 倍
        marking_step = int(photo_w * 0.85) 

        tri_p = self.create_stretched_triangle(color=cur_color).resize((int(15 * 3.5), 15))

        # --- 4. 渲染循环 ---
        for r in range(rows):
            sy = m_y_t + r * (strip_h + rg)
            
            # [物理规范] 左侧起始黑边
            leader_start_x = m_x - side_margin
            draw.rectangle([leader_start_x, sy, c_w, sy + strip_h], fill=(12, 12, 12))
            
            # --- 喷码逻辑攻坚 (模拟 120 原厂连喷) ---
            # CN: 在黑条起始位置加一个 0~side_margin 之间的随机抖动，但不超出左边界
            # EN: Add jitter at the start of the strip, confined within the leader area
            current_marking_x = leader_start_x + random.randint(5, side_margin)
            
            while current_marking_x < c_w - 200:
                # CN: 喷码置于上黑边中心 / EN: Place marking in top margin center
                draw.text((current_marking_x, sy + (side_margin // 2) - 15), 
                          raw_text, font=self.led_font, fill=cur_color)
                # CN: 按 645 物理步进，并加入微小随机不稳定性
                current_marking_x += marking_step + random.randint(-20, 20)

            last_photo_right_x = 0
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(img_list): break
                
                curr_x = m_x + c * col_pitch + 20
                py = sy + side_margin 
                last_photo_right_x = curr_x + photo_w 
                
                # A. 粘贴照片 (EN: Force Landscape / CN: 强制横向)
                self._paste_photo(canvas, img_list[idx], curr_x, py, photo_w, photo_h, force_landscape=True)
                
                # B. 下侧序号三角 (CN: 物理中心对齐 / EN: Physical alignment)
                num_str = str(idx + 1)
                num_tw = draw.textlength(num_str, font=self.font)
                ax_start = (curr_x + photo_w // 2) - (tri_p.width + 50 + num_tw) // 2
                ay = py + photo_h + 5 
                canvas.paste(tri_p, (int(ax_start), int(ay + 5)), tri_p)
                draw.text((int(ax_start + tri_p.width + 50), int(ay)), num_str, font=self.font, fill=cur_color)

                # C. 右侧 EXIF (150px 压缩空间)
                data = meta_handler.get_data(img_list[idx])
                exif_x_base = last_photo_right_x + 35 
                self._draw_exif_p_scaled(canvas, data, exif_x_base, py, photo_h, cur_color, scaled_seg_font)

            if last_photo_right_x > 0:
                crop_line_x = last_photo_right_x + 150
                if crop_line_x < c_w:
                    draw.rectangle([crop_line_x, sy, c_w, sy + strip_h], fill=bg_color)

        return canvas

    def _draw_exif_p_scaled(self, canvas, data, start_x, py, photo_h, color, font):
        dt = data.get("DateTime", "")
        date_str = dt[2:10].replace(":", "/") if len(dt) >= 10 else "00/00/00"
        date_layer = self.create_rotated_text_with_font(date_str, font, 90, color)
        canvas.paste(date_layer, (int(start_x), int(py + photo_h // 2 - date_layer.height // 2)), date_layer)
        
        exif_str = f"f/{data.get('FNumber', '--')} {data.get('ExposureTimeStr', '--')}s {str(data.get('FocalLength', '---')).lower()}"
        exif_layer = self.create_rotated_text_with_font(exif_str, font, 90, color)
        canvas.paste(exif_layer, (int(start_x + 35), int(py + photo_h // 2 - exif_layer.height // 2)), exif_layer)

    def create_rotated_text_with_font(self, text, font, angle, color):
        left, top, right, bottom = font.getbbox(text)
        w, h = right - left, bottom - top
        txt_img = Image.new('RGBA', (w + 20, h + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        draw.text((10, 5), text, font=font, fill=color)
        return txt_img.rotate(angle, expand=True)

    def _paste_photo(self, canvas, path, x, y, w, h, force_landscape=False):
        with Image.open(path) as img:
            img_w, img_h = img.size
            if force_landscape and img_h > img_w: img = img.rotate(-90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))