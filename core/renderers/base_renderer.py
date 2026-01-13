# core/renderers/base_renderer.py
from PIL import Image, ImageDraw, ImageFont

class BaseFilmRenderer:
    def __init__(self, font_path="consola.ttf", font_size=44):
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except:
            self.font = ImageFont.load_default()

    def prepare_canvas(self, w, h):
        """
        EN: Return canvas and ask for emulsion. / CN: 返回画布并获取乳剂号。
        """
        user_emulsion = input("CN: 请输入乳剂号 (如 049): ").strip()
        canvas = Image.new("RGB", (w, h), (235, 235, 235))
        return canvas, user_emulsion

    def create_rotated_text(self, text, angle=90, color=(245, 130, 35, 210)):
        left, top, right, bottom = self.font.getbbox(text)
        w, h = right - left, bottom - top
        txt_img = Image.new('RGBA', (w + 10, h + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        draw.text((5, 0), text, font=self.font, fill=color)
        return txt_img.rotate(angle, expand=True)

    def create_stretched_triangle(self, color):
        tri_raw = self.create_rotated_text("▲", 0, color=color)
        w, h = tri_raw.size
        stretched = tri_raw.resize((w, int(h * 1.8)), Image.Resampling.LANCZOS)
        return stretched.rotate(180, expand=True)