from PIL import Image, ImageFilter

class ShadowEngine:
    """
    EN: High-fidelity diffuse shadow rendering engine.
    CN: 高保真漫反射阴影渲染引擎。
    """
    
    @staticmethod
    def apply_pro_shadow(canvas, radius=20):
        """
        EN: Apply multi-layer Gaussian diffuse shadow.
        CN: 应用多层高斯漫反射阴影。
        """
        shadow_margin = 80
        # EN: Use transparent black (0,0,0,0) to avoid white corners on compression
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (0, 0, 0, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 140))
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 10)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.GaussianBlur(radius=radius))
        
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas

    @staticmethod
    def apply_pro_shadow_fast(canvas, radius=5):
        """
        EN: Fast BoxBlur shadow for real-time previews.
        CN: 预览专用快速 BoxBlur 阴影。
        """
        shadow_margin = 60
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (0, 0, 0, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 120))
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 6)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.BoxBlur(radius=radius))
        
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas

    @staticmethod
    def apply_floating_shadow(canvas, img, x, y):
        """
        EN: Draw premium floating shadows using rounded masks and multi-layer composites.
        CN: 使用圆角遮罩和多层复合绘制高级悬浮投影效果。
        """
        from PIL import Image, ImageFilter, ImageDraw, ImageChops
        
        # 0. EN: Calculate shadow scale factor
        long_edge = max(img.width, img.height)
        sf = long_edge / 2000.0
        
        # --- 1. EN: OFF-SCREEN SHADOW COMPOSITE ---
        max_blur = int(200 * sf)
        margin = max_blur * 4
        shadow_buf = Image.new("RGBA", (img.width + margin * 2, img.height + margin * 2), (0, 0, 0, 0))
        
        def draw_layer(radius, opacity, off_x, off_y, spread_neg, fade_strength=0.0):
            nonlocal shadow_buf
            s_w = max(10, img.width - int(spread_neg * sf) * 2)
            s_h = max(10, img.height - int(spread_neg * sf) * 2)
            
            mask_l = Image.new("L", (s_w, s_h), 0)
            d = ImageDraw.Draw(mask_l)
            r = int(60 * sf)
            d.rounded_rectangle([0, 0, s_w, s_h], radius=r, fill=255)
            
            if fade_strength > 0:
                h_grad = Image.new("L", (s_w, 1))
                for x_px in range(s_w): 
                    h_grad.putpixel((x_px, 0), int(255 * (1.0 - (x_px / s_w) * fade_strength)))
                h_grad = h_grad.resize((s_w, s_h))
                
                v_grad = Image.new("L", (1, s_h))
                for y_px in range(s_h):
                    v_grad.putpixel((0, y_px), int(255 * (1.0 - (y_px / s_h) * fade_strength)))
                v_grad = v_grad.resize((s_w, s_h))
                
                grad = ImageChops.multiply(h_grad, v_grad)
                mask_l = ImageChops.multiply(mask_l, grad)

            mask_cv = Image.new("RGBA", (s_w, s_h), (0, 0, 0, 0))
            mask_cv.putalpha(Image.eval(mask_l, lambda x: int(x * opacity / 255)))
            
            pos_x = margin + int(spread_neg * sf) + int(off_x * sf)
            pos_y = margin + int(spread_neg * sf) + int(off_y * sf)
            
            layer = Image.new("RGBA", shadow_buf.size, (0, 0, 0, 0))
            layer.paste(mask_cv, (pos_x, pos_y))
            layer = layer.filter(ImageFilter.GaussianBlur(radius=radius))
            
            shadow_buf = Image.alpha_composite(shadow_buf, layer)

        # Layer A: Ambient Foundation
        draw_layer(radius=int(180 * sf), opacity=100, off_x=0, off_y=70, spread_neg=20, fade_strength=0.15)
        # Layer B: Supporting Float
        draw_layer(radius=int(80 * sf), opacity=140, off_x=0, off_y=40, spread_neg=10, fade_strength=0.0)
        # Layer C: Tactile Core
        draw_layer(radius=int(20 * sf), opacity=180, off_x=0, off_y=15, spread_neg=0, fade_strength=0.0)
        
        canvas.paste(shadow_buf, (x - margin, y - margin), shadow_buf)
        canvas.paste(img, (x, y))
