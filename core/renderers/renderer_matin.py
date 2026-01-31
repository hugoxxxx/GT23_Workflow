# core/renderers/renderer_matin.py
# EN: Renderer for Matin-Style slide archival sheets
# CN: Matin 风格幻灯片活页渲染器

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from .base_renderer import BaseFilmRenderer

class RendererMatin(BaseFilmRenderer):
    """
    EN: Renders images as mounted slides in a grid.
    CN: 将图片渲染为带卡槽的幻灯片网格布局。
    """
    
    def render(self, canvas, img_list, cfg, meta_handler, user_emulsion, sample_data=None, 
               orientation=None, show_date=True, show_exif=True):
        
        draw = ImageDraw.Draw(canvas)
        # EN: Background - off-white archival page / CN: 背景 - 类乳白色收藏页
        draw.rectangle([0, 0, canvas.width, canvas.height], fill=(245, 245, 245))
        
        cols = cfg.get('cols', 4)
        rows = cfg.get('rows', 5)
        cell_w = cfg.get('cell_w', 1181) # 5cm at 600dpi
        cell_h = cfg.get('cell_h', 1181)
        col_gap = cfg.get('col_gap', 40)
        row_gap = cfg.get('row_gap', 40)
        m_x = cfg.get('margin_x', 150)
        m_y_t = cfg.get('margin_y_top', 500)
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(img_list):
                    break
                
                # Calculate top-left of the mount
                x = m_x + c * (cell_w + col_gap)
                y = m_y_t + r * (cell_h + row_gap)
                
                self._draw_mounted_slide(canvas, img_list[idx], x, y, cell_w, cell_h, 
                                         meta_handler, show_date, show_exif)
        
        return canvas

    def _draw_mounted_slide(self, canvas, img_path, x, y, cw, ch, meta, show_date, show_exif):
        """EN: Draw a single slide mount with depth and labels / CN: 绘制带有深度感和标签的单张幻灯片卡槽"""
        draw = ImageDraw.Draw(canvas)
        
        # 1. EN: Drop Shadow / CN: 绘制投影 (Subtle)
        shadow_box = [x+8, y+8, x+cw+8, y+ch+8]
        draw.rectangle(shadow_box, fill=(210, 210, 210))
        
        # 2. EN: Main Mount Body / CN: 片框主体 (Modern White)
        mount_fill = (255, 255, 255)
        draw.rectangle([x, y, x+cw, y+ch], fill=mount_fill, outline=(225, 225, 225), width=2)
        
        # 3. EN: Inner Bevel (Thickness feel) / CN: 内倒角 (表现厚度感)
        bevel_inset = 6
        draw.rectangle([x+bevel_inset, y+bevel_inset, x+cw-bevel_inset, y+ch-bevel_inset], 
                       outline=(235, 235, 235), width=4)
        
        # 4. EN: Photo Aperture / CN: 照片窗口
        # Calculate aperture based on format
        if cw == 1181: # 135 Matin (5x5cm)
            ap_w_mm, ap_h_mm = 36.0, 24.0
            px_per_mm = cw / 50.0 # 50mm = 5cm
        else: # 120 Matin (7.7x7cm)
            ap_w_mm, ap_h_mm = 56.0, 56.0 # Assume 6x6 as default opening
            px_per_mm = cw / 77.0 # 77mm = 7.7cm
            
        ap_w = int(ap_w_mm * px_per_mm)
        ap_h = int(ap_h_mm * px_per_mm)
        
        ax = x + (cw - ap_w) // 2
        ay = y + (ch - ap_h) // 2
        
        # Draw dark "pocket" / CN: 绘制深色遮片袋
        draw.rectangle([ax - 10, ay - 10, ax + ap_w + 10, ay + ap_h + 10], fill=(15, 15, 15))
        
        # 5. EN: Load and Paste Photo / CN: 加载并粘贴照片
        with Image.open(img_path) as img:
            # Handle orientation for better fit
            is_portrait = img.height > img.width
            if is_portrait and cw != 1181: # For 120, swap aperture if portrait
                ap_w, ap_h = ap_h, ap_w
                ax = x + (cw - ap_w) // 2
                ay = y + (ch - ap_h) // 2
            
            img.thumbnail((ap_w, ap_h), Image.Resampling.LANCZOS)
            
            # Center in aperture
            ix = ax + (ap_w - img.width) // 2
            iy = ay + (ap_h - img.height) // 2
            canvas.paste(img, (ix, iy))
            
        # 6. EN: Label-Style Metadata / CN: 标签式元数据
        data = meta.get_data(img_path)
        date_str, exif_str = self.get_clean_exif(data)
        
        # Use a distinct font for labels
        label_size = int(cw * 0.04)
        try:
            from utils.paths import get_asset_path
            f_path = get_asset_path("fonts/gara.ttf")
            l_font = ImageFont.truetype(f_path, label_size)
        except:
            l_font = self.font.font_variant(size=label_size)
            
        # EN: Label background (Simulated sticker) / CN: 标签背景 (模拟贴纸)
        def draw_label(text, pos, font):
            if not text: return
            bbox = font.getbbox(text)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            pad = 8
            # Pale yellow background for "sticker" look
            draw.rectangle([pos[0]-pad, pos[1]-pad, pos[0]+tw+pad, pos[1]+th+pad], fill=(255, 255, 240))
            draw.rectangle([pos[0]-pad, pos[1]-pad, pos[0]+tw+pad, pos[1]+th+pad], outline=(200, 200, 180), width=1)
            draw.text(pos, text, font=font, fill=(30, 30, 30))

        if show_date and date_str:
            draw_label(date_str, (x + 20, y + 20), l_font)
            
        if show_exif and exif_str:
            # Shorten EXIF for labels
            exif_short = exif_str.split("  ")[0] if len(exif_str) > 20 else exif_str
            draw_label(exif_short, (x + 20, y + ch - 60), l_font)
