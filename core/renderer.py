import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class FilmRenderer:
    """
    EN: Pro-grade renderer with dynamic typography hierarchy.
    CN: 中英双语：具备动态字号层级感的高级渲染器。
    """
    def __init__(self, font_main="assets/fonts/palab.ttf", font_sub="assets/fonts/gara.ttf"):
        self.font_main = font_main
        self.font_sub = font_sub
        self.bg_color = (255, 255, 255)
        self.main_color = (26, 26, 26)   
        self.sub_color = (85, 85, 85)
        self.border_line_color = (238, 238, 238)

    def process_image(self, img_path, data, output_dir, target_long_edge=3000):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            img = Image.open(img_path)
            if img.mode != "RGB": img = img.convert("RGB")
            img = self._smart_resize(img, target_long_edge)
            w, h = img.size
            
            # --- EN: DATA INTEGRITY CHECK / CN: 数据完整性校验 ---
            # EN: Get layout dict, ensure it has defaults to avoid N/A
            # CN: 获取布局字典，确保有默认值防止出现 N/A
            layout = data.get('layout', {})
            layout_name = layout.get('name', 'CUSTOM')
            side_ratio = layout.get('side', 0.04)
            top_ratio = layout.get('top', side_ratio)
            bottom_ratio = layout.get('bottom', 0.13)
            font_base_scale = layout.get('font_scale', 0.032)
            
            # --- EN: CALCULATE SPACING / CN: 计算物理间距 ---
            side_pad = int(w * side_ratio)
            top_pad = int(w * top_ratio)
            bottom_splice = int(h * bottom_ratio)
            
            new_w, new_h = w + (side_pad * 2), h + top_pad + side_pad + bottom_splice
            
            # --- EN: DRAWING / CN: 绘制流程 ---
            canvas = Image.new("RGB", (new_w, new_h), self.bg_color)
            canvas.paste(img, (side_pad, top_pad))
            draw = ImageDraw.Draw(canvas)
            
            # EN: 1px inner border / CN: 1像素内边框
            draw.rectangle([side_pad, top_pad, side_pad + w, top_pad + h], outline=self.border_line_color, width=1)
            
            # --- EN: TYPOGRAPHY HIERARCHY / CN: 字体层级关联 ---
            main_text, sub_text = self._prepare_strings(data)
            
            # EN: Link sub_size to main_size (0.78 ratio)
            # CN: 将副标题字号关联至主标题 (0.78 黄金比例)
            long_edge = max(new_w, new_h)
            base_main_font_size = int(long_edge * font_base_scale)
            base_sub_font_size = int(base_main_font_size * 0.78)

            # EN: Ensure text fits within the available space
            # CN: 确保文本适应可用空间
            available_width = new_w - (side_pad * 2) - 40  # 减去左右边距
            actual_main_size, actual_sub_size = self._adjust_font_sizes_to_fit(
                draw, main_text, sub_text, available_width, 
                base_main_font_size, base_sub_font_size
            )

            self._draw_pro_text(draw, new_w, h, side_pad, top_pad, bottom_splice, 
                            main_text, sub_text, actual_main_size, actual_sub_size)
            
            # EN: Apply shadow effect for professional film look / CN: 应用阴影效果实现专业胶片感
            final_output = self._apply_pro_shadow(canvas)
            return self._save_with_limit(final_output, img_path, output_dir, data, target_long_edge, layout_name)

        except Exception as e:
            print(f"CN: [×] 渲染程序出错: {e}")
            return False

    def _prepare_strings(self, data):
        """EN: Dual-Engine Typography / CN: 胶片/数码双引擎排版"""
        make_raw = str(data.get('Make') or "").strip()
        model_raw = str(data.get('Model') or "").strip()
        make = make_raw.upper()
        model = model_raw.upper()

        # EN: Deduplicate brand prefix in model (e.g., CANON CANON EOS R6 -> CANON EOS R6)
        # CN: 去重型号里的品牌前缀（示例：CANON CANON EOS R6 -> CANON EOS R6）
        dedup_model = model
        if make and model and model.startswith(make):
            dedup_model = model[len(make):].lstrip(" -_/") or model

        if "HASSELBLAD" in make:
            camera_text = f"HASSELBLAD {dedup_model or model or make}".strip()
        else:
            if make and dedup_model:
                camera_text = f"{make} {dedup_model}".strip()
            else:
                camera_text = dedup_model or make
        
        info_parts = []
        is_digi = data.get('is_digital', False)
        
        # 1. EN: Lens / CN: 镜头
        if data.get('LensModel'): 
            info_parts.append(data['LensModel'])
        
        # 2. EN: Focal Length (Digital only) / CN: 焦距 (仅数码)
        if is_digi and data.get('FocalLength'):
            info_parts.append(data['FocalLength'])
        
        # 3. EN: Exposure (Shutter + Aperture + ISO for Digital)
        # CN: 曝光组件 (快门 + 光圈 + 数码模式下的 ISO)
        params = []
        if data.get('ExposureTimeStr'): params.append(f"{data['ExposureTimeStr']}s")
        if data.get('FNumber'): params.append(f"f/{data['FNumber']}")
        if is_digi and data.get('ISO'): params.append(f"ISO {data['ISO']}")
        if params: info_parts.append(" ".join(params))
        
        # 4. EN: Film (Film mode only) / CN: 胶片名称 (仅胶片模式)
        if not is_digi:
            film_name = str(data.get('Film') or "").upper()
            if film_name: info_parts.append(film_name)
        
        return camera_text, "  |  ".join(info_parts)

    def _draw_pro_text(self, draw, new_w, h, side_pad, top_pad, bottom_splice, main_text, sub_text, m_size, s_size):
        # EN: Vertical center of the white area / CN: 白色区域垂直中心
        base_y = top_pad + h + (side_pad + bottom_splice) // 2
        
        # EN: Pro-tip: offset main and sub for better visual balance
        # CN: 专家提示：主标题微调上移，副标题微调下移，视觉更平衡
        try:
            from .typo_engine import TypoEngine
            TypoEngine.draw_text(draw, (new_w // 2, base_y - int(bottom_splice * 0.12)), main_text, self.font_main, m_size, self.main_color)
            TypoEngine.draw_text(draw, (new_w // 2, base_y + int(bottom_splice * 0.22)), sub_text, self.font_sub, s_size, self.sub_color)
        except:
            draw.text((new_w // 2, base_y), main_text, fill="black", anchor="mm")

    def _smart_resize(self, img, target):
        w, h = img.size
        scale = target / max(w, h)
        return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    def _apply_pro_shadow(self, canvas):
        shadow_margin = 140
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (255, 255, 255, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 140))
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 10)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.GaussianBlur(radius=20))
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas

    def _save_with_limit(self, img, original_path, output_dir, data, current_res, layout_name):
        out_name = f"GT23_{os.path.splitext(os.path.basename(original_path))[0]}.png"
        save_path = os.path.join(output_dir, out_name)
        img.save(save_path, "PNG", optimize=True, compress_level=9)
        
        f_size = os.path.getsize(save_path) / (1024 * 1024)
        if f_size > 10.0:
            new_res = current_res - 200
            if os.path.exists(save_path): os.remove(save_path)
            return self.process_image(original_path, data, output_dir, new_res)
        
        # EN: Log the identified format clearly / CN: 明确记录识别出的画幅
        print(f"CN: [✔] 渲染完成: {out_name} | 画幅: {layout_name}")
        return True
    
    def _adjust_font_sizes_to_fit(self, draw, main_text, sub_text, available_width, base_main_size, base_sub_size):
        """
        调整字体大小使其适应可用宽度
        """
        # 创建临时绘图对象来测量文本宽度
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 检查主文本宽度
        main_font = self._get_font(self.font_main, base_main_size)
        main_bbox = temp_draw.textbbox((0, 0), main_text, font=main_font)
        main_text_width = main_bbox[2] - main_bbox[0]
        
        main_scale_factor = min(1.0, available_width / main_text_width) if main_text_width > 0 else 1.0
        
        # 检查副文本宽度  
        sub_font = self._get_font(self.font_sub, base_sub_size)
        sub_bbox = temp_draw.textbbox((0, 0), sub_text, font=sub_font)
        sub_text_width = sub_bbox[2] - sub_bbox[0]
        
        sub_scale_factor = min(1.0, available_width / sub_text_width) if sub_text_width > 0 else 1.0
        
        # 使用最小缩放因子确保两个文本都不会超出边界
        final_scale_factor = min(main_scale_factor, sub_scale_factor)
        
        final_main_size = max(10, int(base_main_size * final_scale_factor))  # 最小字体大小为10
        final_sub_size = max(8, int(base_sub_size * final_scale_factor))   # 最小字体大小为8
        
        return final_main_size, final_sub_size

    def _get_font(self, font_path, font_size):
        """
        获取字体对象，如果指定字体不存在则使用默认字体
        """
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
            else:
                return ImageFont.load_default()
        except:
            return ImageFont.load_default()