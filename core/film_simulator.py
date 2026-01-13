# core/film_simulator.py
from PIL import Image, ImageDraw, ImageFont

class FilmSimulator:
    """
    EN: Replicates the physical appearance of 120 film edge markings.
    CN: 中英双语：复刻 120 胶片边缘喷码的物理外观。
    """
    def __init__(self):
        # EN: Consolas mimics the industrial dot-matrix font seen on film edges
        # CN: Consolas 字体能很好地模拟胶片边缘那种工业感点阵喷码
        try:
            self.font = ImageFont.truetype("consola.ttf", 40)
        except:
            self.font = ImageFont.load_default()
        
        # EN: Signature Fujifilm Amber-Orange (Translucent)
        # CN: 富士招牌的琥珀橘色（带透明度，模拟透光感）
        self.fuji_amber = (245, 130, 35, 210)

    def _render_text_layer(self, text):
        """
        EN: Creates a vertical transparent layer with amber text.
        CN: 创建一个带有琥珀色文字的垂直透明图层。
        """
        txt_img = Image.new('RGBA', (1200, 80), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        draw.text((0, 10), text, font=self.font, fill=self.fuji_amber)
        # EN: Rotate 90 degrees to fit the side of the film strip
        # CN: 旋转 90 度以符合胶片侧边排布
        return txt_img.rotate(90, expand=True)

    def draw_markings(self, canvas, x, y, w, h, film_full_name, frame_idx, emulsion=""):
        """
        EN: Main draw call: [Emulsion + Model] on left, [Arrow + Frame] on right.
        CN: 渲染主调用：左侧放置[乳剂号 + 型号]，右侧放置[箭头 + 序号]。
        """
        # --- EN: Model Name Mapping / CN: 型号名称映射 ---
        # EN: Based on your feedback, show 'RDPIII' instead of 'Provia 100F'
        # CN: 根据你的反馈，将全称映射为底片上的缩写（如 RDPIII）
        model_map = {
            "Provia 100F": "RDPIII",
            "Velvia 50": "RVP50",
            "Velvia 100": "RVP100",
            "Portra 400": "400VC", # 模拟柯达早期或特定版本缩写，也可保持原样
        }
        raw_name = film_full_name.replace("FUJIFILM ", "").replace("KODAK ", "")
        short_name = model_map.get(raw_name, raw_name.split()[-1].upper())

        # --- EN: LEFT SIDE / CN: 左侧 ---
        left_text = f"{emulsion}  {short_name}".strip()
        left_layer = self._render_text_layer(left_text)
        canvas.paste(left_layer, (int(x + 18), int(y + 60)), left_layer)

        # --- EN: RIGHT SIDE / CN: 右侧 ---
        right_text = f"▲  {frame_idx}"
        right_layer = self._render_text_layer(right_text)
        canvas.paste(right_layer, (int(x + w - 75), int(y + h // 2)), right_layer)