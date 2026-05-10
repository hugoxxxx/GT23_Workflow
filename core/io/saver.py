import os
from PIL import Image

class ImageSaver:
    """
    EN: Responsible for final image flattening and high-quality file saving.
    CN: 负责最终图像的合并（打平）与高质量文件保存。
    """
    
    @staticmethod
    def flatten_and_save(canvas, save_path, exif_bytes=None, quality=95, theme="light"):
        """
        EN: Flattens RGBA canvas to RGB based on theme and saves to disk.
        CN: 根据主题将 RGBA 画布打平并保存。
        """
        # 1. EN: Determine background color based on theme
        # CN: 根据主题确定打平后的背景色（防止阴影出现白边/黑边 artifacts）
        if theme in ["dark", "slate_teal"]:
            bg_color = (0, 0, 0)
        elif theme == "sakura":
            bg_color = (255, 245, 247)
        else:
            bg_color = (255, 255, 255)

        # 2. EN: Flatten Alpha / CN: 复合 Alpha 通道
        if canvas.mode == "RGBA":
            img_to_save = Image.new("RGB", canvas.size, bg_color)
            img_to_save.paste(canvas, mask=canvas.split()[3])
        else:
            img_to_save = canvas.convert("RGB")
            
        # 3. EN: Initial Save / CN: 初始保存
        img_to_save.save(save_path, "JPEG", quality=quality, subsampling=0, exif=exif_bytes)
        
        # 4. EN: Quality Guard / CN: 质量守卫 (针对大图进行二次压缩)
        try:
            f_size = os.path.getsize(save_path) / (1024 * 1024)
            if f_size > 10.0:
                img_to_save.save(save_path, "JPEG", quality=92, subsampling=0, exif=exif_bytes)
                f_size = os.path.getsize(save_path) / (1024 * 1024)
        except:
            f_size = 0
            
        return os.path.basename(save_path), f_size
