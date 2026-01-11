import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class FilmRenderer:
    """
    EN: Renders film-style borders and metadata with size/resolution control.
    CN: 中英双语：渲染带有边框和元数据的胶卷效果，并控制分辨率与文件体积。
    """
    def __init__(self, font_main="assets/fonts/palab.ttf", font_sub="assets/fonts/gara.ttf"):
        # EN: Visual setup / CN: 视觉参数配置
        self.font_main = font_main
        self.font_sub = font_sub
        self.border_ratio = 0.04  # 4% 侧边框
        self.bottom_ratio = 0.13  # 13% 底部边框
        self.bg_color = (255, 255, 255)
        self.main_color = (26, 26, 26)   
        self.sub_color = (85, 85, 85)
        self.border_line_color = (238, 238, 238)

    def process_image(self, img_path, data, output_dir, target_long_edge=3000):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 1. EN: Load and Resize / CN: 加载并等比缩放
            img = Image.open(img_path)
            if img.mode != "RGB": img = img.convert("RGB")
            img = self._smart_resize(img, target_long_edge)
            w, h = img.size
            
            # 2. EN: Layout Calculation / CN: 布局计算
            side_pad = int(w * self.border_ratio)
            bottom_splice = int(h * self.bottom_ratio)
            new_w, new_h = w + (side_pad * 2), h + (side_pad * 2) + bottom_splice
            
            canvas = Image.new("RGB", (new_w, new_h), self.bg_color)
            canvas.paste(img, (side_pad, side_pad))
            draw = ImageDraw.Draw(canvas)
            
            # EN: Inner Border / CN: 1px 细内边框
            draw.rectangle([side_pad, side_pad, side_pad + w, side_pad + h], outline=self.border_line_color, width=1)
            
            # 3. EN: Metadata Extraction (Crucial Fix) / CN: 元数据提取 (核心修复)
            # EN: Funnel-style detection for film name
            # CN: 漏斗式胶片名称识别：匹配所有可能的 EXIF 键名
            film_val = (data.get('Film') or 
                        data.get('film') or 
                        data.get('Image Description') or 
                        data.get('ImageDescription') or 
                        data.get('Description') or "")
            
            film_name = str(film_val).upper() if film_val else ""

            # EN: Prepare Other Info / CN: 准备其他参数
            make = str(data.get('Make') or "").upper()
            model = str(data.get('Model') or "").upper()
            camera_text = f"HASSELBLAD {model}" if "HASSELBLAD" in make else f"{make} {model}"
            
            info_parts = []
            if data.get('LensModel'): info_parts.append(data['LensModel'])
            
            params = []
            if data.get('ExposureTimeStr'): params.append(f"{data['ExposureTimeStr']}s")
            if data.get('FNumber'): params.append(f"f/{data['FNumber']}")
            if params: info_parts.append(" ".join(params))
            if film_name: info_parts.append(film_name)
            
            info_line = "  |  ".join(info_parts)

            # 4. EN: Draw Text / CN: 绘制文字
            self._draw_pro_text(draw, new_w, h, side_pad, bottom_splice, camera_text, info_line)
            
            # 5. EN: Apply Shadow / CN: 添加画廊阴影 (防止色阶断层，不使用量化)
            final_output = self._apply_pro_shadow(canvas)
            
            # 6. EN: Save with 200px Recursive Limit / CN: 200px 步进递归保存检查
            return self._save_with_limit(final_output, img_path, output_dir, data, target_long_edge)

        except Exception as e:
            print(f"CN: [×] 渲染程序出错: {e}")
            return False

    def _smart_resize(self, img, target):
        w, h = img.size
        scale = target / max(w, h)
        return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    def _draw_pro_text(self, draw, new_w, h, side_pad, bottom_splice, main_text, sub_text):
        base_y = h + side_pad + (side_pad + bottom_splice) // 2
        main_size = int(new_w * 0.032)
        sub_size = int(new_w * 0.026)
        
        try:
            from .typo_engine import TypoEngine
            TypoEngine.draw_text(draw, (new_w // 2, base_y - int(bottom_splice * 0.15)), main_text, self.font_main, main_size, self.main_color)
            TypoEngine.draw_text(draw, (new_w // 2, base_y + int(bottom_splice * 0.20)), sub_text, self.font_sub, sub_size, self.sub_color)
        except:
            # Fallback if TypoEngine missing / 如果排版引擎缺失的兜底逻辑
            draw.text((new_w // 2, base_y), main_text, fill="black", anchor="mm")

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

    def _save_with_limit(self, img, original_path, output_dir, data, current_res):
        out_name = f"GT23_{os.path.splitext(os.path.basename(original_path))[0]}.png"
        save_path = os.path.join(output_dir, out_name)
        
        # EN: Save as pure PNG / CN: 纯 PNG 保存，杜绝色阶断层
        img.save(save_path, "PNG", optimize=True, compress_level=9)
        
        f_size = os.path.getsize(save_path) / (1024 * 1024)
        if f_size > 10.0:
            # EN: Recursive Step: -200px / CN: 递归步进：下调 200px
            new_res = current_res - 200
            print(f"CN: [!] {f_size:.2f}MB 超标，降级至 {new_res}px 重新渲染...")
            if os.path.exists(save_path): os.remove(save_path)
            return self.process_image(original_path, data, output_dir, new_res)
        
        print(f"CN: [✔] 渲染完成: {out_name} | 大小: {f_size:.2f}MB | 分辨率: {current_res}px")
        return True