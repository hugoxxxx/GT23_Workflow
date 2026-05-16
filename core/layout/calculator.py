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
        # --- EN: IMAGE BASE SCALING ---
        # CN: 图片基础缩放基准（锁定在原始图片，不随边框变化）
        img_long_edge = max(w, h)
        ref_factor = img_long_edge / 4500.0
        
        # EN: Initial margin ratios / CN: 初始边距比例
        left_ratio = layout.get('left', layout.get('side', 0.04))
        right_ratio = layout.get('right', layout.get('side', 0.04))
        top_ratio = layout.get('top', 0.04)
        bottom_ratio = layout.get('bottom', 0.13)
        
        inner_bottom_margin = 0
        
        # --- EN: INITIAL MARGIN CALCULATION ---
        if data.get('sprocket_enabled', False):
            px_per_mm = h / 24.0
            margin_px = int(5.5 * px_per_mm)
            top_pad = margin_px
            bottom_splice = margin_px
            side_pad_left = side_pad_right = int(2.0 * px_per_mm)
        else:
            side_pad_left = int(img_long_edge * left_ratio)
            side_pad_right = int(img_long_edge * right_ratio)
            top_pad = int(img_long_edge * top_ratio)
            bottom_splice = int(img_long_edge * bottom_ratio)
            
        new_w = w + side_pad_left + side_pad_right
        new_h = h + top_pad + inner_bottom_margin + bottom_splice
        
        # --- EN: TARGET ASPECT RATIO ADAPTATION ---
        target_ratio_str = str(data.get('target_ratio') or 'Original')
        ratio_match = re.search(r'(\d+):(\d+)', target_ratio_str)
        
        if ratio_match:
            tr_w, tr_h = int(ratio_match.group(1)), int(ratio_match.group(2))
            tr = tr_w / tr_h
            current_ratio = new_w / new_h
            
            if abs(current_ratio - tr) / tr > 0.001:
                if current_ratio < tr:
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
                            
        # --- EN: TYPOGRAPHY CALCULATION (v2.4.1 Migrated) ---
        # CN: 文字排版计算（从 Renderer 迁移）
        main_text = data.get('main_text', '') # Expected pre-prepared
        sub_text = data.get('sub_text', '')
        
        # 1. Resolve Paths
        resolved_main, resolved_sub = "", ""
        if font_resolver:
            manual_main = data.get('font_main_path', 'Default')
            manual_sub = data.get('font_sub_path', 'Default')
            resolved_main, resolved_sub = font_resolver.resolve(
                main_text, sub_text, 
                custom_main=manual_main if manual_main != 'Default' else None,
                custom_sub=manual_sub if manual_sub != 'Default' else None
            )
            
        # 2. Resolve Sizes
        font_base_scale = layout.get('font_scale', 0.032)
        ui_font_scale = data.get('font_scale')
        if ui_font_scale is not None:
            f_val = float(ui_font_scale)
            base_main_font_size = int(f_val * ref_factor) if f_val >= 1.0 else int(img_long_edge * f_val)
        else:
            font_main_scale = layout.get('font_main_scale', font_base_scale)
            base_main_font_size = int(img_long_edge * font_main_scale)
            
        ui_font_sub_px = data.get('font_sub_px')
        if ui_font_sub_px is not None:
            base_sub_font_size = int(float(ui_font_sub_px) * ref_factor)
        else:
            font_sub_scale = layout.get('font_sub_scale', font_base_scale * 0.78)
            base_sub_font_size = int(img_long_edge * font_sub_scale)

        # 3. Spacing & Offsets
        ui_font_spacing = data.get('font_spacing')
        base_spacing = int(float(ui_font_spacing) * ref_factor) if ui_font_spacing is not None else int(base_main_font_size * 1.25)

        ui_font_v_offset = data.get('font_v_offset')
        font_v_offset_px = int(float(ui_font_v_offset) * ref_factor) if ui_font_v_offset is not None else int(img_long_edge * layout.get('font_v_offset', 0))

        return {
            "side_pad_left": side_pad_left,
            "side_pad_right": side_pad_right,
            "top_pad": top_pad,
            "bottom_splice": bottom_splice,
            "new_w": new_w,
            "new_h": new_h,
            "inner_bottom_margin": inner_bottom_margin,
            # Typography results
            "base_main_font_size": base_main_font_size,
            "base_sub_font_size": base_sub_font_size,
            "base_spacing": base_spacing,
            "font_v_offset_px": font_v_offset_px,
            "resolved_main": resolved_main,
            "resolved_sub": resolved_sub,
            "ref_factor": ref_factor
        }
