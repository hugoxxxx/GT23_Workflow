from PIL import Image, ImageDraw

class SprocketEngine:
    """
    EN: Film sprocket and perfs rendering engine for 135/120 formats.
    CN: 135/120 胶片齿孔与边码渲染引擎。
    """
    
    @staticmethod
    def apply_sprocket_perfs(canvas, img_w, img_h, x, y):
        """
        EN: Draws physical-accurate Kodak-style film perfs.
        CN: 绘制物理精确的柯达风格胶片齿孔。
        """
        draw = ImageDraw.Draw(canvas)
        # EN: Standard 135 Film Perf: 4.75mm x 2.80mm / CN: 标准 135 齿孔尺寸
        # EN: We calculate scale based on image height relative to 24mm film area
        px_per_mm = img_h / 24.0
        
        perf_w = int(4.75 * px_per_mm)
        perf_h = int(2.80 * px_per_mm)
        perf_r = int(0.5 * px_per_mm) # Corner radius
        
        # EN: Pitch is 4.75mm / CN: 齿孔间距
        pitch = int(4.75 * px_per_mm)
        
        # EN: Top perfs
        for px in range(0, canvas.width, pitch * 2):
            left = px + pitch // 2
            top = int(1.0 * px_per_mm)
            draw.rounded_rectangle([left, top, left + perf_w, top + perf_h], radius=perf_r, fill=(20, 20, 20))
            
        # EN: Bottom perfs
        for px in range(0, canvas.width, pitch * 2):
            left = px + pitch // 2
            top = canvas.height - int(1.0 * px_per_mm) - perf_h
            draw.rounded_rectangle([left, top, left + perf_w, top + perf_h], radius=perf_r, fill=(20, 20, 20))
            
    @staticmethod
    def get_sprocket_colors():
        """
        EN: Returns the high-contrast exposure palette for sprocket mode.
        CN: 返回齿孔模式下的高对比度曝光色调。
        """
        # EN: Exposure Orange / Luminous White
        return (0, 0, 0), (255, 120, 0), (235, 235, 235), (40, 40, 40)
