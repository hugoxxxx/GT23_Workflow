import re

class LayoutCalculator:
    """
    EN: Responsible for calculating image margins, canvas dimensions, and aspect ratio adaptations.
    CN: 负责计算图像边距、画布尺寸以及画幅比例适配。
    """
    
    @staticmethod
    def calculate_layout(w, h, data, layout, h_offset=0, v_offset=0):
        """
        EN: Calculates final padding and canvas size based on parameters.
        CN: 根据参数计算最终边距和画布尺寸。
        """
        # EN: Initial margin ratios / CN: 初始边距比例
        left_ratio = layout.get('left', layout.get('side', 0.04))
        right_ratio = layout.get('right', layout.get('side', 0.04))
        top_ratio = layout.get('top', 0.04)
        bottom_ratio = layout.get('bottom', 0.13)
        
        inner_bottom_margin = 0
        
        # --- EN: INITIAL MARGIN CALCULATION ---
        # EN: Note: Sprocket logic will be moved to specialized module in Step 7.
        # EN: For now, we keep the basic logic here and refine later.
        if data.get('sprocket_enabled', False):
            px_per_mm = h / 24.0
            margin_px = int(5.5 * px_per_mm)
            top_pad = margin_px
            bottom_splice = margin_px
            side_pad_left = side_pad_right = int(2.0 * px_per_mm)
        else:
            long_edge = max(w, h)
            side_pad_left = int(long_edge * left_ratio)
            side_pad_right = int(long_edge * right_ratio)
            top_pad = int(long_edge * top_ratio)
            bottom_splice = int(long_edge * bottom_ratio)
            
        new_w = w + side_pad_left + side_pad_right
        new_h = h + top_pad + inner_bottom_margin + bottom_splice
        
        # --- EN: TARGET ASPECT RATIO ADAPTATION ---
        target_ratio_str = str(data.get('target_ratio') or 'Original')
        
        # EN: Identify ratio pattern (e.g. 4:5). If not found, treat as Original.
        # CN: 识别比例模式（如 4:5）。如果匹配不到数字比例，则视为“原图”模式。
        ratio_match = re.search(r'(\d+):(\d+)', target_ratio_str)
        
        if ratio_match:
            tr_w, tr_h = int(ratio_match.group(1)), int(ratio_match.group(2))
            tr = tr_w / tr_h
            current_ratio = new_w / new_h
            
            # EN: 0.1% epsilon for float stability
            if abs(current_ratio - tr) / tr > 0.001:
                if current_ratio < tr:
                    # EN: Add horizontal padding
                    target_new_w = int(new_h * tr)
                    diff_w = target_new_w - new_w
                    if diff_w > 0:
                        h_off = h_offset / 100.0
                        dist_h = 0.5 + (h_off / 2.0)
                        l_extra = int(diff_w * dist_h)
                        side_pad_left += l_extra
                        side_pad_right += (diff_w - l_extra)
                        new_w = target_new_w
                elif current_ratio > tr:
                    # EN: Add vertical padding
                    target_new_h = int(new_w / tr)
                    diff_h = target_new_h - new_h
                    if diff_h > 0:
                        TEXT_RESERVE = 550
                        v = v_offset / 100.0
                        shift_budget = max(0, diff_h - TEXT_RESERVE)
                        dist_v = (0.3 * (1 + v)) if v < 0 else (0.3 + 0.7 * v)
                        top_extra = int(shift_budget * dist_v)
                        top_pad += top_extra
                        bottom_splice += (diff_h - top_extra)
                        new_h = target_new_h
                            
        return {
            "side_pad_left": side_pad_left,
            "side_pad_right": side_pad_right,
            "top_pad": top_pad,
            "bottom_splice": bottom_splice,
            "new_w": new_w,
            "new_h": new_h,
            "inner_bottom_margin": inner_bottom_margin
        }
