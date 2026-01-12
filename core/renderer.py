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
            bottom_ratio = layout.get('bottom', 0.13)
            font_base_scale = layout.get('font_scale', 0.032)
            
            # --- EN: CALCULATE SPACING / CN: 计算物理间距 ---
            side_pad = int(w * side_ratio)
            bottom_splice = int(h * bottom_ratio)
            
            new_w, new_h = w + (side_pad * 2), h + (side_pad * 2) + bottom_splice
            
            # --- EN: DRAWING / CN: 绘制流程 ---
            canvas = Image.new("RGB", (new_w, new_h), self.bg_color)
            canvas.paste(img, (side_pad, side_pad))
            draw = ImageDraw.Draw(canvas)
            
            # EN: 1px inner border / CN: 1像素内边框
            draw.rectangle([side_pad, side_pad, side_pad + w, side_pad + h], outline=self.border_line_color, width=1)
            
            # --- EN: TYPOGRAPHY HIERARCHY / CN: 字体层级关联 ---
            main_text, sub_text = self._prepare_strings(data)
            
            # EN: Link sub_size to main_size (0.78 ratio)
            # CN: 将副标题字号关联至主标题 (0.78 黄金比例)
            main_font_size = int(new_w * font_base_scale)
            sub_font_size = int(main_font_size * 0.78)
            
            self._draw_pro_text(draw, new_w, h, side_pad, bottom_splice, main_text, sub_text, main_font_size, sub_font_size)
            
            final_output = self._apply_pro_shadow(canvas)
            return self._save_with_limit(final_output, img_path, output_dir, data, target_long_edge, layout_name)

        except Exception as e:
            print(f"CN: [×] 渲染程序出错: {e}")
            return False

    def _prepare_strings(self, data):
        """EN: Dual-Engine Typography / CN: 胶片/数码双引擎排版"""
        make = str(data.get('Make') or "").upper()
        model = str(data.get('Model') or "").upper()
        camera_text = f"HASSELBLAD {model}" if "HASSELBLAD" in make else f"{make} {model}"
        
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

    def _draw_pro_text(self, draw, new_w, h, side_pad, bottom_splice, main_text, sub_text, m_size, s_size):
        # EN: Vertical center of the white area / CN: 白色区域垂直中心
        base_y = h + side_pad + (side_pad + bottom_splice) // 2
        
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