# core/renderers/base_renderer.py
import os
import sys
from PIL import Image, ImageDraw, ImageFont

class BaseFilmRenderer:
    def __init__(self, font_path="consola.ttf", font_size=44):
        # EN: Get resource base path (works both in dev and PyInstaller exe)
        # CN: 获取资源基础路径（开发环境和打包后的 exe 都适用）
        if getattr(sys, 'frozen', False):
            # EN: Running in PyInstaller bundle / CN: 在打包的 exe 中运行
            base_path = sys._MEIPASS
        else:
            # EN: Running in normal Python environment / CN: 在普通 Python 环境中运行
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(os.path.dirname(current_dir))
        
        # A. EN: Standard Font / CN: 标准字体
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except:
            self.font = ImageFont.load_default()

        # B. EN: Metadata Font (Seven Segment) / CN: 元数据字体 (数码管)
        seg_path = os.path.join(base_path, "assets", "fonts", "LiquidCrystal-Bold.otf")
        try:
            self.seg_font = ImageFont.truetype(seg_path, 40)
        except:
            self.seg_font = self.font

        # C. EN: Edge Marking Font (LED Dot-Matrix) / CN: 侧边喷码字体 (点阵)
        led_path = os.path.join(base_path, "assets", "fonts", "consola.ttf")
        try:
            self.led_font = ImageFont.truetype(led_path, 48)
        except:
            print(f"CN: [!] 未找到喷码字体: {led_path}, 将回退。")
            self.led_font = self.font

        # D. EN: LED Dot-Matrix1 Font (for 135 date display) / CN: LED Dot-Matrix1 字体 (用于 135 日期显示)
        led_dot_path = os.path.join(base_path, "assets", "fonts", "LED Dot-Matrix1.ttf")
        try:
            self.led_dot_font = ImageFont.truetype(led_dot_path, 40)
        except:
            print(f"CN: [!] 未找到 LED Dot-Matrix1 字体: {led_dot_path}, 将回退到数码管字体。")
            self.led_dot_font = self.seg_font

        # E. EN: IntoDotMatrix Font (alternative for 135 date stamp) / CN: IntoDotMatrix 字体（135 日期喷码备用）
        into_dot_path = os.path.join(base_path, "assets", "fonts", "intodotmatrix.ttf")
        try:
            self.into_dot_font = ImageFont.truetype(into_dot_path, 40)
        except:
            print(f"CN: [!] 未找到 IntoDotMatrix 字体: {into_dot_path}, 将回退到 LED Dot-Matrix1。")
            self.into_dot_font = self.led_dot_font

    def prepare_canvas(self, w, h, emulsion_number=None):
        """
        EN: Prepare canvas and get emulsion number
        CN: 准备画布并获取乳剂号
        
        Args:
            emulsion_number: Optional emulsion number for GUI mode
        """
        if emulsion_number is None:
            # EN: If interactive (CLI), ask user; otherwise default to empty to avoid GUI blocking.
            # CN: 若为可交互命令行则询问用户；否则默认空字符串，避免 GUI 阻塞。
            if getattr(sys.stdin, "isatty", lambda: False)():
                user_emulsion = input(
                    "EN: Enter emulsion number (e.g. 049) | CN: 请输入乳剂号 (如 049) >>> "
                ).strip()
            else:
                user_emulsion = ""
        else:
            # EN: GUI mode - use provided value / CN: GUI模式 - 使用提供的值
            user_emulsion = (emulsion_number or "").strip() if isinstance(emulsion_number, str) else str(emulsion_number)
        canvas = Image.new("RGB", (w, h), (235, 235, 235))
        return canvas, user_emulsion

    def get_marking_str(self, sample_data, user_emulsion):
        # EN: Priority: EdgeCode > Film (User Input) > Default
        # CN: 优先级：专业喷码 > 匹配到的型号名(或手动输入) > 默认值
        film_text = sample_data.get("EdgeCode") or sample_data.get("Film") or "又错了"
        
        # 只有存在乳剂号时才拼接，体现精准度
        prefix = f"{user_emulsion.strip()}  " if user_emulsion else ""
        return f"{prefix}{film_text}"

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
    
    def get_clean_exif(self, data):
        """
        EN: Return sanitized Date and EXIF strings. Returns None if missing.
        CN: 返回清洗后的日期和 EXIF 字符串。如果缺失则返回 None。
        """
        # 1. 处理日期
        dt = data.get("DateTime", "")
        date_out = dt[2:10].replace(":", "/") if len(dt) >= 10 else None

        # 2. 处理 EXIF 组合
        f_num = data.get('FNumber')
        exp_val = data.get('ExposureTimeStr')
        foc_val = str(data.get("FocalLength", "")).lower()
        
        parts = []
        if f_num: parts.append(f"f/{f_num}")
        if exp_val: parts.append(f"{exp_val}s")
        if foc_val and foc_val not in ["", "---", "--"]: parts.append(foc_val)
        
        exif_out = "  ".join(parts) if parts else None
        
        return date_out, exif_out