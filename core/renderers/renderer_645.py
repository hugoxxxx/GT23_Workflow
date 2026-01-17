# core/renderers/renderer_645.py
# EN: Renderer for 645 film format (landscape and portrait modes)
# CN: 645 胶片渲染器 (横纵向模式)

import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer645(BaseFilmRenderer):
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None):
        # EN: Execute 645 rendering | CN: 执行 645 渲染
        print("EN: [645 2.0] Executing render ... | CN: [645 2.0] 执行渲染 ...")
        
        # EN: 1. Re-select mode and reset canvas size
        # CN: 1. 重新选择模式并重置画布尺寸
        choice = input("\nEN: 1. Vertical strip (L) - horizontal photo  2. Horizontal strip (P) - vertical photo [Default 1]\nCN: 1.垂直条(L)照片横向 2.水平条(P)照片竖向 [默认 1]: ").strip()
        suffix = "L" if choice != "2" else "P"
        final_cfg = meta_handler.get_contact_layout(f"645_{suffix}")
        
        # EN: Key step! Regenerate canvas based on JSON-defined dimensions for correct PL mode aspect ratio
        # CN: 关键步骤！根据 json 定义的宽高重新生成画布，确保 PL 模式长宽正确
        new_w, new_h = final_cfg['canvas_w'], final_cfg['canvas_h']
        canvas = canvas.resize((new_w, new_h))  # EN: Force stretch or reset / CN: 强制拉伸或重置
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235))  # EN: Fill background color / CN: 刷上背景色
        
        c_w, c_h = new_w, new_h
        bg_color = (235, 235, 235)
        mode = final_cfg.get("orientation", "landscape")

        m_x, m_y_t = final_cfg['margin_x'], final_cfg['margin_y_top']
        cg, rg = final_cfg['col_gap'], final_cfg['row_gap']
        cols, rows = final_cfg['cols'], final_cfg['rows']
        
        # EN: Aspect ratio constants for 645 format
        # CN: 645 画幅的宽高比常数
        STRIP_RATIO = 61.5 / 41.5 
        PHOTO_ASPECT = 56.0 / 41.5 
        
        # EN: Get sample data from first image if not provided
        # CN: 如果未提供，从第一张图片获取样本数据
        if not sample_data:
            sample_data = meta_handler.get_data(img_list[0])
            
        # EN: Extract contact sheet color and marking text for this film roll
        # CN: 提取接触纸颜色和喷码文本 (这一卷胶片的喷码名)
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        raw_text = self.get_marking_str(sample_data, user_emulsion)

        if mode == "landscape":
            # EN: --- 645_L: Vertical film strip logic with correction ---
            # CN: --- 645_L: 垂直底片条逻辑修正 ---
            area_w = (c_w - 2 * m_x - (cols-1) * cg) // cols
            # EN: Vertical step increment
            # CN: 垂直步进
            step_y = (c_h - m_y_t - final_cfg.get('margin_y_bottom', 350) - (rows * rg)) // rows + rg
            
            # EN: 645 aspect ratio calibration - reduce photo size slightly for bottom breathing room
            # CN: 645 比例校准：适当减小照片比例，为底部留出呼吸感
            photo_h = int((step_y - rg) * 0.9) 
            photo_w = int(photo_h * PHOTO_ASPECT)
            strip_w = int(photo_h * STRIP_RATIO)
            
            edge_layer = self.create_rotated_text(raw_text, angle=90, color=cur_color)
            tri_l = self.create_stretched_triangle(color=cur_color).resize((int(15 * 3.5), 15)).rotate(-90, expand=True)

            for c in range(cols):
                sx = m_x + c * (area_w + cg) + (area_w - strip_w) // 2
                draw.rectangle([sx, m_y_t - 80, sx + strip_w, c_h], fill=(12, 12, 12))
                
                # EN: --- 1. Marking logic: Align to top with jitter limited to downward only ---
                # CN: --- 1. 喷码逻辑：对齐靠上 + 限制抖动向上越界 ---
                # EN: Edge markings: Start position aligned to top, jitter range (0, +100) to prevent upward overflow
                # CN: 喷码逻辑：起始对齐靠上，抖动仅向下延伸，防止超出底片上边缘
                
                marking_step_y = c_h // 4  # EN: Fixed 4 positions / CN: 固定 4 个
                # EN: Start point slightly below edge, jitter (0, +100) to ensure no upward overflow
                # CN: 起始点设在边缘稍下方，jitter 范围设为 (0, +100)，确保不往上跑
                marking_y = (m_y_t - 80) + random.randint(0, 100) 
                
                left_margin_w = (strip_w - photo_w) // 2
                while marking_y < c_h - 100:
                    lx = sx + (left_margin_w // 2) - (edge_layer.width // 2)
                    canvas.paste(edge_layer, (int(lx), int(marking_y)), edge_layer)
                    # EN: Step increment plus random downward jitter
                    # CN: 步进加随机向下抖动
                    marking_y += marking_step_y + random.randint(0, 50)

                # EN: --- EXIF distance correction (synchronized to be closer to photo) ---
                # CN: --- EXIF 距离修正 (同步贴近照片) ---

                for r in range(rows):
                    idx = c * rows + r
                    curr_y = m_y_t + r * step_y
                    
                    # EN: Always draw frame number and triangle, even without photo
                    # CN: 总是绘制序号和三角形，即使没有照片
                    r_mid_x = sx + strip_w - (strip_w - photo_w) // 4
                    canvas.paste(tri_l, (int(r_mid_x - tri_l.width//2), int(curr_y + photo_h//2 - 105)), tri_l)
                    num_layer = self.create_rotated_text(str(idx + 1), 90, color=cur_color)
                    canvas.paste(num_layer, (int(r_mid_x - num_layer.width//2), int(curr_y + photo_h//2)), num_layer)

                    # EN: If photo exists, render it and related information
                    # CN: 如果有对应的照片，则绘制照片和相关信息
                    if idx < len(img_list):
                        px = sx + (strip_w - photo_w)//2
                        self._paste_photo(canvas, img_list[idx], px, curr_y, photo_w, photo_h, rotate=True)
                        
                        # EN: --- Issue 1 correction: Move EXIF closer to photo bottom ---
                        # CN: --- 问题 1 修正：EXIF 距离照片更近 ---
                        # EN: Move EXIF closer to the photo bottom
                        # CN: 让 EXIF 紧贴照片底边。不再使用 black_area_center，改为固定偏移
                        data = meta_handler.get_data(img_list[idx])
                        date_str, exif_str = self.get_clean_exif(data)
                        
                        # EN: Base offset from photo bottom (e.g., 60 pixels)
                        # CN: 设定 EXIF 第一行离照片底部的距离 (例如 60 像素)
                        exif_y_start = curr_y + photo_h + 70 
                        
                        # EN: Draw date string if available
                        # CN: 如果可用，绘制日期字符串
                        if date_str and str(date_str).strip().upper() != "NONE":
                            tw_date = draw.textlength(date_str, font=self.seg_font)
                            draw.text((px + photo_w//2 - tw_date//2, exif_y_start), date_str, font=self.seg_font, fill=cur_color)
                        
                        # EN: Draw EXIF info string if available
                        # CN: 如果可用，绘制 EXIF 信息字符串
                        if exif_str and str(exif_str).strip().upper() != "NONE":
                            tw_exif = draw.textlength(exif_str, font=self.seg_font)
                            # EN: Second line follows first with 50-pixel spacing
                            # CN: 第二行紧跟第一行，间距 50 像素
                            draw.text((px + photo_w//2 - tw_exif//2, exif_y_start + 50), exif_str, font=self.seg_font, fill=cur_color)

                # EN: D. Fixed crop after last preset row
                # CN: D. 固定裁切到最后一个预设行之后
                crop_line_y = m_y_t + rows * step_y
                draw.rectangle([sx, crop_line_y, sx + strip_w, c_h], fill=bg_color)

        else:  # EN: Portrait mode / CN: 纵向模式
            # EN: --- 645_P: Horizontal film strip (correction: right black margin width = photo gap) ---
            # CN: --- 645_P: 水平底片条 (修正：右侧黑边宽度 = 照片间隙) ---
            strip_h = (c_h - m_y_t - final_cfg['margin_y_bottom'] - (rows-1)*rg) // rows
            photo_w = int(strip_h / STRIP_RATIO)
            photo_h = int(photo_w * PHOTO_ASPECT)
            col_pitch = (c_w - 2 * m_x) // cols
            
            tri_p = self.create_stretched_triangle(color=cur_color).resize((int(15 * 3.5), 15))

            for r in range(rows):
                sy = m_y_t + r * (strip_h + rg)
                # EN: 1. Lay out continuous black strip
                # CN: 1. 铺设连续黑条
                draw.rectangle([m_x, sy, c_w, sy + strip_h], fill=(12, 12, 12))
                
                for c in range(cols):
                    idx = r * cols + c
                    cell_center_x = m_x + c * col_pitch + col_pitch // 2
                    curr_x = cell_center_x - photo_w // 2 
                    py = sy + (strip_h - photo_h) // 2
                    
                    # EN: Always draw frame number, even without photo
                    # CN: 总是绘制序号，即使没有照片
                    num_str = str(idx + 1)
                    # EN: Get text bbox for precise height
                    # CN: 获取文字 bbox 以获得精确高度
                    n_l, n_t, n_r, n_b = self.font.getbbox(num_str)
                    num_h = n_b - n_t
                    num_tw = draw.textlength(num_str, font=self.font)
                    asset_total_w = tri_p.width + 100 + num_tw
                    
                    # EN: Horizontal center anchor point
                    # CN: 水平居中锚点
                    ax_start = cell_center_x - asset_total_w // 2
                    
                    # EN: Vertical center logic for black area
                    # CN: 垂直居中核心逻辑
                    b_top, b_bottom = py + photo_h, sy + strip_h
                    black_area_center_y = b_top + (b_bottom - b_top) // 2

                    # EN: ---------------------------------------------------------
                    # EN: Core Fine-tuning Area
                    # EN: ---------------------------------------------------------
                    # EN: 1. Frame number Y coordinate: Fine-tune text center
                    # EN: If number appears too high, increase +10; if too low, decrease it
                    # CN: 1. 序号 Y 坐标：文字重心微调
                    # CN: 如果序号偏上，增大 +10；如果偏下，减小它
                    ay = black_area_center_y - (num_h // 2) - 5

                    # EN: 2. Triangle Y coordinate: Independent text alignment
                    # EN: If triangle appears higher than text, increase +5
                    # CN: 2. 三角 Y 坐标：独立对齐文字
                    # CN: tri_p_y = ay + 偏移。如果三角比文字靠上，增大 +5
                    tri_p_y = ay + 10 
                    # EN: ---------------------------------------------------------
                    # CN: ---------------------------------------------------------

                    # EN: Draw triangle and frame number (even without photo)
                    # CN: 绘制三角形和序号（即使没有照片）
                    canvas.paste(tri_p, (int(ax_start), int(tri_p_y)), tri_p)
                    draw.text((int(ax_start + tri_p.width + 50), int(ay)), num_str, font=self.font, fill=cur_color)
                    
                    # EN: Top info: Horizontal marking (always display)
                    # CN: 上侧信息：水平喷码（始终显示）
                    draw.text((curr_x, sy + 10), raw_text, font=self.led_font, fill=cur_color)
                    
                    # EN: If photo exists, render it and related information
                    # CN: 如果有对应的照片，则绘制照片和相关信息
                    if idx < len(img_list):
                        # EN: A. Paste photo
                        # CN: A. 粘贴照片
                        self._paste_photo(canvas, img_list[idx], curr_x, py, photo_w, photo_h, rotate=False)

                        # EN: B. Right side info: Two-line EXIF (rotated 90 degrees)
                        # CN: B. 右侧信息：双行 EXIF (旋转 90)
                        data = meta_handler.get_data(img_list[idx])
                        date_str, exif_str = self.get_clean_exif(data)
                        
                        # EN: Key physical logic: Center line of right-side black margin
                        # CN: 关键物理逻辑：右侧黑边的中轴线
                        right_margin_center_x = curr_x + photo_w + (col_pitch - photo_w) // 3
                        # EN: Draw date if available
                        # CN: 如果可用，绘制日期
                        if date_str and str(date_str).strip().upper() != "NONE":
                            date_layer = self.create_rotated_seg_text(date_str, 90, cur_color)
                            canvas.paste(date_layer, (int(right_margin_center_x - 45), int(py + photo_h // 2 - date_layer.height // 2)), date_layer)

                        # EN: Draw EXIF if available
                        # CN: 如果可用，绘制 EXIF
                        if exif_str and str(exif_str).strip().upper() != "NONE":
                            exif_layer = self.create_rotated_seg_text(exif_str, 90, cur_color)
                            canvas.paste(exif_layer, (int(right_margin_center_x + 5), int(py + photo_h // 2 - exif_layer.height // 2)), exif_layer)

            # EN: --- 2. Unified right area fixed crop (similar to L mode) ---
            # CN: --- 2. 统一右侧区域固定裁切 (类似L模式) ---
            # EN: Right margin should equal the gap between photos (col_pitch - photo_w)
            # CN: 右侧黑边应该等于照片间隙（col_pitch - photo_w）
            # EN: Last photo right edge + full gap width
            # CN: 最后照片右边缘 + 完整间隙宽度
            last_photo_right = m_x + (cols - 1) * col_pitch + (col_pitch + photo_w) // 2
            gap_width = col_pitch - photo_w
            crop_line_x = last_photo_right + gap_width
            if crop_line_x < c_w:
                draw.rectangle([crop_line_x, 0, c_w, c_h], fill=bg_color)

        return canvas

    def _paste_photo(self, canvas, path, x, y, w, h, rotate=False):
        # EN: Helper method to paste and resize photo with optional rotation
        # CN: 辅助方法：粘贴并调整照片大小，支持可选旋转
        with Image.open(path) as img:
            if rotate and img.height > img.width: img = img.rotate(90, expand=True)
            if not rotate and img.width > img.height: img = img.rotate(90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))