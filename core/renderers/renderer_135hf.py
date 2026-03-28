# core/renderers/renderer_135hf.py
# EN: Renderer for 135 Half-Frame format (18x24mm) - v3.0 (Unified Strip Rotation)
# CN: 135 半格画幅渲染器 (18x24mm) - v3.0 (统一底片条旋转架构)

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

        # 2. EN: Physical Constants (mm) / CN: 物理常数 (mm)
        m_x, m_y_t = final_cfg.get('margin_x', 150), final_cfg.get('margin_y_top', 500)
        usable_w_px = (new_w - 2 * m_x)
        px_per_mm = usable_w_px / 228.0 # EN: Baseline 228mm for parity / CN: 对齐基准 228mm
        
        # 3. EN: Meta Prep / CN: 元数据准备
        standard_data = sample_data if sample_data else meta_handler.get_data(img_list[0])
        film_text = standard_data.get('EdgeCode') or standard_data.get('Film') or user_emulsion or "FILM"
        prefix = f"{user_emulsion.strip()}  " if user_emulsion and user_emulsion.strip() != film_text else ""
        display_name = f"{prefix}{film_text}"
        cur_color = standard_data.get("ContactColor", (245, 130, 35, 210))
        
        # 4. EN: Render into Strips (Rotation Logic)
        # CN: 渲染为底片条 (旋转逻辑核心)
        cols_per_strip = 12
        num_strips = 6
        strip_h_mm, strip_w_mm = 35.0, 228.0
        s_h, s_w = int(strip_h_mm * px_per_mm), int(strip_w_mm * px_per_mm)
        
        # EN: Ensure 72 slots are filled / CN: 确保填充 72 个槽位
        total_slots = cols_per_strip * num_strips
        full_list = img_list + [None] * (total_slots - len(img_list))
        
        for i in range(num_strips):
            chunk = full_list[i * cols_per_strip : (i + 1) * cols_per_strip]
            
            # EN: Render a Horizontal Strip (P-style) / CN: 渲染一个水平底片条 (P式布局)
            strip_img = Image.new('RGBA', (s_w, s_h), (12, 12, 12, 255))
            self._render_single_hf_strip(
                strip_img, chunk, i, cols_per_strip, px_per_mm, 
                display_name, cur_color, meta_handler, show_date, show_exif
            )
            
            # 5. EN: Paste based on Orientation / CN: 根据方向进行粘贴
            if orientation == 'L':
                # EN: L-Mode: Rotate strip 90 deg clockwise and paste vertically
                # CN: L 模式: 顺时针旋转 90 度并垂直粘贴
                rotated_strip = strip_img.rotate(-90, expand=True)
                col_pitch = usable_w_px / num_strips
                # Center-align strips horizontally
                paste_x = m_x + i * col_pitch + (col_pitch - s_h) // 2 # s_h is the new width
                canvas.paste(rotated_strip, (int(paste_x), m_y_t), rotated_strip)
            else:
                # EN: P-Mode: Paste horizontally
                # CN: P 模式: 直接水平粘贴
                row_gap = final_cfg.get('row_gap', 100)
                paste_y = m_y_t + i * (s_h + row_gap)
                canvas.paste(strip_img, (m_x, paste_y), strip_img)

        # 6. EN: Cleanup right edge for P-Mode / CN: P 模式右边缘截断清理
        if orientation != 'L':
            final_cutoff_x = m_x + s_w + int(1.0 * px_per_mm)
            if final_cutoff_x < new_w:
                draw.rectangle([final_cutoff_x, 0, new_w, new_h], fill=(235, 235, 235))

        return canvas

    def _render_single_hf_strip(self, strip_canvas, img_paths, strip_idx, cols, px_per_mm, film_name, color, meta, show_date, show_exif):
        """EN: Renders a single 35mm horizontal strip containing HF frames"""
        draw = ImageDraw.Draw(strip_canvas)
        pw_mm, ph_mm, gap_mm, info_mm = 18.0, 24.0, 1.0, 5.5
        pw, ph = int(pw_mm * px_per_mm), int(ph_mm * px_per_mm)
        gap = int(gap_mm * px_per_mm)
        info_h = int(info_mm * px_per_mm)
        strip_h = int(35.0 * px_per_mm)
        
        em_font = self.led_font.font_variant(size=int(1.3 * px_per_mm))
        date_font = self.into_dot_font.font_variant(size=int(1.2 * px_per_mm))
        exif_font = self.seg_font.font_variant(size=int(1.2 * px_per_mm))

        # EN: Draw High-Precision Sprockets using Parent SVG logic
        # CN: 使用父类 SVG 逻辑绘制高精度齿孔
        self._draw_iso_sprockets_vector(strip_canvas, 0, strip_canvas.width, 0, info_h, strip_h, int(2.0 * px_per_mm), int(2.8 * px_per_mm), px_per_mm, film_name)
        
        for c in range(len(img_paths)):
            # EN: Center frames within the 228mm strip by splitting the extra 1mm gap
            # CN: 通过平分多出的 1mm 间隙，使照片在 228mm 的底片条内居中
            curr_x = gap // 2 + c * (pw + gap)
            py = info_h
            
            # Paste Photo (Crop - don't stretch)
            # CN: 居中裁切 - 不进行缩放拉伸
            if img_paths[c]:
                from PIL import ImageOps
                with Image.open(img_paths[c]) as img:
                    # EN: Force Portrait for the horizontal strip logic (will be rotated later in L-mode)
                    # CN: 在水平条逻辑中强制竖向 (L模式下后续会整体旋转)
                    if img.width > img.height:
                        img = img.rotate(-90, expand=True)
                    
                    # EN: Center Crop to 18:24 / CN: 居中裁切为 18:24
                    img = ImageOps.fit(img, (pw, ph), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    strip_canvas.paste(img, (int(curr_x), py))
            else:
                # EN: Fill empty slot with dark gray / CN: 空槽位填充深灰色
                draw.rectangle([curr_x, py, curr_x + pw, py + ph], fill=(25, 25, 25))
            
            # Numbering (Top)
            if c % 2 == 0:
                num_idx = (strip_idx * (cols // 2)) + (c // 2) + 1
                val_str = str(num_idx)
                tw = draw.textlength(val_str, font=em_font)
                draw.text((curr_x + (pw - tw)//2, int(0.2 * px_per_mm)), val_str, font=em_font, fill=color)
            
            # Branding (Top Periodical)
            if c % 4 == 1:
                bw = draw.textlength(film_name, font=em_font)
                bx = curr_x + (pw - bw)//2
                self._draw_single_glowing_text(strip_canvas, film_name, (bx, int(0.2 * px_per_mm)), em_font, color)
            
            # Data Back (EXIF)
            if img_paths[c]:
                p_data = meta.get_data(img_paths[c])
                self._draw_glowing_data_back(strip_canvas, p_data, curr_x, py, pw, ph, color, date_font, exif_font, px_per_mm, show_date=show_date, show_exif=show_exif)

    def _draw_single_glowing_text(self, canvas, text, pos, font, color):
        draw = ImageDraw.Draw(canvas)
        glow_color = (color[0], color[1], color[2], 75)
        draw.text((pos[0]+1, pos[1]+1), text, font=font, fill=glow_color)
        draw.text(pos, text, font=font, fill=color)
