# core/renderers/renderer_66.py
import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer66(BaseFilmRenderer):
    """
    EN: 66 Renderer. Fixed bottom margin to match inter-frame gaps and solved overflow.
    CN: 中英双语：66 渲染器。修正底部黑边高度使其与行间距一致，并解决喷码溢出。
    """
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None):
        print("CN: [Renderer] 执行 66 渲染 (精准等宽裁切版)...")
        draw = ImageDraw.Draw(canvas)
        c_w, c_h = canvas.size
        bg_color = (235, 235, 235) 
        
        m_y_t, m_y_b = cfg.get('margin_y_top', 600), cfg.get('margin_y_bottom', 370)
        c_gap, h_gap = cfg.get('col_gap', 150), cfg.get('row_gap', 220)
        cols, rows = 3, 4
        
        STRIP_RATIO = 61.5 / 56.0 
        v_padding_top = 80 
        frame_box_h = (c_h - m_y_t - m_y_b - (rows * h_gap)) // rows
        strip_w = int(frame_box_h * STRIP_RATIO)
        max_photo_w = int(frame_box_h) 
        step_y = frame_box_h + h_gap # 每一帧占用的总垂直跨度 (含间距)
        
        step_645 = int(step_y * 0.75) 
        start_x = (c_w - (cols * strip_w + (cols - 1) * c_gap)) // 2
        black_margin_w = (strip_w - max_photo_w) // 2 

        if not sample_data:
            sample_data = meta_handler.get_data(img_list[0])
            
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        raw_text = self.get_marking_str(sample_data, user_emulsion)
        edge_layer = self.create_rotated_text(raw_text, angle=90, color=cur_color)

        for c in range(cols):
            sx = start_x + c * (strip_w + c_gap)
            
            # --- 1. 铺设黑条与喷码 (645均布逻辑) ---
            # 先画到底部
            draw.rectangle([sx, m_y_t - v_padding_top, sx + strip_w, c_h], fill=(12, 12, 12))
            
            marking_y = m_y_t - v_padding_top + 40
            while marking_y < c_h - 100:
                lx = sx + black_margin_w // 2 - edge_layer.width // 2
                canvas.paste(edge_layer, (int(lx), int(marking_y + random.randint(-30, 30))), edge_layer)
                marking_y += step_645

            last_frame_y_start = 0
            num_in_col = 0

            # --- 2. 渲染照片与元数据 ---
            for r in range(rows):
                idx = c * rows + r 
                if idx >= len(img_list): break
                num_in_col += 1
                curr_y = m_y_t + r * step_y
                last_frame_y_start = curr_y 
                
                frame_data = meta_handler.get_data(img_list[idx])
                with Image.open(img_list[idx]) as img:
                    img_w, img_h = img.size
                    scale = frame_box_h / img_h
                    new_w, new_h = int(img_w * scale), int(img_h * scale)
                    if new_w > max_photo_w:
                        scale = max_photo_w / new_w
                        new_w, new_h = int(new_w * scale), int(new_h * scale)
                    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    px = sx + (strip_w - new_w) // 2
                    canvas.paste(img_resized, (int(px), int(curr_y)))

                # 元数据 (焦距单位 mm 小写)
                data = meta_handler.get_data(img_list[idx])
                date_str, exif_str = self.get_clean_exif(data)
                
                text_y_start = curr_y + new_h + 15
                if date_str and str(date_str).strip().upper() != "NONE":
                    draw.text((sx + strip_w//2 - draw.textlength(date_str, font=self.seg_font)//2, text_y_start), 
                          date_str, font=self.seg_font, fill=cur_color)
                    
                if exif_str and str(exif_str).strip().upper() != "NONE":
                    draw.text((sx + strip_w//2 - draw.textlength(exif_str, font=self.seg_font)//2, text_y_start + 45), 
                          exif_str, font=self.seg_font, fill=cur_color)

                # 右侧标识
                r_mid = sx + strip_w - black_margin_w // 2
                tri_raw = self.create_stretched_triangle(color=cur_color)
                tri_final = tri_raw.resize((int(tri_raw.size[0] * 3.5), tri_raw.size[1])).rotate(-90, expand=True)
                canvas.paste(tri_final, (int(r_mid - tri_final.width//2), int(curr_y + new_h//2 - 105)), tri_final)
                num_layer = self.create_rotated_text(str(idx + 1), 90, color=cur_color)
                canvas.paste(num_layer, (int(r_mid - num_layer.width//2), int(curr_y + new_h//2 + 25)), num_layer)

            # --- 3. 精准裁切 (确保最后一行下方黑边高度 = 行间黑边高度) ---
            if num_in_col > 0:
                # EN: The visual gap between photos is created by the step_y.
                # CN: 照片间的视觉间隔是由 step_y 定义的。
                # EN: Cutting exactly at (last_start + step_y) ensures the final black tail 
                #     is identical to the black area between frame 1 and 2.
                # CN: 裁切线 = 最后一帧起点 + 一个完整步进长度。
                # 这保证了最后一帧下面的黑边厚度不多不少，刚好等于中间行的厚度。
                crop_line_y = last_frame_y_start + step_y
                
                # 用背景色遮盖该线以下的所有内容
                draw.rectangle([sx, crop_line_y, sx + strip_w, c_h], fill=bg_color)

        return canvas