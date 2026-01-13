# core/renderers/renderer_66.py
import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer66(BaseFilmRenderer):
    """
    EN: 6x6 Renderer with randomized but safe edge coding.
    CN: 中英双语：66 渲染器。喷码位置兼顾随机性与边界安全性，确保不溢出照片或画布。
    """
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion):
        print("CN: [Renderer] 正在执行喷码安全随机化渲染...")
        draw = ImageDraw.Draw(canvas)
        
        # --- 1. EN: Load Specs / CN: 1. 加载参数 ---
        FILM_RATIO = 61.5 / 56.0 
        m_x, m_y_t, m_y_b = cfg['margin_x'], cfg['margin_y_top'], cfg['margin_y_bottom']
        c_gap, r_gap = cfg['col_gap'], cfg['row_gap']
        cols, rows = 3, 4 
        c_w, c_h = canvas.size
        
        # --- 2. EN: Pre-calculate / CN: 2. 物理尺寸预计算 ---
        strip_area_w = (c_w - 2 * m_x - (cols - 1) * c_gap) // cols
        # 考虑到喷码宽度，我们需要微调 side_length 的高度约束逻辑
        padding_top = 80
        available_h = c_h - m_y_t - m_y_b - padding_top
        side_by_height = (available_h - (rows * r_gap)) // rows
        side_by_width = int(strip_area_w / FILM_RATIO)
        
        side_length = min(side_by_width, side_by_height)
        strip_w = int(side_length * FILM_RATIO)
        
        # 边界定义
        strip_top = m_y_t - padding_top
        last_photo_bottom = m_y_t + (rows - 1) * (side_length + r_gap) + side_length
        strip_bottom = last_photo_bottom + r_gap 

        # --- 3. EN: Metadata & Coding / CN: 3. 元数据识别与喷码准备 ---
        sample_data = meta_handler.get_data(img_list[0])
        film_brand = sample_data.get("FilmModel", "FUJI")
        edge_name = sample_data.get("EdgeCode", "SAFETY FILM")
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        
        # EN: Create edge code layer / CN: 创建旋转喷码图层
        edge_text = f"{user_emulsion}  {film_brand} {edge_name}"
        edge_layer = self.create_rotated_text(edge_text, 90, color=cur_color)

        # --- 4. EN: Render Strips & Randomized Coding / CN: 4. 绘制黑条与随机喷码 ---
        for c in range(cols):
            cx = m_x + (strip_area_w // 2) + c * (strip_area_w + c_gap)
            sx = cx - (strip_w // 2)
            draw.rectangle([sx, strip_top, sx + strip_w, strip_bottom], fill=(12, 12, 12))
            
            # EN: Randomized logic for edge codes / CN: 随机喷码逻辑
            # EN: Start with a random offset / CN: 初始位置随机偏移
            curr_y = strip_top + random.randint(20, 100)
            
            # EN: Distance between codes remains consistent but has minor jitter
            # CN: 间隔规律基本不变（约 0.8 倍照片高），但加入微小抖动 (+/- 20px)
            base_step = int(side_length * 0.85)
            
            while curr_y < strip_bottom - edge_layer.height - 20:
                # EN: Safety Check: Ensure text doesn't overlap the photo area
                # CN: 安全检查：将喷码严格靠左侧边缘粘贴 (sx + 8)
                # 由于 strip_w > side_length，左侧有 (strip_w - side_length)/2 的空隙
                text_x = int(sx + 6) 
                
                canvas.paste(edge_layer, (text_x, int(curr_y)), edge_layer)
                
                # EN: Move to next position with minor jitter / CN: 步进并加入微调随机量
                curr_y += base_step + random.randint(-30, 30)

        # --- 5. EN: Render Photos / CN: 5. 渲染照片 ---
        for i, path in enumerate(img_list[:12]):
            c, r = i // rows, i % rows
            cx = m_x + (strip_area_w // 2) + c * (strip_area_w + c_gap)
            row_y = m_y_t + r * (side_length + r_gap)
            
            with Image.open(path) as img:
                img = img.resize((side_length, side_length), Image.Resampling.LANCZOS)
                # EN: Horizontal centering / CN: 水平居中（会自动避开左侧喷码区）
                canvas.paste(img, (int(cx - side_length // 2), int(row_y)))

                # EN: Markings (Right side) / CN: 右侧帧号与标识
                tri = self.create_stretched_triangle(color=cur_color)
                num_layer = self.create_rotated_text(str(i + 1), 90, color=cur_color)
                
                # EN: Anchor to the right edge minus padding
                # CN: 锚定在黑条右边缘减去固定边距
                rx = (cx - strip_w // 2) + strip_w - num_layer.width - 10
                canvas.paste(tri, (int(rx), int(row_y + side_length//2 - 70)), tri)
                canvas.paste(num_layer, (int(rx + 2), int(row_y + side_length//2 + 30)), num_layer)