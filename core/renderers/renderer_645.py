import random
from PIL import Image, ImageDraw
from .base_renderer import BaseFilmRenderer

class Renderer645(BaseFilmRenderer):
    """
    EN: 645 Renderer. P-mode: Solves left margin, overflow, and number centering via strict physics.
    CN: 中英双语：645 渲染器。P 模式：严格遵循先计算后渲染，解决左边宽、右溢出、序号居中问题。
    """
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion):
        print("\nCN: [645 排版方案] 请选择:")
        print("1. 横排 (Landscape / _L): 垂直底片条 (保持满意效果)")
        print("2. 竖排 (Portrait / _P): 水平底片条 (物理复刻版)")
        choice = input(">>> 请输入数字 (默认 1): ").strip()
        
        suffix = "L" if choice != "2" else "P"
        cfg['output_suffix'] = suffix 
        
        final_cfg = meta_handler.get_contact_layout(f"645_{suffix}")
        mode = final_cfg.get("orientation", "landscape")
        
        # 物理画布重塑
        if (mode == "landscape" and canvas.height > canvas.width) or \
           (mode == "portrait" and canvas.width > canvas.height):
            canvas = Image.new("RGB", (final_cfg['canvas_w'], final_cfg['canvas_h']), (255, 255, 255))

        draw = ImageDraw.Draw(canvas)
        c_w, c_h = canvas.size
        m_x, m_y_t = final_cfg['margin_x'], final_cfg['margin_y_top']
        cg, rg = final_cfg['col_gap'], final_cfg['row_gap']
        cols, rows = final_cfg['cols'], final_cfg['rows']
        
        # --- 物理常数 ---
        STRIP_RATIO = 61.5 / 41.5  # 胶片厚度比 1.48
        PHOTO_ASPECT = 56.0 / 41.5 # 1.35
        
        sample_data = meta_handler.get_data(img_list[0])
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        film_brand = sample_data.get("FilmModel", "KODAK")
        font_obj = getattr(self, 'font', None)

        if mode == "landscape":
            # --- 645_L: 原有逻辑完全不动 ---
            area_w = (c_w - 2 * m_x - (cols-1) * cg) // cols
            side_h = min(int(area_w / STRIP_RATIO), (c_h - m_y_t - final_cfg['margin_y_bottom'] - 80 - rows*rg) // rows)
            side_w = int(side_h * PHOTO_ASPECT)
            ss = int(side_h * STRIP_RATIO)
            for c in range(cols):
                cx = m_x + (area_w // 2) + c * (area_w + cg)
                draw.rectangle([cx - ss//2, m_y_t - 80, cx + ss//2, m_y_t + (rows-1)*(side_h+rg) + side_h + 80], fill=(12,12,12))
                code_layer = self.create_rotated_text(f"{user_emulsion}  {film_brand} SAFETY FILM", 90, color=cur_color)
                self._draw_codes_v(canvas, cx - ss//2 + 8, m_y_t - 50, side_h, rows, rg, code_layer)
            for i, path in enumerate(img_list[:cols*rows]):
                c, r = i // rows, i % rows
                cx, cy = m_x + (area_w // 2) + c * (area_w + cg), m_y_t + r * (side_h + rg)
                self._paste_and_num_l(canvas, path, cx, cy, side_w, side_h, ss, cur_color, i+1)
        
        else:
            # --- 645_P: 精确物理推算 ---
            # 1. 计算高度步进
            ss_h = (c_h - m_y_t - final_cfg['margin_y_bottom'] - (rows-1)*rg) // rows
            # 2. 锁定照片物理尺寸
            sw = int(ss_h / STRIP_RATIO)
            sh = int(sw * PHOTO_ASPECT)
            # 3. 锁定水平间距
            left_edge = 25 # 解决“头部太宽”
            # 计算单列列宽：col_pitch (包含 cg)
            col_pitch = (c_w - 2 * m_x) // cols
            # 4. 整体水平居中计算
            total_strip_w = (cols * col_pitch) - cg
            start_x = (c_w - total_strip_w) // 2

            # --- 渲染阶段 ---
            for r in range(rows):
                cy_center = m_y_t + (ss_h // 2) + r * (ss_h + rg)
                
                # 绘制底片条 (物理截断，防止右溢)
                draw.rectangle([start_x, cy_center - ss_h//2, start_x + total_strip_w, cy_center + ss_h//2], fill=(12, 12, 12))
                
                for c in range(cols):
                    idx = r * cols + c
                    if idx >= len(img_list): break
                    
                    # 每一个物理单元的左起坐标
                    cell_x = start_x + c * col_pitch
                    # 照片起始坐标 (cell_x + 窄左边)
                    px = cell_x + left_edge
                    py = cy_center - sh // 2
                    
                    # A. 喷码 (上方黑边)
                    info_txt = f"{user_emulsion}  {film_brand} SAFETY FILM"
                    draw.text((px, cy_center - ss_h//2 + 10), info_txt, font=font_obj, fill=cur_color)
                    
                    # B. 照片粘贴
                    self._paste_photo_p(canvas, img_list[idx], px, py, sw, sh)
                    
                    # C. 序号 (照片下方居中)
                    num_str = str(idx + 1)
                    # 计算文字宽度以实现绝对居中
                    tw = draw.textlength(num_str, font=font_obj) if hasattr(draw, 'textlength') else 15
                    draw.text((px + sw//2 - tw//2, cy_center + sh//2 + 8), num_str, font=font_obj, fill=cur_color)

        return canvas

    def _paste_photo_p(self, canvas, path, x, y, sw, sh):
        with Image.open(path) as img:
            if img.width > img.height: img = img.rotate(90, expand=True)
            img = img.resize((sw, sh), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))

    def _paste_and_num_l(self, canvas, path, cx, cy, sw, sh, ss, color, num):
        with Image.open(path) as img:
            if img.height > img.width: img = img.rotate(90, expand=True)
            img = img.resize((sw, sh), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(cx - sw // 2), int(cy)))
        num_layer = self.create_rotated_text(str(num), 90, color=color)
        nx = cx + ss // 2 - num_layer.width - 12
        canvas.paste(num_layer, (int(nx), int(cy + sh // 2 - num_layer.height // 2)), num_layer)

    def _draw_codes_v(self, canvas, x, y_start, step, rows, rg, layer):
        curr_y = y_start
        for _ in range(rows):
            canvas.paste(layer, (int(x), int(curr_y + random.randint(10, 40))), layer)
            curr_y += (step + rg)