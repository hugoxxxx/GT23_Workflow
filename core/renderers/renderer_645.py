# core/renderers/renderer_645.py
import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer645(BaseFilmRenderer):
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion):
        print("\nCN: [645 2.0] 执行渲染 ...")
        
        # 1. 重新选择模式并重置画布尺寸
        # EN: Re-select mode and reset canvas size based on user choice
        choice = input(">>> 1.垂直条(L)照片横向 2.水平条(P)照片竖向 [默认 1]: ").strip()
        suffix = "L" if choice != "2" else "P"
        final_cfg = meta_handler.get_contact_layout(f"645_{suffix}")
        
        # CN: 关键步骤！根据 json 定义的宽高重新生成画布，确保 PL 模式长宽正确
        # EN: Resize canvas based on the specific JSON config for L or P
        new_w, new_h = final_cfg['canvas_w'], final_cfg['canvas_h']
        canvas = canvas.resize((new_w, new_h)) # 强制拉伸或重置
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235)) # 刷上背景色
        
        c_w, c_h = new_w, new_h
        bg_color = (235, 235, 235)
        mode = final_cfg.get("orientation", "landscape")

        m_x, m_y_t = final_cfg['margin_x'], final_cfg['margin_y_top']
        cg, rg = final_cfg['col_gap'], final_cfg['row_gap']
        cols, rows = final_cfg['cols'], final_cfg['rows']
        
        STRIP_RATIO = 61.5 / 41.5 
        PHOTO_ASPECT = 56.0 / 41.5 
        
        sample_data = meta_handler.get_data(img_list[0])
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        raw_text = self.get_marking_str(sample_data, user_emulsion)

        if mode == "landscape":
            # --- 645_L: 垂直底片条逻辑修正 ---
            area_w = (c_w - 2 * m_x - (cols-1) * cg) // cols
            # 垂直步进
            step_y = (c_h - m_y_t - final_cfg.get('margin_y_bottom', 350) - (rows * rg)) // rows + rg
            
            # 645 比例校准：适当减小照片比例，为底部留出呼吸感
            photo_h = int((step_y - rg) * 0.82) 
            photo_w = int(photo_h * PHOTO_ASPECT)
            strip_w = int(photo_h * STRIP_RATIO)
            
            edge_layer = self.create_rotated_text(raw_text, angle=90, color=cur_color)
            tri_l = self.create_stretched_triangle(color=cur_color).resize((int(15 * 3.5), 15)).rotate(-90, expand=True)

            for c in range(cols):
                sx = m_x + c * (area_w + cg) + (area_w - strip_w) // 2
                draw.rectangle([sx, m_y_t - 80, sx + strip_w, c_h], fill=(12, 12, 12))
                
               # --- 1. 喷码逻辑：对齐靠上 + 限制抖动向上越界 ---
                # EN: Edge markings: Align to top with jitter limited to downward only
                # CN: 喷码逻辑：起始对齐靠上，抖动仅向下延伸，防止超出底片上边缘
                
                marking_step_y = c_h // 4 # 固定 4 个
                # 起始点设在边缘稍下方，jitter 范围设为 (0, +100)，确保不往上跑
                marking_y = (m_y_t - 80) + random.randint(0, 100) 
                
                left_margin_w = (strip_w - photo_w) // 2
                while marking_y < c_h - 100:
                    lx = sx + (left_margin_w // 2) - (edge_layer.width // 2)
                    canvas.paste(edge_layer, (int(lx), int(marking_y)), edge_layer)
                    # 步进加随机向下抖动
                    marking_y += marking_step_y + random.randint(0, 50)

                # --- EXIF 距离修正 (同步贴近照片) ---
                # EN: EXIF position refined to be closer to photo bottom
                # CN: EXIF 距离修正，紧贴照片底部 (70 -> 40)

                num_in_col = 0
                last_frame_y_start = 0
                for r in range(rows):
                    idx = c * rows + r
                    if idx >= len(img_list): break
                    num_in_col += 1
                    curr_y = m_y_t + r * step_y
                    last_frame_y_start = curr_y
                    
                    px = sx + (strip_w - photo_w)//2
                    self._paste_photo(canvas, img_list[idx], px, curr_y, photo_w, photo_h, rotate=True)
                    
                    # 右侧标识（保持）
                    r_mid_x = sx + strip_w - (strip_w - photo_w) // 4
                    num_layer = self.create_rotated_text(str(idx + 1), 90, color=cur_color)
                    canvas.paste(tri_l, (int(r_mid_x - tri_l.width//2), int(curr_y + photo_h//2 - 105)), tri_l)
                    canvas.paste(num_layer, (int(r_mid_x - num_layer.width//2), int(curr_y + photo_h//2 + 25)), num_layer)
                    
                    # --- 问题 1 修正：EXIF 距离照片更近 ---
                    # EN: Move EXIF closer to the photo bottom
                    # CN: 让 EXIF 紧贴照片底边。不再使用 black_area_center，改为固定偏移
                    data = meta_handler.get_data(img_list[idx])
                    dt = data.get("DateTime", "")
                    date_str = dt[2:10].replace(":", "/") if len(dt) >= 10 else "00/00/00"
                    f_val = str(data.get("FocalLength", "---")).lower()
                    exif_str = f"f/{data.get('FNumber', '--')}  {data.get('ExposureTimeStr', '--')}s  {f_val}"
                    
                    # 设定 EXIF 第一行离照片底部的距离 (例如 60 像素)
                    # EN: Base offset from photo bottom
                    exif_y_start = curr_y + photo_h + 70 
                    
                    tw_date = draw.textlength(date_str, font=self.seg_font)
                    draw.text((px + photo_w//2 - tw_date//2, exif_y_start), date_str, font=self.seg_font, fill=cur_color)
                    
                    tw_exif = draw.textlength(exif_str, font=self.seg_font)
                    # 第二行紧跟第一行，间距 50 像素
                    draw.text((px + photo_w//2 - tw_exif//2, exif_y_start + 50), exif_str, font=self.seg_font, fill=cur_color)

                # D. 裁切 (保持步进逻辑)
                if num_in_col > 0:
                    crop_line_y = last_frame_y_start + step_y
                    draw.rectangle([sx, crop_line_y, sx + strip_w, c_h], fill=bg_color)

        else:
            # --- 645_P: 水平底片条 (修正：右侧黑边宽度 = 照片间隙) ---
            strip_h = (c_h - m_y_t - final_cfg['margin_y_bottom'] - (rows-1)*rg) // rows
            photo_w = int(strip_h / STRIP_RATIO)
            photo_h = int(photo_w * PHOTO_ASPECT)
            col_pitch = (c_w - 2 * m_x) // cols
            
            tri_p = self.create_stretched_triangle(color=cur_color).resize((int(15 * 3.5), 15))

            for r in range(rows):
                sy = m_y_t + r * (strip_h + rg)
                # 1. 铺设连续黑条
                draw.rectangle([m_x, sy, c_w, sy + strip_h], fill=(12, 12, 12))
                
                last_photo_right_x = 0
                for c in range(cols):
                    idx = r * cols + c
                    if idx >= len(img_list): break
                    
                    cell_center_x = m_x + c * col_pitch + col_pitch // 2
                    curr_x = cell_center_x - photo_w // 2 
                    py = sy + (strip_h - photo_h) // 2
                    last_photo_right_x = curr_x + photo_w # 记录真实物理边缘
                    
                    # A. 粘贴照片
                    self._paste_photo(canvas, img_list[idx], curr_x, py, photo_w, photo_h, rotate=False)
                    
                    # B. 上侧信息：水平喷码
                    draw.text((curr_x, sy + 10), raw_text, font=self.led_font, fill=cur_color)
                    
                    # C. 下侧信息：序号与三角 (在底部黑边垂直水平双居中)
                    num_str = str(idx + 1)
                    # 获取文字 bbox 以获得精确高度
                    n_l, n_t, n_r, n_b = self.font.getbbox(num_str)
                    num_h = n_b - n_t
                    num_tw = draw.textlength(num_str, font=self.font)
                    asset_total_w = tri_p.width + 100 + num_tw
                    
                    # 水平居中锚点
                    ax_start = cell_center_x - asset_total_w // 2
                    
                    # 垂直居中核心逻辑
                    b_top, b_bottom = py + photo_h, sy + strip_h
                    black_area_center_y = b_top + (b_bottom - b_top) // 2

                    # ---------------------------------------------------------
                    # 核心微调区 (Core Fine-tuning)
                    # ---------------------------------------------------------
                    # 1. 序号 Y 坐标：文字重心微调
                    # 如果序号偏上，增大 +10；如果偏下，减小它
                    ay = black_area_center_y - (num_h // 2) - 5

                    # 2. 三角 Y 坐标：独立对齐文字
                    # tri_p_y = ay + 偏移。如果三角比文字靠上，增大 +5
                    tri_p_y = ay + 10 
                    # ---------------------------------------------------------

                    # 执行绘制
                    canvas.paste(tri_p, (int(ax_start), int(tri_p_y)), tri_p)
                    draw.text((int(ax_start + tri_p.width + 50), int(ay)), num_str, font=self.font, fill=cur_color)

                    # D. 右侧信息：双行 EXIF (旋转 90)
                    data = meta_handler.get_data(img_list[idx])
                    dt = data.get("DateTime", "")
                    date_str = dt[2:10].replace(":", "/") if len(dt) >= 10 else "00/00/00"
                    
                    # 关键物理逻辑：右侧黑边的中轴线
                    right_margin_center_x = curr_x + photo_w + (col_pitch - photo_w) // 3
                    
                    date_layer = self.create_rotated_seg_text(date_str, 90, cur_color)
                    canvas.paste(date_layer, (int(right_margin_center_x - 45), int(py + photo_h // 2 - date_layer.height // 2)), date_layer)

                    f_val = str(data.get("FocalLength", "---")).lower()
                    exif_str = f"f/{data.get('FNumber', '--')}  {data.get('ExposureTimeStr', '--')}s  {f_val}"
                    exif_layer = self.create_rotated_seg_text(exif_str, 90, cur_color)
                    canvas.paste(exif_layer, (int(right_margin_center_x + 5), int(py + photo_h // 2 - exif_layer.height // 2)), exif_layer)

                # --- 2. 精准裁切 (校正) ---
                # EN: Inter-photo gap = col_pitch - photo_w
                # CN: 照片之间的视觉间隙宽度是 col_pitch - photo_w
                # CN: 裁切起点 = 照片右边缘 + 完整的间隙宽度
                if last_photo_right_x > 0:
                    gap_w = col_pitch - photo_w
                    crop_line_x = last_photo_right_x + gap_w
                    if crop_line_x < c_w:
                        draw.rectangle([crop_line_x, sy, c_w, sy + strip_h], fill=bg_color)

        return canvas

    def _paste_photo(self, canvas, path, x, y, w, h, rotate=False):
        with Image.open(path) as img:
            if rotate and img.height > img.width: img = img.rotate(90, expand=True)
            if not rotate and img.width > img.height: img = img.rotate(90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))