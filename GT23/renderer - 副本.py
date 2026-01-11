import os
from PIL import Image, ImageDraw, ImageFilter
from .typo_engine import TypoEngine

class FilmRenderer:
    def __init__(self):
        # EN: Visual setup / CN: 中英双语：视觉参数配置
        self.bg_color = (255, 255, 255)
        self.main_color = (26, 26, 26)   
        self.sub_color = (85, 85, 85)    
        self.border_line_color = (238, 238, 238) 
        
        # EN: Asset paths / CN: 资源路径
        self.font_dir = os.path.abspath("assets/fonts")
        self.font_main = os.path.join(self.font_dir, "palab.ttf")
        self.font_sub = os.path.join(self.font_dir, "gara.ttf")

    def apply_pro_shadow(self, canvas):
        # EN: Add gallery-style soft shadow / CN: 添加画廊级柔和阴影
        shadow_margin = 160 
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (255, 255, 255, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 153)) 
        
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 15)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.GaussianBlur(radius=25))
        
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas

    def process_image(self, img_path, metadata, output_dir):
        try:
            # EN: Ensure output directory exists / CN: 确保输出目录存在
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with Image.open(img_path) as img:
                if img.mode != "RGB": img = img.convert("RGB")
                w, h = img.size
                
                # --- EN: Layout / CN: 布局比例 ---
                side_pad = int(w * 0.04)
                bottom_splice = int(h * 0.13)
                new_w, new_h = w + (side_pad * 2), h + (side_pad * 2) + bottom_splice 
                
                canvas = Image.new("RGB", (new_w, new_h), self.bg_color)
                canvas.paste(img, (side_pad, side_pad))
                draw = ImageDraw.Draw(canvas)
                
                # EN: 1px internal border / CN: 1像素细边框
                draw.rectangle([side_pad, side_pad, side_pad + w, side_pad + h], outline=self.border_line_color, width=1)
                
                # --- EN: Typography Positioning / CN: 排版定位计算 ---
                base_area_center = h + side_pad + (side_pad + bottom_splice) // 2
                main_size = int(w * 0.032)
                sub_size = int(w * 0.026)
                
                # EN: Format Text Content / CN: 格式化文字内容
                make = str(metadata.get('Make', '')).upper()
                model = str(metadata.get('Model', '')).upper()
                camera_text = f"HASSELBLAD {model}" if "HASSELBLAD" in make else f"{make} {model}"
                
                info_parts = []
                # EN: Check if LensModel exists / CN: 检查镜头模型是否存在
                if metadata.get('LensModel'): info_parts.append(metadata['LensModel'])
                
                params = []
                if metadata.get('ExposureTimeStr'): params.append(f"{metadata['ExposureTimeStr']}s")
                if metadata.get('FNumber'): params.append(f"f/{metadata['FNumber']}")
                if params: info_parts.append(" ".join(params))
                
                if metadata.get('Film'): info_parts.append(metadata['Film'])
                info_line = "  |  ".join(info_parts)

                # --- EN: Call TypoEngine / CN: 调用排版引擎 ---
                TypoEngine.draw_text(draw, (new_w // 2, base_area_center - int(bottom_splice * 0.15)), 
                                     camera_text, self.font_main, main_size, self.main_color)

                TypoEngine.draw_text(draw, (new_w // 2, base_area_center + int(bottom_splice * 0.20)), 
                                     info_line, self.font_sub, sub_size, self.sub_color)

                # --- EN: Save Process / CN: 保存流程 ---
                # EN: Use PNG for shadow transparency / CN: 使用 PNG 以支持阴影透明度
                final_output = self.apply_pro_shadow(canvas)
                out_name = f"GT23_{os.path.splitext(os.path.basename(img_path))[0]}.png"
                save_path = os.path.join(output_dir, out_name)
                
                # EN: Explicit save call / CN: 显式保存调用
                final_output.save(save_path, "PNG")
                print(f"CN: [✔] 渲染成功，保存至: {save_path}")
                return True
                
        except Exception as e:
            print(f"CN: [×] 渲染程序出错: {e}")
            import traceback
            traceback.print_exc()
            return False