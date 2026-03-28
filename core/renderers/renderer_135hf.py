# core/renderers/renderer_135hf.py
# EN: Renderer for 135 Half-Frame format (18x24mm) - v1.0
# CN: 135 半格画幅渲染器 (18x24mm) - v1.0

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
        print("EN: [135HF] Rendering Half-Frame Contact Sheet (72 Frames capacity)")
        print("CN: [135HF] 正在渲染半格索引页 (支持 72 张图片)")
        print("="*65)
        
        # 1. EN: Load 135HF configuration / CN: 加载 135HF 配置
        final_cfg = meta_handler.get_contact_layout("135HF")
        new_w, new_h = final_cfg.get('canvas_w', 4800), final_cfg.get('canvas_h', 6000)
        canvas = canvas.resize((new_w, new_h))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235))

        # 2. EN: ISO 1007 Physical Parameters (mm) / CN: ISO 1007 物理参数 (mm)
        # EN: Standard 135 strip = 35mm wide.
        # EN: Half-frame = 18.0mm (W) x 24.0mm (H).
        # EN: 4 perforations pitch = 19.0mm. Gap = 19 - 18 = 1.0mm.
        # CN: 标准 135 胶片宽 35mm。
        # CN: 半格画幅 = 18.0mm (宽) x 24.0mm (高)。
        # CN: 4 个齿孔位间距 = 19.0mm。因此间隙 = 19 - 18 = 1.0mm。
        STRIP_W_MM = 35.0
        PHOTO_W_MM, PHOTO_H_MM = 18.0, 24.0
        GAP_MM = 1.0  # EN: Key research finding: 1.0mm / CN: 核心调研结论：1.0mm
        SPROC_W_MM, SPROC_H_MM = 2.0, 2.8
        INFO_ZONE_MM = 5.5
        
        cols, rows = final_cfg.get('cols', 12), final_cfg.get('rows', 6)
        m_x, m_y_t = final_cfg.get('margin_x', 150), final_cfg.get('margin_y_top', 500)

        # 3. EN: Calculate scale constants / CN: 计算比例常数
        col_pitch_px = (new_w - 2 * m_x) // cols
        # EN: Scaling ratio based on physical unit (frame + gap)
        # CN: 基于物理单元（画幅+间隙）的缩放比例
        px_per_mm = (col_pitch_px * (PHOTO_W_MM / (PHOTO_W_MM + GAP_MM))) / PHOTO_W_MM
        
        photo_w, photo_h = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)
        gap_w = int(GAP_MM * px_per_mm)
        strip_h, info_h = int(STRIP_W_MM * px_per_mm), int(INFO_ZONE_MM * px_per_mm)
        sp_w, sp_h = int(SPROC_W_MM * px_per_mm), int(SPROC_H_MM * px_per_mm)
        row_gap = final_cfg.get('row_gap', 100)

        # 4. EN: Font variants / CN: 字体变体
        # EN: Slightly smaller for 135HF density / CN: 针对高密度排版稍微缩小字号
        em_font = self.led_font.font_variant(size=int(1.3 * px_per_mm))
        db_font = self.seg_font.font_variant(size=int(1.3 * px_per_mm))

        # 5. EN: Roll-level metadata / CN: 全卷元数据
        standard_data = sample_data if sample_data else meta_handler.get_data(img_list[0])
        film_text = standard_data.get('EdgeCode') or standard_data.get('Film') or user_emulsion or "FILM"
        prefix = f"{user_emulsion.strip()}  " if user_emulsion and user_emulsion.strip() != film_text else ""
        display_code_from_standard = f"{prefix}{film_text}"
        cur_color = standard_data.get("ContactColor", (245, 130, 35, 210))

        # 6. EN: Render Loops / CN: 渲染循环
        for r in range(rows):
            sy = m_y_t + r * (strip_h + row_gap)
            strip_start_x = m_x - gap_w // 2
            strip_end_x = m_x + (cols * (photo_w + gap_w)) - gap_w // 2
            
            # EN: Draw film strip background / CN: 绘制胶片条背景
            draw.rectangle([strip_start_x, sy, strip_end_x, sy + strip_h], fill=(12, 12, 12))
            
            # EN: Render vector sprockets / CN: 渲染矢量齿孔
            self._draw_iso_sprockets_vector(canvas, strip_start_x, strip_end_x, sy, info_h, strip_h, sp_w, sp_h, px_per_mm, display_code_from_standard)

            for c in range(cols):
                idx = r * cols + c
                if idx >= len(img_list):
                    break
                
                curr_x = m_x + c * (photo_w + gap_w)
                py = sy + info_h

                # EN: Paste photo (Maintains portrait aspect)
                # CN: 粘贴照片（保持竖向比例）
                self._paste_photo_for_hf(canvas, img_list[idx], curr_x, py, photo_w, photo_h)

                # EN: Render index number / CN: 渲染索引序号
                top_label = f"{idx + 1}"
                tw = draw.textlength(top_label, font=em_font)
                draw.text((curr_x + (photo_w - tw)//2, sy + int(0.2 * px_per_mm)), top_label, font=em_font, fill=cur_color)

                # EN: Render data back (EXIF) per frame / CN: 每帧渲染数据背 (EXIF)
                sample_data_for_back = meta_handler.get_data(img_list[idx])
                date_font = self.into_dot_font.font_variant(size=int(1.2 * px_per_mm))
                exif_font = self.seg_font.font_variant(size=int(1.2 * px_per_mm))
                
                self._draw_glowing_data_back(
                    canvas, sample_data_for_back, curr_x, py, photo_w, photo_h,
                    cur_color, date_font, exif_font, px_per_mm,
                    show_date=show_date, show_exif=show_exif
                )

        # 7. EN: Right-side cutoff cleanup / CN: 右侧截断清理
        max_photo_right = m_x + cols * (photo_w + gap_w) - gap_w
        final_cutoff_x = max_photo_right + int(1.0 * px_per_mm)
        if final_cutoff_x < new_w:
            draw.rectangle([final_cutoff_x, 0, new_w, new_h], fill=(235, 235, 235))

        return canvas

    def _paste_photo_for_hf(self, canvas, path, x, y, w, h):
        """EN: Paste photo and keep portrait orientation for HF"""
        with Image.open(path) as img:
            # EN: Half-Frame is natively portrait. If shot landscape, rotate to fit.
            # CN: 半格原生即为竖向。如果是横拍，则旋转以适应。
            if img.width > img.height:
                img = img.rotate(-90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))
