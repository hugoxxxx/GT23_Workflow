import os
import io
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class FilmRenderer:
    """
    EN: Pro-grade renderer with dynamic typography hierarchy.
    CN: 中英双语：具备动态字号层级感的高级渲染器。
    """
    def __init__(self, font_main="assets/fonts/palab.ttf", font_sub="assets/fonts/gara.ttf"):
        self.font_main = font_main
        self.font_sub = font_sub
        self.bg_color = (255, 255, 255)
        self.main_color = (26, 26, 26)   
        self.sub_color = (85, 85, 85)
        self.border_line_color = (238, 238, 238)
        self.logo_dir = "assets/logo"
        self._setup_cairo_dll()

    def _setup_cairo_dll(self):
        """EN: Fix for cairosvg DLL loading on Windows. / CN: 修复 Windows 上 cairosvg 的 DLL 加载。"""
        if sys.platform == "win32":
            # EN: Try to find cairo.dll in conda env Library/bin
            # CN: 尝试在 conda 环境的 Library/bin 中寻找 cairo.dll
            conda_prefix = os.environ.get("CONDA_PREFIX")
            if conda_prefix:
                bin_dir = os.path.join(conda_prefix, "Library", "bin")
                if os.path.isdir(bin_dir) and hasattr(os, "add_dll_directory"):
                    try:
                        os.add_dll_directory(bin_dir)
                    except:
                        pass


    def process_image(self, img_path, data, output_dir, target_long_edge=4500):
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            img = Image.open(img_path)
            if img.mode != "RGB": img = img.convert("RGB")
            img = self._smart_resize(img, target_long_edge)
            w, h = img.size
            
            # --- EN: DATA INTEGRITY CHECK / CN: 数据完整性校验 ---
            # EN: Get layout dict, ensure it has defaults to avoid N/A
            # CN: 获取布局字典，确保有默认值防止出现 N/A
            layout = data.get('layout', {})
            layout_name = layout.get('name', 'CUSTOM')
            side_ratio = layout.get('side', 0.04)
            top_ratio = layout.get('top', side_ratio)
            bottom_ratio = layout.get('bottom', 0.13)
            font_base_scale = layout.get('font_scale', 0.032)
            
            # --- EN: CALCULATE SPACING / CN: 计算物理间距 ---
            side_pad = int(w * side_ratio)
            top_pad = int(w * top_ratio)
            bottom_splice = int(h * bottom_ratio)
            
            new_w, new_h = w + (side_pad * 2), h + top_pad + side_pad + bottom_splice
            
            # --- EN: DRAWING / CN: 绘制流程 ---
            canvas = Image.new("RGB", (new_w, new_h), self.bg_color)
            canvas.paste(img, (side_pad, top_pad))
            draw = ImageDraw.Draw(canvas)
            
            # EN: 1px inner border / CN: 1像素内边框
            draw.rectangle([side_pad, top_pad, side_pad + w, top_pad + h], outline=self.border_line_color, width=1)
            
            # --- EN: TYPOGRAPHY HIERARCHY / CN: 字体层级关联 ---
            main_text, sub_text = self._prepare_strings(data)
            
            # EN: Link sub_size to main_size (0.78 ratio)
            # CN: 将副标题字号关联至主标题 (0.78 黄金比例)
            long_edge = max(new_w, new_h)
            base_main_font_size = int(long_edge * font_base_scale)
            base_sub_font_size = int(base_main_font_size * 0.78)

            # EN: Ensure text fits within the available space
            # CN: 确保文本适应可用空间
            available_width = new_w - (side_pad * 4)  # 减去左右边距和安全余量
            actual_main_size, actual_sub_size = self._adjust_font_sizes_to_fit(
                draw, main_text, sub_text, available_width, 
                base_main_font_size, base_sub_font_size
            )

            self._draw_pro_text(draw, new_w, h, side_pad, top_pad, bottom_splice, 
                            main_text, sub_text, actual_main_size, actual_sub_size, data=data)
            
            # EN: Apply shadow effect for professional film look / CN: 应用阴影效果实现专业胶片感
            final_output = self._apply_pro_shadow(canvas)
            return self._save_with_limit(final_output, img_path, output_dir, data, target_long_edge, layout_name)

        except Exception as e:
            print(f"CN: [×] 渲染程序出错: {e}")
            return False

    def _prepare_strings(self, data):
        """EN: Dual-Engine Typography / CN: 胶片/数码双引擎排版"""
        make_raw = str(data.get('Make') or "").strip()
        model_raw = str(data.get('Model') or "").strip()
        make = make_raw.upper()
        model = model_raw.upper()

        # EN: Deduplicate brand prefix in model (e.g., CANON CANON EOS R6 -> CANON EOS R6)
        # CN: 去重型号里的品牌前缀（示例：CANON CANON EOS R6 -> CANON EOS R6）
        dedup_model = model
        if make and model and model.startswith(make):
            dedup_model = model[len(make):].lstrip(" -_/") or model

        if "HASSELBLAD" in make:
            camera_text = f"HASSELBLAD {dedup_model or model or make}".strip()
        else:
            if make and dedup_model:
                camera_text = f"{make} {dedup_model}".strip()
            else:
                camera_text = dedup_model or make
        
        info_parts = []
        is_digi = data.get('is_digital', False)
        
        # 1. EN: Lens / CN: 镜头
        if data.get('LensModel'): 
            info_parts.append(data['LensModel'])
        
        # 2. EN: Focal Length (Digital only) / CN: 焦距 (仅数码)
        if is_digi and data.get('FocalLength'):
            info_parts.append(data['FocalLength'])
        
        # 3. EN: Exposure (Shutter + Aperture + ISO for Digital)
        # CN: 曝光组件 (快门 + 光圈 + 数码模式下的 ISO)
        params = []
        if data.get('ExposureTimeStr'): params.append(f"{data['ExposureTimeStr']}s")
        if data.get('FNumber'): params.append(f"f/{data['FNumber']}")
        if is_digi and data.get('ISO'): params.append(f"ISO {data['ISO']}")
        if params: info_parts.append(" ".join(params))
        
        # 4. EN: Film (Film mode only) / CN: 胶片名称 (仅胶片模式)
        if not is_digi:
            film_name = str(data.get('Film') or "").upper()
            if film_name: info_parts.append(film_name)
        
        return camera_text, "  |  ".join(info_parts)

    def _draw_pro_text(self, draw, new_w, h, side_pad, top_pad, bottom_splice, main_text, sub_text, m_size, s_size, data=None):
        # EN: Vertical center of the white area / CN: 白色区域垂直中心
        base_y = top_pad + h + (side_pad + bottom_splice) // 2
        
        main_draw_pos = (new_w // 2, base_y - int(bottom_splice * 0.15))
        sub_draw_pos = (new_w // 2, base_y + int(bottom_splice * 0.28))

        # --- EN: CAMERA LOGO RENDERING / CN: 相机 LOGO 渲染 ---
        logo_drawn = False
        if data:
            make = str(data.get('Make') or "").strip()
            model = str(data.get('Model') or "").strip()
            logo_path = self._find_logo_path(make, model)
            
            if logo_path:
                try:
                    import cairosvg
                    from .typo_engine import TypoEngine
                    resolved_main = TypoEngine._resolve_font_path(self.font_main)
                    main_font = self._get_font(resolved_main, m_size)
                    
                    # EN: Calculate typical font height for scaling / CN: 计算典型字体高度用于缩放
                    ascent, descent = main_font.getmetrics()
                    target_h = ascent + descent
                    
                    png_data = cairosvg.svg2png(url=logo_path, output_height=target_h)
                    logo_img = Image.open(io.BytesIO(png_data))
                    
                    # EN: Crop to actual content to ensure perfect centering
                    bbox = logo_img.getbbox()
                    if bbox:
                        logo_img = logo_img.crop(bbox)

                    # EN: Center horizontally, align vertically with text pos
                    # CN: 水平居中，垂直与文字位置对齐
                    logo_x = (new_w - logo_img.width) // 2
                    logo_y = main_draw_pos[1] - logo_img.height // 2
                    
                    # EN: Paste with alpha mask / CN: 带透明蒙版粘贴
                    draw._image.paste(logo_img, (logo_x, logo_y), logo_img)
                    
                    # DEBUG: Draw center line
                    # draw.line([(new_w // 2, top_pad + h), (new_w // 2, new_h)], fill="red", width=2)

                    logo_drawn = True
                except Exception as e:
                    print(f"CN: [!] Logo 渲染失败 fallback to text: {e}")

        # --- EN: ZEISS T* HIGHLIGHT / CN: 蔡司 T* 红色高亮 ---
        # Zeiss red color: #ed1f25 -> (237, 31, 37)
        sub_colors = self.sub_color
        if "T*" in sub_text:
            sub_colors = [self.sub_color] * len(sub_text)
            zeiss_red = (237, 31, 37)
            i = 0
            while i < len(sub_text) - 1:
                if sub_text[i:i+2] == "T*":
                    sub_colors[i] = zeiss_red
                    sub_colors[i+1] = zeiss_red
                    i += 2
                else:
                    i += 1

        # EN: Text drawing / CN: 文字绘制
        try:
            from .typo_engine import TypoEngine
            if not logo_drawn:
                TypoEngine.draw_text(draw, main_draw_pos, main_text, self.font_main, m_size, self.main_color)
            TypoEngine.draw_text(draw, sub_draw_pos, sub_text, self.font_sub, s_size, sub_colors)
        except Exception as e:
            if not logo_drawn:
                draw.text(main_draw_pos, main_text, fill="black", anchor="mm")
            # Fallback for sub_text: just use the base sub_color as a single fill
            draw.text(sub_draw_pos, sub_text, fill=self.sub_color, anchor="mm")


    def _find_logo_path(self, make, model):
        """EN: Case-insensitive logo lookup. / CN: 不区分大小写的 Logo 查找。"""
        if not os.path.exists(self.logo_dir): return None
        
        # EN: Common naming patterns / CN: 常见命名匹配模式
        search_names = []
        if make and model:
            search_names.append(f"{make}-{model}.svg".upper())
            search_names.append(f"{make}_{model}.svg".upper())
            search_names.append(f"{make}{model}.svg".upper())
        if model:
            search_names.append(f"{model}.svg".upper())
        if make:
            search_names.append(f"{make}.svg".upper())
            
        try:
            files = os.listdir(self.logo_dir)
            file_map = {f.upper(): f for f in files if f.lower().endswith(".svg")}
            
            for name in search_names:
                if name in file_map:
                    return os.path.join(self.logo_dir, file_map[name])
        except:
            pass
        return None

    def _smart_resize(self, img, target):
        w, h = img.size
        scale = target / max(w, h)
        return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    def _apply_pro_shadow(self, canvas):
        shadow_margin = 80
        # EN: Use transparent black (0,0,0,0) to avoid white corners on compression
        # CN: 使用透明黑 (0,0,0,0) 作为基色，防止压缩后出现白角
        full_canvas = Image.new("RGBA", (canvas.width + shadow_margin, canvas.height + shadow_margin), (0, 0, 0, 0))
        shadow_mask = Image.new("RGBA", canvas.size, (0, 0, 0, 140))
        shadow_pos = (shadow_margin // 2, shadow_margin // 2 + 10)
        full_canvas.paste(shadow_mask, shadow_pos)
        full_canvas = full_canvas.filter(ImageFilter.GaussianBlur(radius=20))
        canvas_rgba = canvas.convert("RGBA")
        full_canvas.paste(canvas_rgba, (shadow_margin // 2, shadow_margin // 2), canvas_rgba)
        return full_canvas

    def _save_with_limit(self, img, original_path, output_dir, data, current_res, layout_name):
        # EN: Default to JPG for better social media compatibility, fallback to PNG if requested
        # CN: 默认输出 JPG 以获得更好的社交平台兼容性（自动硬化阴影）
        ext = ".jpg"
        out_name = f"GT23_{os.path.splitext(os.path.basename(original_path))[0]}{ext}"
        save_path = os.path.join(output_dir, out_name)
        
        try:
            if img.mode == 'RGBA':
                # EN: Flatten onto white background for JPEG
                # CN: 为 JPG 复合纯白底色，强制“硬化”阴影效果
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3]) # Use alpha channel as mask
                img_to_save = background
            else:
                img_to_save = img

            img_to_save.save(save_path, "JPEG", quality=95, subsampling=0)
        except Exception as e:
            print(f"CN: [!] JPG 保存失败，回退至 PNG: {e}")
            save_path = save_path.replace(".jpg", ".png")
            out_name = out_name.replace(".jpg", ".png")
            img.save(save_path, "PNG", optimize=True)

        f_size = os.path.getsize(save_path) / (1024 * 1024)
        # EN: 10MB limit is generous for JPG, no longer need aggressive downsampling
        # CN: 对于 JPG，10MB 限制非常充裕，不再需要激进的递归降采样
        if f_size > 10.0:
            print(f"CN: [!] 文件较大 ({f_size:.1f}MB)，正尝试以稍低质量重新保存...")
            img_to_save.save(save_path, "JPEG", quality=88, subsampling=0)
        
        # EN: Log the identified format clearly / CN: 明确记录识别出的画幅
        print(f"CN: [✔] 渲染完成: {out_name} | 画幅: {layout_name}")
        return out_name
    
    def _adjust_font_sizes_to_fit(self, draw, main_text, sub_text, available_width, base_main_size, base_sub_size):
        """
        调整字体大小使其适应可用宽度
        使用与 TypoEngine 相同的字体路径解析，确保测量准确。
        """
        # EN: Use same path resolution as TypoEngine to ensure fonts match
        # CN: 使用与 TypoEngine 相同的路径解析，确保字体一致
        from .typo_engine import TypoEngine
        resolved_main = TypoEngine._resolve_font_path(self.font_main)
        resolved_sub  = TypoEngine._resolve_font_path(self.font_sub)

        # 创建临时绘图对象来测量文本宽度
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 检查主文本宽度
        main_font = self._get_font(resolved_main, base_main_size)
        main_bbox = temp_draw.textbbox((0, 0), main_text, font=main_font)
        main_text_width = main_bbox[2] - main_bbox[0]
        
        main_scale_factor = min(1.0, available_width / main_text_width) if main_text_width > 0 else 1.0
        
        # 检查副文本宽度（使用与 TypoEngine.draw_text 相同的 textlength 累加）
        sub_font = self._get_font(resolved_sub, base_sub_size)
        sub_text_width = sum(temp_draw.textlength(c, font=sub_font) for c in list(sub_text))
        
        sub_scale_factor = min(1.0, available_width / sub_text_width) if sub_text_width > 0 else 1.0
        
        # 使用最小缩放因子确保两个文本都不会超出边界
        final_scale_factor = min(main_scale_factor, sub_scale_factor)
        
        final_main_size = max(10, int(base_main_size * final_scale_factor))  # 最小字体大小为10
        final_sub_size = max(8, int(base_sub_size * final_scale_factor))   # 最小字体大小为8
        
        return final_main_size, final_sub_size

    def _get_font(self, font_path, font_size):
        """
        获取字体对象，如果指定字体不存在则使用默认字体
        """
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
            else:
                return ImageFont.load_default()
        except:
            return ImageFont.load_default()