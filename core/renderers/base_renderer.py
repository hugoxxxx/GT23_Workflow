# core/renderers/base_renderer.py
import os
from PIL import Image, ImageDraw, ImageFont

class BaseFilmRenderer:
    def __init__(self, font_path="consola.ttf", font_size=44):
        # EN: Get project root / CN: 获取项目根目录以定位 assets
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # A. EN: Standard Font / CN: 标准字体
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except:
            self.font = ImageFont.load_default()

        # B. EN: Metadata Font (Seven Segment) / CN: 元数据字体 (数码管)
        seg_path = os.path.join(project_root, "assets", "fonts", "LiquidCrystal-Bold.otf")
        try:
            self.seg_font = ImageFont.truetype(seg_path, 40)
        except:
            self.seg_font = self.font

        # C. EN: Edge Marking Font (LED Dot-Matrix) / CN: 侧边喷码字体 (点阵)
        led_path = os.path.join(project_root, "assets", "fonts", "consola.ttf")
        try:
            self.led_font = ImageFont.truetype(led_path, 48)
        except:
            print(f"CN: [!] 未找到喷码字体: {led_path}, 将回退。")
            self.led_font = self.font

    def prepare_canvas(self, w, h):
        user_emulsion = input("CN: 请输入乳剂号 (如 049): ").strip()
        canvas = Image.new("RGB", (w, h), (235, 235, 235))
        return canvas, user_emulsion

    def get_marking_str(self, sample_data, user_emulsion):
        film_text = sample_data.get("EdgeCode") or "KODAK"
        return f"{user_emulsion}  {film_text}"

    def create_stretched_triangle(self, color):
        """EN: 16x34 base triangle / CN: 生成基础拉伸三角符号"""
        base_w, base_h = 16, 34
        tri_img = Image.new('RGBA', (base_w, base_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(tri_img)
        d.polygon([(0, base_h), (base_w, base_h // 2), (0, 0)], fill=color)
        return tri_img

    def create_rotated_text(self, text, angle=90, color=(245, 130, 35, 210)):
        left, top, right, bottom = self.led_font.getbbox(text)
        w, h = right - left, bottom - top
        txt_img = Image.new('RGBA', (w + 20, h + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        draw.text((10, 0), text, font=self.led_font, fill=color)
        return txt_img.rotate(angle, expand=True)
    
    def create_rotated_seg_text(self, text, angle, color):
        """ 
        EN: Standard Seven-Segment text generator with rotation.
        CN: 标准数码管文字生成器，支持旋转，复用项目内置 seg_font。
        """
        l, t, r, b = self.seg_font.getbbox(text)
        img = Image.new('RGBA', (r - l + 20, b - t + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((10, 0), text, font=self.seg_font, fill=color)
        return img.rotate(angle, expand=True)