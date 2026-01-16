# core/renderers/renderer_135.py
import os
from PIL import Image, ImageDraw, ImageFont
from .base_renderer import BaseFilmRenderer
# --- [新增] 矢量渲染依赖 ---
# 我们现在强制要求 cairosvg 可用，不再提供回退选项。
# 这保证了代码路径的简洁和 ISO 1007 标准的严格执行。
import svgwrite
from cairosvg import svg2png
import io
# --- [END OF NEW IMPORTS] ---

class Renderer135(BaseFilmRenderer):
    """ EN: 135 Format - Dynamic EdgeCode & Precision Positioning (v9.2)
         CN: 135 画幅 - 动态喷码修正版：解决写死字符串问题、数据后背极低位压低、手动输入复用问题。 """
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None):
        print("\n" + "="*65)
        print("CN: [135 9.5] 修复：复用手动输入的 sample_data，避免后续图片匹配失败。")
        print("="*65)
        
        final_cfg = meta_handler.get_contact_layout("135")
        new_w, new_h = final_cfg.get('canvas_w', 4800), final_cfg.get('canvas_h', 6000)
        canvas = canvas.resize((new_w, new_h))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, new_w, new_h], fill=(235, 235, 235))

        # --- 1. ISO 1007 物理参数 (mm) ---
        STRIP_W_MM, PHOTO_W_MM, PHOTO_H_MM = 35.0, 36.0, 24.0
        GAP_MM = 2.0 # 2mm 过片间隙
        SPROC_W_MM, SPROC_H_MM = 2.0, 2.8
        INFO_ZONE_MM = 5.5
        cols, rows = final_cfg.get('cols', 6), final_cfg.get('rows', 6)
        m_x, m_y_t = final_cfg.get('margin_x', 150), final_cfg.get('margin_y_top', 500)

        col_pitch_px = (new_w - 2 * m_x) // cols
        px_per_mm = (col_pitch_px * (PHOTO_W_MM / (PHOTO_W_MM + GAP_MM))) / PHOTO_W_MM
        photo_w, photo_h = int(PHOTO_W_MM * px_per_mm), int(PHOTO_H_MM * px_per_mm)
        gap_w, strip_h, info_h = int(GAP_MM * px_per_mm), int(STRIP_W_MM * px_per_mm), int(INFO_ZONE_MM * px_per_mm)
        sp_w, sp_h = int(SPROC_W_MM * px_per_mm), int(SPROC_H_MM * px_per_mm)
        rg = final_cfg.get('row_gap', 150)

        # 统一缩小的喷码字号 (1.6mm 物理高度)
        em_font = ImageFont.truetype(self.led_font.path, int(1.6 * px_per_mm))
        db_font = ImageFont.truetype(self.seg_font.path, int(1.6 * px_per_mm))

        # --- [核心修改点] 只读取一次，获取标准信息 ---
        # 如果 sample_data 不存在（兼容旧逻辑），则读取第一张图片
        standard_data = sample_data if sample_data else meta_handler.get_data(img_list[0])
        # 提取需要在整个胶卷上保持一致的信息
        display_code_from_standard = standard_data.get('EdgeCode') or standard_data.get('Film') or user_emulsion or "未知胶卷"
        cur_color_from_standard = standard_data.get("ContactColor", (245, 130, 35, 210))
        # --- [END OF MODIFICATION] ---

        for r in range(rows):
            sy = m_y_t + r * (strip_h + rg)
            strip_start_x, strip_end_x = m_x - gap_w // 2, m_x + (cols * (photo_w + gap_w)) - gap_w // 2
            draw.rectangle([strip_start_x, sy, strip_end_x, sy + strip_h], fill=(12, 12, 12))
            # --- [核心修改] 使用高精度矢量齿孔 ---
            self._draw_iso_sprockets_vector(canvas, strip_start_x, strip_end_x, sy, info_h, strip_h, sp_w, sp_h, px_per_mm)
            # --- [END OF MODIFICATION] ---

            for c in range(cols):
                idx = r * cols + c
                if idx >= len(img_list):
                    break
                curr_x, py = m_x + c * (photo_w + gap_w), sy + info_h

                # --- [核心修改点] 使用预读取的标准信息 ---
                # cur_color 和 display_code 都来自第一次读取的 standard_data
                cur_color = cur_color_from_standard
                display_code = display_code_from_standard
                # --- [END OF MODIFICATION] ---

                self._paste_photo_auto_rotate(canvas, img_list[idx], curr_x, py, photo_w, photo_h)

                # --- [修正逻辑] 动态 EdgeCode ---
                # 使用从 standard_data 获取的 display_code
                top_label = f"{idx + 1} {display_code}"
                tw = draw.textlength(top_label, font=em_font)
                # 顶部 2mm 缝隙垂直居中
                draw.text((curr_x + (photo_w - tw)//2, sy + int(0.2 * px_per_mm)), top_label, font=em_font, fill=cur_color)

                # 底部过片间隙帧号
                gap_center_x = curr_x + photo_w + (gap_w // 2)
                frame_label = f"{idx + 1}A"
                fw = draw.textlength(frame_label, font=em_font)
                # 底部 2mm 缝隙垂直居中
                draw.text((gap_center_x - fw//2, sy + strip_h - int(1.8 * px_per_mm)), frame_label, font=em_font, fill=cur_color)

                # [精准定义] 我们在这里定义两个变量，分别控制日期和 EXIF
                # CN: date_font 用于照片内左下角，exif_font 用于照片外黑边
                date_font = self.seg_font.font_variant(size=int(1.5 * px_per_mm))
                exif_font = self.seg_font.font_variant(size=int(1.5 * px_per_mm)) # EXIF 稍微小一点，适合塞进黑边

                # --- [重要] 数据背信息 ---
                # 数据背可能需要显示每张照片特有的信息（如具体日期、EXIF）。
                # 为了兼容性和一致性，这里可以选择使用 standard_data 或 individual_data。
                # 方案一：所有照片显示相同的基础信息（如统一的相机型号，若存在）
                # sample_data_for_back = standard_data
                # 方案二：照片显示各自的具体EXIF
                sample_data_for_back = meta_handler.get_data(img_list[idx])

                # 压低的数据后背 (极靠右下角)
                self._draw_glowing_data_back(canvas, sample_data_for_back, curr_x, py, photo_w, photo_h, cur_color, date_font, exif_font, px_per_mm)

        # --- [最终截断] 全局右侧清理 ---
        # CN: 135 渲染器尺寸固定，直接在照片右边缘外侧刷一层背景色，切掉所有超出的序号。
        # EN: Global crop: Overwrite anything beyond the last photo column with background color.
        # 计算理论上最后一列照片的右边缘 (px)
        # 135 模式：起始偏移 + 列数 * (照片宽 + 间隙) - 最后一个多算的间隙
        max_photo_right = m_x + cols * (photo_w + gap_w) - gap_w
        # 截断点：最后一张照片右边缘 + 1mm 呼吸位
        final_cutoff_x = max_photo_right + int(1.0 * px_per_mm)
        # 如果截断点在画布内，直接刷到底
        if final_cutoff_x < new_w:
            # draw.rectangle([左, 上, 右, 下], fill=背景色)
            # y1=0, y2=new_h 代表从画布顶部一直刷到底部
            draw.rectangle([final_cutoff_x, 0, new_w, new_h], fill=(235, 235, 235))

        return canvas

    

    def _paste_photo_auto_rotate(self, canvas, path, x, y, w, h):
        with Image.open(path) as img:
            if img.height > img.width:
                img = img.rotate(-90, expand=True)
            img = img.resize((w, h), Image.Resampling.LANCZOS)
            canvas.paste(img, (int(x), int(y)))

    def _draw_single_glowing_text(self, canvas, text, pos, font, color):
        draw = ImageDraw.Draw(canvas)
        glow_color = (color[0], color[1], color[2], 75)
        draw.text((pos[0]+1, pos[1]+1), text, font=font, fill=glow_color)
        draw.text(pos, text, font=font, fill=color)

    def _draw_glowing_data_back(self, canvas, data, px, py, pw, ph, color, d_font, e_font, px_mm):
        date_str, exif_str = self.get_clean_exif(data)

        # 1. 绘制日期 (右下角版)
        if date_str and str(date_str).strip().upper() != "NONE":
            margin = 1.5 * px_mm
            bbox = d_font.getbbox(date_str) # 使用 d_font
            text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            pos_d = (px + pw - margin - text_w, py + ph - margin - text_h)
            self._draw_single_glowing_text(canvas, date_str, pos_d, d_font, color)

        # 2. EXIF (精准对齐下方黑边居中)
        if exif_str and str(exif_str).strip().upper() != "NONE":
            # 计算 y 偏移：
            # 135 胶卷底部黑边约 5.5mm，齿孔占据了中间 2.8mm。
            # 齿孔下方的纯黑边宽度约只有 1.5mm - 2mm。
            # 我们将文字中心定在距离照片底部约 4.6mm 处。
            offset_y = 4 * px_mm
            # 计算 x 居中：
            # 照片起点 + (照片宽 - 文字宽) / 2
            tw_e = ImageDraw.Draw(canvas).textlength(exif_str, font=e_font)
            pos_e_x = px + (pw - tw_e) // 2
            # y 轴：照片底边 py + ph 再加上偏移
            pos_e_y = py + ph + offset_y
            self._draw_single_glowing_text(canvas, exif_str, (pos_e_x, pos_e_y), e_font, color)

    def _draw_iso_sprockets_vector(self, canvas, x_start, x_end, sy, info_h, strip_h, sp_w, sp_h, px_per_mm):
            """
            使用 SVG + CairoSVG 绘制高精度抗锯齿齿孔。
            这是绘制 ISO 1007 齿孔的唯一方法，不提供光栅回退。
            """
            # 创建一个与胶片条等宽高的透明画布 (RGBA)
            strip_width = int(x_end - x_start)
            if strip_width <= 0:
                return

            # --- 1. 构建 SVG ---
            dwg = svgwrite.Drawing(size=(strip_width, strip_h), profile='tiny')
            dwg.viewbox(0, 0, strip_width, strip_h)

            # 定义精确的 KS 齿孔参数 (毫米)，符合 ISO 1007
            SPROC_H_MM_ACTUAL = 2.8
            SPROC_W_MM_ACTUAL = 1.94
            CORNER_RADIUS_MM = 0.4
            PITCH_MM = 4.75

            # 计算 SVG 中的像素尺寸
            w_px = SPROC_W_MM_ACTUAL * px_per_mm
            h_px = SPROC_H_MM_ACTUAL * px_per_mm
            r_px = CORNER_RADIUS_MM * px_per_mm
            pitch_px = PITCH_MM * px_per_mm

            # 计算齿孔 Y 坐标 (物理对齐: 外边 2mm)
            y_top_svg = 2.0 * px_per_mm
            y_bottom_svg = strip_h - (2.0 * px_per_mm) - h_px

            # 生成齿孔路径
            def make_rounded_rect_path(x, y, w, h, r):
                return (
                    f"M {x+r},{y} "
                    f"H {x+w-r} "
                    f"A {r},{r} 0 0 1 {x+w},{y+r} "
                    f"V {y+h-r} "
                    f"A {r},{r} 0 0 1 {x+w-r},{y+h} "
                    f"H {x+r} "
                    f"A {r},{r} 0 0 1 {x},{y+h-r} "
                    f"V {y+r} "
                    f"A {r},{r} 0 0 1 {x+r},{y} Z"
                )

            # 绘制顶部和底部齿孔
            current_x = (pitch_px / 4) # 起始偏移，符合标准
            while current_x < strip_width:
                if current_x + w_px < strip_width:
                    # 顶部
                    path_d = make_rounded_rect_path(current_x, y_top_svg, w_px, h_px, r_px)
                    dwg.add(dwg.path(d=path_d, fill='white'))
                    # 底部
                    path_d = make_rounded_rect_path(current_x, y_bottom_svg, w_px, h_px, r_px)
                    dwg.add(dwg.path(d=path_d, fill='white'))
                current_x += pitch_px

            # --- 2. 将 SVG 渲染为 PNG 字节流 ---
            # 使用高 DPI (600) 保证边缘极度平滑
            png_bytes = svg2png(bytestring=dwg.tostring(), dpi=1200, output_width=strip_width, output_height=strip_h)

            # --- 3. 转换为 PIL Image ---
            vector_strip = Image.open(io.BytesIO(png_bytes)).convert('RGBA')

            # 将矢量条贴到主画布上
            canvas.paste(vector_strip, (int(x_start), int(sy)), mask=vector_strip)    