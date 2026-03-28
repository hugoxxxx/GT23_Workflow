# contact_sheet.py
import os
import sys
from core.metadata import MetadataHandler
from core.renderers.renderer_66 import Renderer66
from core.renderers.renderer_645 import Renderer645
from core.renderers.renderer_67 import Renderer67
from core.renderers.renderer_135 import Renderer135
from core.renderers.renderer_135hf import Renderer135HF

class ContactSheetPro:
    def __init__(self):
        self.meta = MetadataHandler()
        self.renderers = {
            "66": Renderer66(), 
            "645": Renderer645(), 
            "67": Renderer67(), 
            "135": Renderer135(),
            "135HF": Renderer135HF()
        }

    def run(self):
        try:
            # EN: Get working directory for photos_in/out
            # CN: 获取 photos_in/out 的工作目录
            if getattr(sys, 'frozen', False):
                working_dir = os.path.dirname(sys.executable)
            else:
                working_dir = os.getcwd()
            
            input_dir = os.path.join(working_dir, "photos_in")
            output_dir = os.path.join(working_dir, "photos_out")
            img_paths = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            if not img_paths: return

            # 1. 胶片手动匹配与元数据预提取
            sample_data = self.meta.get_data(img_paths[0])
            user_keyword = None # 用于接力的关键字

            if not sample_data.get('Film'):
                print("EN: [?] Film not recognized, starting manual matching... | CN: [?] 无法识别胶卷，启动手动匹配...")
                user_keyword = input("EN: Enter keyword (e.g. p400) | CN: 请输入关键字 (如 p400) >>> ").strip()
                # EN: Re-extract using manual_film to get full bundle (EdgeCode/Color)
                # CN: 使用手动关键字重新提取，确保拿到匹配库后的 EdgeCode 和颜色
                sample_data = self.meta.get_data(img_paths[0], manual_film=user_keyword)

            # 2. 调度渲染器执行
            layout_key = self.meta.detect_batch_layout(img_paths)
            cfg = self.meta.get_contact_layout(layout_key)
            renderer = self.renderers.get(layout_key, self.renderers["66"])
            
            canvas, user_emulsion = renderer.prepare_canvas(cfg.get("canvas_w", 4800), cfg.get("canvas_h", 6000))
            # EN: Inject sample_data directly to the renderer
            # CN: 将已经确定好的 sample_data 直接注入渲染器，实现整卷信息统一
            canvas = renderer.render(canvas, img_paths, cfg, self.meta, user_emulsion, sample_data=sample_data)

            # 3. 保存 (无页脚)
            if not os.path.exists(output_dir): os.makedirs(output_dir)
            save_path = os.path.join(output_dir, f"ContactSheet_{layout_key}.jpg")
            canvas.save(save_path, quality=95)
            print(f"EN: [✔] Contact sheet saved to: {save_path} | CN: [✔] 索引页已保存至: {save_path}")
            
        except Exception as e:
            print("\n" + "="*60)
            print("CN: [!] 程序运行出错 / EN: Program Error")
            print("="*60)
            print(f"错误信息 / Error: {e}")
            print("\n详细错误信息 / Detailed Error:")
            import traceback
            traceback.print_exc()
            print("\n" + "-"*60)
            print("CN: 如果问题持续存在，请联系开发者：")
            print("EN: If the problem persists, please contact:")
            print("📧 Email: xjames007@gmail.com")
            print("-"*60)
            input("\n按回车键退出 / Press Enter to exit...")
    
    def generate(self, input_dir, output_dir, format=None, manual_film=None, emulsion_number=None, orientation=None, lang="zh", progress_callback=None, show_date=True, show_exif=True, sort_method="name", reverse=False):
        """
        EN: Pure logic function for contact sheet generation (GUI-friendly).
        CN: 底片索引生成纯逻辑函数（GUI友好）。
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            format: Format type ("66", "645", "67", "135" or long names like "645_6x8_43", or None for auto-detect)
            manual_film: Manual film keyword
            emulsion_number: User-provided emulsion number
            orientation: For 645 format: "L" (landscape/vertical strip) or "P" (portrait/horizontal strip)
            progress_callback: Function(message) for progress updates
            sort_method: "name" (filename) or "date" (EXIF date)
            reverse: Whether to reverse sorting order
        
        Returns:
            {
                'success': bool,
                'output_path': str,
                'layout_detected': str,
                'frames_count': int,
                'message': str
            }
        """
        try:
            # EN: Localized message helper / CN: 本地化消息助手
            def _t(zh_text, en_text):
                return zh_text if lang == "zh" else en_text
            
            # EN: Map long format names to short renderer keys / CN: 将长格式名映射到短渲染器key
            format_map = {
                "6x6": "66",
                "6x7_4x5": "67",
                "645_6x8_43": "645",
                "135_6x9": "135",
                "135HF": "135HF",
                "PANORAMIC": "135"  # EN: Fallback panoramic to 135 / CN: 全景降级为135
            }
            
            if format and format in format_map:
                format = format_map[format]

            if progress_callback:
                progress_callback(_t("正在扫描文件...", "Scanning files..."))
            
            # EN: Get image paths / CN: 获取图片路径
            raw_imgs = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not raw_imgs:
                return {
                    'success': False,
                    'output_path': '',
                    'layout_detected': '',
                    'frames_count': 0,
                    'message': _t("未找到图片", "No images found")
                }

            # EN: Apply sorting / CN: 执行排序
            if sort_method == "date":
                if progress_callback:
                    progress_callback(_t("正在按拍摄时间排序...", "Sorting by date..."))
                # EN: Sort by EXIF date, fallback to filename if dates are equal or missing
                # CN: 按拍摄日期排序，如果日期相同或缺失则回序至文件名
                def get_date_key(path):
                    try:
                        d = self.meta.get_data(path)
                        return (d.get("DateTime", "9999:99:99 99:99:99"), path)
                    except:
                        return ("9999:99:99 99:99:99", path)
                img_paths = sorted(raw_imgs, key=get_date_key, reverse=reverse)
            else:
                # EN: Default sorting by filename / CN: 默认按文件名排序
                img_paths = sorted(raw_imgs, reverse=reverse)
            if not img_paths:
                return {
                    'success': False,
                    'output_path': '',
                    'layout_detected': '',
                    'frames_count': 0,
                    'message': _t("未找到图片", "No images found")
                }
            
            if progress_callback:
                progress_callback(_t(f"找到 {len(img_paths)} 张图片", f"Found {len(img_paths)} images"))
            
            # EN: 1. Film matching and metadata extraction / CN: 1. 胶片匹配与元数据提取
            # EN: If manual_film is specified, use it directly (priority over auto-detection)
            # CN: 如果指定了手动胶片，直接使用（优先于自动识别）
            if manual_film:
                if progress_callback:
                    progress_callback(_t(f"使用手动胶片: {manual_film}", f"Using manual film: {manual_film}"))
                sample_data = self.meta.get_data(img_paths[0], manual_film=manual_film)
            else:
                # EN: Auto-detect from EXIF / CN: 从EXIF自动识别
                sample_data = self.meta.get_data(img_paths[0])
            
            # EN: 2. Layout detection / CN: 2. 画幅检测
            if format:
                layout_key = format
                if progress_callback:
                    progress_callback(_t(f"使用指定画幅: {layout_key}", f"Using specified format: {layout_key}"))
            else:
                layout_key = self.meta.detect_batch_layout(img_paths)
                # EN: Map long format names to short renderer keys / CN: 将长格式名映射到短渲染器key
                if layout_key in format_map:
                    layout_key = format_map[layout_key]
                if progress_callback:
                    progress_callback(_t(f"自动检测画幅: {layout_key}", f"Auto-detected format: {layout_key}"))

            # EN: Fallback if detection failed / CN: 检测失败回退
            if not layout_key:
                layout_key = "66"
                if progress_callback:
                    progress_callback(_t("画幅检测失败，回退为 66", "Format detection failed, fallback to 66"))

            # EN: Ensure 645 never blocks: default orientation when missing / CN: 确保 645 不阻塞：缺省方向默认 L
            if layout_key == "645" and not orientation:
                orientation = "L"
            
            cfg = self.meta.get_contact_layout(layout_key)
            renderer = self.renderers.get(layout_key, self.renderers["66"])
            
            # EN: 3. Render canvas / CN: 3. 渲染画布
            if progress_callback:
                progress_callback(_t("正在渲染索引页...", "Rendering contact sheet..."))
            
            # EN: Pass emulsion_number to prepare_canvas to avoid input() in GUI mode / CN: 传递乳剂号到prepare_canvas避免GUI模式下的input()
            canvas, user_emulsion = renderer.prepare_canvas(
                cfg.get("canvas_w", 4800), 
                cfg.get("canvas_h", 6000),
                emulsion_number=emulsion_number
            )
            
            # EN: Pass orientation to render for 645 format to avoid input() in GUI mode / CN: 传递方向参数给645画幅渲染器避免GUI模式下的input()
            canvas = renderer.render(
                canvas,
                img_paths,
                cfg,
                self.meta,
                user_emulsion,
                sample_data=sample_data,
                orientation=orientation,
                show_date=show_date,
                show_exif=show_exif
            )
            
            # EN: 4. Save output / CN: 4. 保存输出
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            save_path = os.path.join(output_dir, f"ContactSheet_{layout_key}.jpg")
            canvas.save(save_path, quality=95)
            
            if progress_callback:
                progress_callback(_t(f"已保存至: {save_path}", f"Saved to: {save_path}"))
            
            return {
                'success': True,
                'output_path': save_path,
                'layout_detected': layout_key,
                'frames_count': len(img_paths),
                'message': _t("成功", "Success")
            }
            
        except Exception as e:
            import traceback
            return {
                'success': False,
                'output_path': '',
                'layout_detected': '',
                'frames_count': 0,
                'message': f"{_t('错误', 'Error')}: {e}\n{traceback.format_exc()}"
            }

if __name__ == "__main__":
    ContactSheetPro().run()