# core/renderers/renderer_645.py
import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer645(BaseFilmRenderer):
    """
    EN: 645 Renderer. Strictly uses Base methods; forced full-gap tailing margins.
    CN: 中英双语：645 渲染器。彻底复用 Base 方法，强制末端黑边为完整间距 (rg/cg)。
    """
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion):
        print("\nCN: [645 排版方案选择]")
        print("1. 横排 (Landscape / _L): 垂直底片条")
        print("2. 竖排 (Portrait / _P): 水平底片条")
        choice = input(">>> 请输入数字 (默认 1): ").strip()
        
        suffix = "L" if choice != "2" else "P"
        final_cfg = meta_handler.get_contact_layout(f"645_{suffix}")
        mode = final_cfg.get("orientation", "landscape")
        
        # 物理画布重塑逻辑
        if (mode == "landscape" and canvas.height > canvas.width) or \
           (mode == "portrait" and canvas.width > canvas.height):
            canvas = Image.new("RGB", (final_cfg['canvas_w'], final_cfg['canvas_h']), (235, 235, 235))

        draw = ImageDraw.Draw(canvas)
        c_w, c_h = canvas.size
        m_x, m_y_t = final_cfg['margin_x'], final_cfg['margin_y_top']
        cg, rg = final_cfg['col_gap'], final_cfg['row_gap']
        cols, rows = final_cfg['cols'], final_cfg['rows']
        
        STRIP_RATIO = 61.5 / 41.5  
        PHOTO_ASPECT = 56.0 / 41.5 
        
        sample_data = meta_handler.get_data(img_list[0])
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        # [Base调用] 获取喷码字符串
        raw_text = self.get_marking_str(sample_data, user_emulsion)

        if mode == "landscape":
            # --- 645_L: 垂直底片条 ---
            area_w = (c_w - 2 * m_x - (cols-1) * cg) // cols
            side_h = min(int(area_w / STRIP_RATIO), (c_h - m_y_t - final_cfg['margin_y_bottom'] - 160 - rows*rg) // rows)
            side_w = int(side_h * PHOTO_ASPECT)
            ss_w = int(side_h * STRIP_RATIO)
            
            # CN: 底部黑边 = 完整 rg / EN: Bottom margin = full rg
            film_start_y = m_y_t - 80
            film_end_y = m_y_t + (rows - 1) * (side_h + rg) + side_h + rg
            
            # [Base调用] 生成旋转喷码图层
            edge_layer = self.create_rotated_text(raw_text, angle=90, color=cur_color)

            for c in range(cols):
                cx = m_x + (area_w // 2) + c * (area_w + cg)
                draw.rectangle([cx - ss_w//2, film_start_y, cx + ss_w//2, film_end_y], fill=(12,12,12))
                # 绘制垂直喷码
                self._draw_codes_v(canvas, cx - ss_w//2 + 10, m_y_t - 50, side_h, rows, rg, edge_layer)
                
                for r in range(rows):
                    idx = c * rows + r
                    if idx >= len(img_list): break
                    cy = m_y_t + r * (side_h + rg)
                    self._paste_and_num_l(canvas, img_list[idx], cx, cy, side_w, side_h, ss_w, cur_color, idx+1)
        
        else:
            # --- 645_P: 水平底片条 ---
            ss_h = (c_h - m_y_t - final_cfg['margin_y_bottom'] - (rows-1)*rg) // rows
            s_w = int(ss_h / STRIP_RATIO)
            s_h = int(s_w * PHOTO_ASPECT)
            
            col_pitch = (c_w - 2 * m_x) // cols
            left_edge = 25 
            # CN: 右侧黑边 = 完整 cg / EN: Right margin = full cg
            total_strip_w = (cols * col_pitch)
            start_x = (c_w - total_strip_w) // 2

            # [Base调用] 3.5倍物理拉伸三角 (尖端向右)
            tri_raw = self.create_stretched_triangle(color=cur_color)
            tri_p = tri_raw.resize((int(tri_raw.width * 3.5), tri_raw.height), Image.Resampling.LANCZOS)

            for r in range(rows):
                cy_center = m_y_t + (ss_h // 2) + r * (ss_h + rg)
                draw.rectangle([start_x, cy_center - ss_h//2, start_x + total_strip_w, cy_center + ss_h//2], fill=(12, 12, 12))
                
                for c in range(cols):
                    idx = r * cols + c
                    if idx >= len(img_list): break
                    px = start_x + c * col_pitch + left_edge
                    py = cy_center - s_h // 2
                    
                    draw.text((px, cy_center - ss_h//2 + 10), raw_text, font=self.font, fill=cur_color)
                    self._paste_photo_p(canvas, img_list[idx], px, py, s_w, s_h)
                    
                    # 序号居中绘制
                    num_str = str(idx + 1)
                    tw = draw.textlength(num_str, font=self.font)
                    nx = px + s_w // 2 - tw // 2
                    ny = cy_center + s_h // 2 + 10
                    draw.text((nx, ny), num_str, font=self.font, fill=cur_color)
                    
                    # 粘贴三角 (序号左侧)
                    tx, ty = nx - tri_p.width - 20, ny + (self.font.size // 2) - (tri_p.height // 2)
                    canvas.paste(tri_p, (int(tx), int(ty)), tri_p)

        return canvas

    def _draw_codes_v(self, canvas, x, y_start, step, rows, rg, layer):
        """CN: 垂直喷码绘制逻辑"""
        curr_y = y_start
        for _ in range(rows):
            canvas.paste(layer, (int(x), int(curr_y + random.randint(10, 50))), layer)
            curr_y += (step + rg)

    def _paste_photo_p(self, canvas, path, x, y, sw, sh):
        """CN: P模式照片旋转逻辑"""
        with Image.open(path) as img:
            if img.width > img.height: img = img.rotate(90, expand=True)
            img = img.resize((sw, sh), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))

    def _paste_and_num_l(self, canvas, path, cx, cy, sw, sh, ss, color, num):
        """CN: L模式专用，利用基类工具实现旋转资产粘贴"""
        with Image.open(path) as img:
            if img.height > img.width: img = img.rotate(90, expand=True)
            img = img.resize((sw, sh), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(cx - sw // 2), int(cy)))
        
        r_mid_x = cx + ss // 2 - (ss - sw) // 4
        # [Base调用] 3.5x三角 + 旋转 (尖端向下)
        tri_raw = self.create_stretched_triangle(color=color)
        tri_l = tri_raw.resize((int(tri_raw.width * 3.5), tri_raw.height), Image.Resampling.LANCZOS).rotate(-90, expand=True)
        canvas.paste(tri_l, (int(r_mid_x - tri_l.width//2), int(cy + sh//2 - 105)), tri_l)
        
        # [Base调用] 旋转文字图层
        num_layer = self.create_rotated_text(str(num), 90, color=color)
        canvas.paste(num_layer, (int(r_mid_x - num_layer.width//2), int(cy + sh//2 + 25)), num_layer)