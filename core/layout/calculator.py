import re

class LayoutCalculator:
    """
    EN: Responsible for calculating image margins, canvas dimensions, and aspect ratio adaptations.
    CN: 负责计算图像边距、画布尺寸以及画幅比例适配。
    """
    
    @staticmethod
    def calculate_layout(w, h, data, layout, h_offset=0, v_offset=0, font_resolver=None):
        """
        EN: Calculates final padding, canvas size, and typography parameters.
        CN: 计算最终边距、画布尺寸以及文字排版相关参数。
        """
        img_long_edge = max(w, h)
        ref_factor = img_long_edge / 4500.0
        
        # 1. Base Margins
        left_ratio = layout.get('left', layout.get('side', 0.04))
        right_ratio = layout.get('right', layout.get('side', 0.04))
        top_ratio = layout.get('top', 0.04)
        bottom_ratio = layout.get('bottom', 0.13)
        
        if data.get('sprocket_enabled', False):
            px_per_mm = h / 24.0
            margin_px = int(5.5 * px_per_mm)
            base_t = base_b = margin_px
            base_l = base_r = int(2.0 * px_per_mm)
        else:
            base_l = int(img_long_edge * left_ratio)
            base_r = int(img_long_edge * right_ratio)
            base_t = int(img_long_edge * top_ratio)
            base_b = int(img_long_edge * bottom_ratio)
            
        # 2. Aspect Ratio Adaptation
        target_ratio_str = str(data.get('target_ratio') or 'Original')
        is_free = "Original" in target_ratio_str or "原图" in target_ratio_str
        
        new_w, new_h = w + base_l + base_r, h + base_t + base_b
        
        if not is_free:
            match = re.search(r'(\d+):(\d+)', target_ratio_str)
            if match:
                tr = int(match.group(1)) / int(match.group(2))
                if (new_w / new_h) < tr: new_w = int(new_h * tr)
                elif (new_w / new_h) > tr: new_h = int(new_w / tr)
        
        # 3. Distribute Extra Space by Offsets
        extra_w = new_w - (w + base_l + base_r)
        extra_h = new_h - (h + base_t + base_b)
        
        l_extra, r_extra, t_extra, b_extra = LayoutCalculator.distribute_extra_space(
            extra_w, extra_h, h_offset, v_offset
        )
        
        side_pad_left = base_l + l_extra
        side_pad_right = base_r + r_extra
        top_pad = base_t + t_extra
        bottom_splice = base_b + b_extra

        # 4. Typography
        main_text, sub_text = data.get('main_text', ''), data.get('sub_text', '')
        resolved_main, resolved_sub = "", ""
        if font_resolver:
            resolved_main, resolved_sub = font_resolver.resolve(
                main_text, sub_text, 
                custom_main=data.get('font_main_path') if data.get('font_main_path') != 'Default' else None,
                custom_sub=data.get('font_sub_path') if data.get('font_sub_path') != 'Default' else None
            )
            
        ui_font_scale = data.get('font_scale')
        base_main_font_size = int(float(ui_font_scale) * ref_factor) if ui_font_scale else int(img_long_edge * layout.get('font_main_scale', 0.032))
        ui_font_sub_px = data.get('font_sub_px')
        base_sub_font_size = int(float(ui_font_sub_px) * ref_factor) if ui_font_sub_px else int(img_long_edge * layout.get('font_sub_scale', 0.025))

        return {
            "w": w, "h": h, "new_w": new_w, "new_h": new_h,
            "side_pad_left": side_pad_left, "side_pad_right": side_pad_right,
            "top_pad": top_pad, "bottom_splice": bottom_splice,
            "inner_bottom_margin": 0, "ref_factor": ref_factor,
            "base_main_font_size": base_main_font_size, "base_sub_font_size": base_sub_font_size,
            "base_spacing": int(base_main_font_size * 1.25),
            "font_v_offset_px": int(float(data.get('font_v_offset', 0)) * ref_factor),
            "resolved_main": resolved_main, "resolved_sub": resolved_sub
        }

    @staticmethod
    def distribute_extra_space(extra_w, extra_h, h_offset, v_offset):
        """
        EN: Core mathematical model for distributing EXTRA space added by ratio adaptation.
        CN: 核心数学模型：分配因比例适配而产生的“额外留白”。
        """
        # Horizontal
        h_ratio = 0.5 + (h_offset / 200.0)
        l = int(extra_w * h_ratio)
        r = extra_w - l
        
        # Vertical
        v = v_offset / 100.0
        dist_v = (0.3 * (1 + v)) if v < 0 else (0.3 + 0.7 * v)
        t = int(extra_h * dist_v)
        b = extra_h - t
        return l, r, t, b

    @staticmethod
    def preview_ui_paddings(w, h, target_ratio_str, base_paddings, h_offset, v_offset):
        """
        EN: Specialized method for UI to predict slider values based on base paddings + offsets.
        CN: 专门供 UI 预测滑块数值的方法（基于基础边距 + 偏移分配）。
        """
        base_l, base_r, base_t, base_b = base_paddings['l'], base_paddings['r'], base_paddings['t'], base_paddings['b']
        new_w, new_h = w + base_l + base_r, h + base_t + base_b
        
        is_free = "Original" in target_ratio_str or "原图" in target_ratio_str
        if not is_free:
            match = re.search(r'(\d+):(\d+)', target_ratio_str)
            if match:
                tr = int(match.group(1)) / int(match.group(2))
                if (new_w / new_h) < tr: new_w = int(new_h * tr)
                else: new_h = int(new_w / tr)
        
        # Re-distribute ONLY the extra space
        extra_w, extra_h = new_w - (w + base_l + base_r), new_h - (h + base_t + base_b)
        l_ex, r_ex, t_ex, b_ex = LayoutCalculator.distribute_extra_space(extra_w, extra_h, h_offset, v_offset)
        
        return {
            "left": base_l + l_ex, "right": base_r + r_ex,
            "top": base_t + t_ex, "bottom": base_b + b_ex
        }
