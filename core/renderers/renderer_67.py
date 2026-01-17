# core/renderers/renderer_67.py
import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer67(BaseFilmRenderer):
    """
    EN: 6x7 Renderer (645-step edge markings & left-aligned jitter)
    CN: 6x7 画幅渲染器 (645 物理喷码步进 + 左对齐随机抖动版)
    """
    
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None):
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
        
        # 2. [精准注入] 获取全卷统一信息
        if not sample_data:
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
        for r in range(3):  # 硬编码为3行，符合6x7物理布局
            # 根据6x7物理布局特点：前两行4个，第三行2个
            if r < 2:  # 前两行：4列
                row_cols = 4
            else:  # 第三行：2列
                row_cols = 2
                
            sy = m_y_t + r * (strip_h + rg)
            
            # [物理规范] 左侧起始黑边
            if r < 2:  # 前两行：完整的黑边
                leader_start_x = m_x - side_margin
                draw.rectangle([leader_start_x, sy, c_w, sy + strip_h], fill=(12, 12, 12))
            else:  # 第三行：只覆盖2个位置的黑边
                # 计算第三行2个位置的总宽度
                third_row_width = 2 * col_pitch
                leader_start_x = m_x - side_margin
                draw.rectangle([leader_start_x, sy, m_x + third_row_width, sy + strip_h], fill=(12, 12, 12))
            
            # --- 喷码逻辑攻坚 (模拟 120 原厂连喷) ---
            # CN: 在黑条起始位置加一个 0~side_margin 之间的随机抖动，但不超出左边界
            # EN: Add jitter at the start of the strip, confined within the leader area
            current_marking_x = leader_start_x + random.randint(5, side_margin)
            
            # 第三行的喷码只在有效的区域内
            marking_limit = m_x + 2 * col_pitch - 200 if r == 2 else c_w - 200
            while current_marking_x < marking_limit:
                # CN: 喷码置于上黑边中心 / EN: Place marking in top margin center
                draw.text((current_marking_x, sy + (side_margin // 2) - 15), 
                        raw_text, font=self.led_font, fill=cur_color)
                # CN: 按 645 物理步进，并加入微小随机不稳定性
                current_marking_x += marking_step + random.randint(-20, 20)

            for c in range(row_cols):
                if r < 2:  # 前两行
                    idx = r * 4 + c
                    curr_x = m_x + c * col_pitch + 20
                else:  # 第三行，只使用前2个位置
                    idx = 8 + c  # 第三行从第9张开始编号（索引8）
                    curr_x = m_x + c * col_pitch + 20  # 使用相同布局，但只使用前2个

                py = sy + side_margin 
                
                # 总是绘制序号，即使没有照片
                num_str = str(idx + 1)
                num_tw = draw.textlength(num_str, font=self.font)
                ax_start = (curr_x + photo_w // 2) - (tri_p.width + 50 + num_tw) // 2
                ay = py + photo_h + 5 
                draw.text((int(ax_start + tri_p.width + 50), int(ay)), num_str, font=self.font, fill=cur_color)
                
                # 如果有对应的照片，则绘制照片和相关信息
                if idx < len(img_list):
                    # A. 粘贴照片 (EN: Force Landscape / CN: 强制横向)
                    self._paste_photo(canvas, img_list[idx], curr_x, py, photo_w, photo_h, force_landscape=True)
                    
                    # B. 下侧序号三角 (CN: 物理中心对齐 / EN: Physical alignment)
                    canvas.paste(tri_p, (int(ax_start), int(ay + 5)), tri_p)
                    draw.text((int(ax_start + tri_p.width + 50), int(ay)), num_str, font=self.font, fill=cur_color)

                    # C. 右侧 EXIF (150px 压缩空间)
                    data = meta_handler.get_data(img_list[idx])
                    date_str, exif_str = self.get_clean_exif(data)
                        
                    # 关键物理逻辑：右侧黑边的中轴线
                    right_margin_center_x = curr_x + photo_w + (col_pitch - photo_w) // 2
                    if date_str and str(date_str).strip().upper() != "NONE":
                        date_layer = self.create_rotated_seg_text(date_str, 90, cur_color)
                        canvas.paste(date_layer, (int(right_margin_center_x - 45), int(py + photo_h // 2 - date_layer.height // 2)), date_layer)

                    if exif_str and str(exif_str).strip().upper() != "NONE":
                        exif_layer = self.create_rotated_seg_text(exif_str, 90, cur_color)
                        canvas.paste(exif_layer, (int(right_margin_center_x + 5), int(py + photo_h // 2 - exif_layer.height // 2)), exif_layer)

        # --- 固定右侧裁切 ---
        # 按照6x7物理布局进行固定裁切：前两行每行4个，第三行前2个位置
        crop_line_x = m_x + 4 * col_pitch  # 固定裁切到4个位置的宽度（按前两行的标准）
        
        if crop_line_x < c_w:
            draw.rectangle([crop_line_x, 0, c_w, c_h], fill=bg_color)

        return canvas

    def _paste_photo(self, canvas, path, x, y, w, h, force_landscape=False):
        with Image.open(path) as img:
            img_w, img_h = img.size
            if force_landscape and img_h > img_w: img = img.rotate(-90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))