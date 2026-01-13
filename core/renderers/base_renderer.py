# core/renderers/base_renderer.py
import os
from PIL import Image, ImageDraw, ImageFont

class BaseFilmRenderer:
    def __init__(self, font_path="consola.ttf", font_size=44):
        # EN: Get project root / CN: 获取项目根目录以定位 assets
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # A. EN: Standard Font / CN: 标准字体 (用于辅助计算)
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

        # C. EN: Edge Marking Font (LED Dot-Matrix) / CN: 侧边喷码字体 (LED 点阵)
        led_path = os.path.join(project_root, "assets", "fonts", "consola.ttf")
        try:
            # EN: Dot-Matrix fonts usually need slightly larger size to be legible
            # CN: 点阵字体通常需要稍大一点的字号（如 48）来保证清晰度
            self.led_font = ImageFont.truetype(led_path, 48)
        except:
            print(f"CN: [!] 未找到喷码字体: {led_path}, 将回退。")
            self.led_font = self.font

    def prepare_canvas(self, w, h):
        user_emulsion = input("CN: 请输入乳剂号 (如 049): ").strip()
        canvas = Image.new("RGB", (w, h), (235, 235, 235))
        return canvas, user_emulsion

    def get_marking_str(self, sample_data, user_emulsion):
        # EN: Returns formatted string for LED font / CN: 返回适用于 LED 字体的格式
        film_text = sample_data.get("EdgeCode") or "KODAK"
        return f"{user_emulsion}  {film_text}"

    def get_metadata_str(self, sample_data):
        """EN: Format EXIF as YY-MM-DD / CN: 格式化元数据，时间使用 yy-mm-dd"""
        f_num = sample_data.get('FNumber', '')
        shutter = sample_data.get('ExposureTimeStr', '')
        focal = sample_data.get('FocalLength', '')
        dt = sample_data.get('DateTime', '') # 格式通常为 "YYYY:MM:DD HH:MM:SS"

        # --- CN: 时间格式转换 YY-MM-DD ---
        date_part = ""
        if dt and len(dt) >= 10:
            raw_date = dt[:10].replace(":", "/") # "2026-01-13"
            date_part = raw_date[2:] # "26-01-13"

        parts = []
        if f_num: parts.append(f"f/{f_num}")
        if shutter: parts.append(f"{shutter}s")
        if focal: parts.append(focal)
        
        info_str = "  ".join(parts)
        return f"{info_str}   {date_part}".strip()

    def create_stretched_triangle(self, color):
        """EN: 16x34 base triangle / CN: 生成基础拉伸三角符号"""
        base_w, base_h = 16, 34
        tri_img = Image.new('RGBA', (base_w, base_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(tri_img)
        d.polygon([(0, base_h), (base_w, base_h // 2), (0, 0)], fill=color)
        return tri_img

    def create_rotated_text(self, text, angle=90, color=(245, 130, 35, 210)):
        # EN: Use led_font for edge markings / CN: 侧边喷码改用 led_font
        left, top, right, bottom = self.led_font.getbbox(text)
        w, h = right - left, bottom - top
        txt_img = Image.new('RGBA', (w + 20, h + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        draw.text((10, 0), text, font=self.led_font, fill=color)
        return txt_img.rotate(angle, expand=True)