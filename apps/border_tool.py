# apps/border_tool.py
import os
import sys

# EN: Import from core / CN: 从 core 导入核心模块
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer

# EN: Get working directory (where photos_in/out should be)
# CN: 获取工作目录（photos_in/out 应该所在的位置）
def get_working_dir():
    """EN: Returns the directory where exe runs or script is located.
       CN: 返回 exe 运行的目录或脚本所在目录。"""
    if getattr(sys, 'frozen', False):
        # Running as exe: use executable's directory
        return os.path.dirname(sys.executable)
    else:
        # Running as script: use project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir) 

def run_border_tool():
    """
    EN: Main logic for the Border Tool (Standardized with manual matching).
    CN: 中英双语：边框工具主逻辑（支持手动输入标准化）。
    """
    try:
        print("\n" + "="*40)
        print("EN: >>> Running: Border Tool | CN: >>> 正在运行: 边框美化工具")
        print("="*40)
        
        # EN: Mode selection / CN: 模式选择
        print("EN: [SELECT] 1.Film Project (FILM)  2.Digital Project (DIGITAL)")
        print("CN: [SELECT] 1.胶片项目 (FILM)  2.数码项目 (DIGITAL)")
        mode_choice = input("EN: Enter number (default 1) | CN: 输入数字 (默认1) >>> ").strip()
        is_digital = (mode_choice == "2")

        # 2. EN: Initialization / CN: 初始化
        # EN: MetadataHandler now handles all film library logic
        # CN: MetadataHandler 现在负责所有的胶片库逻辑
        meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
        renderer = FilmRenderer()
        
        working_dir = get_working_dir()
        input_dir = os.path.join(working_dir, "photos_in")
        output_dir = os.path.join(working_dir, "photos_out")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 3. EN: File scanning / CN: 扫描文件
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            print(f"EN: [!] No images in folder {input_dir} | CN: [!] 文件夹 {input_dir} 中没有图片。")
            return

        print(f"EN: >>> Preparing to process {len(images)} photos... | CN: >>> 准备处理 {len(images)} 张照片...")

        # 4. EN: Batch processing / CN: 批量处理
        for img_name in images:
            img_path = os.path.join(input_dir, img_name)
            
            # EN: Extract / CN: 提取 (已经包含了自动匹配逻辑)
            data = meta.get_data(img_path, is_digital_mode=is_digital)
            
            # EN: Handle interactive input for Film / CN: 胶片模式下的手动输入
            if not is_digital and not data['Film']:
                print(f"EN: [?] {img_name} film not recognized | CN: [?] {img_name} 无法识别胶卷")
                user_input = input("EN: Enter film name | CN: 请手动输入胶卷名称 >>> ").strip()
                
                # --- EN: CORE FIX / CN: 核心修复处 ---
                # EN: Use match_film to standardize user input
                # CN: 使用 match_film 标准化用户输入
                if user_input:
                    data['Film'] = meta.match_film(user_input)
                    print(f"EN: [✔] Matched standard name: {data['Film']} | CN: [✔] 已校对标准名: {data['Film']}")
                else:
                    data['Film'] = "UNKNOWN FILM"
            
            # EN: Final Rendering / CN: 最终渲染
            try:
                renderer.process_image(img_path, data, output_dir)
                print(f"EN: [DONE] Generated: {img_name} | CN: [DONE] 已生成: {img_name}")
            except Exception as e:
                print(f"EN: [ERROR] {img_name} failed: {e} | CN: [ERROR] {img_name} 失败: {e}")
                import traceback
                traceback.print_exc()

        print("\nEN: [FINISH] All border processing complete! | CN: [FINISH] 边框处理全部完成！")
        
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


def process_border_batch(input_dir, output_dir, is_digital=False, manual_film=None, progress_callback=None, lang="zh", custom_layout=None, manual_exif=None):
    """
    EN: Pure logic function for batch border processing (GUI-friendly).
    CN: 批量边框处理纯逻辑函数（GUI友好）。
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        is_digital: Digital mode flag
        manual_film: Manual film selection (keyword)
        progress_callback: Function(current, total, filename) for progress updates
        lang: Language for messages ("zh" or "en")
        custom_layout: Dict with custom params: {"side": 0.04, "top": 0.04, "bottom": 0.13, "font_scale": 0.032}
        manual_exif: Dict with manual exif overrides (Make, Model, LensModel, ExposureTimeStr, FNumber, ISO)
    
    Returns:
        {
            'success': bool,
            'processed': int,
            'failed': list[(filename, error)],
            'message': str
        }
    """
    try:
        # EN: Localized message helper / CN: 本地化消息助手
        def _t(zh_text, en_text):
            return zh_text if lang == "zh" else en_text

        # EN: Initialization / CN: 初始化
        meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
        renderer = FilmRenderer()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # EN: File scanning / CN: 扫描文件
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not images:
            return {
                'success': False,
                'processed': 0,
                'failed': [],
                'message': _t("文件夹中没有图片", "No images in folder")
            }
        
        total = len(images)
        processed = 0
        failed = []
        
        # EN: Batch processing / CN: 批量处理
        for idx, img_name in enumerate(images, 1):
            img_path = os.path.join(input_dir, img_name)
            
            try:
                # EN: Extract metadata / CN: 提取元数据
                if manual_film:
                    # EN: Use manual film selection / CN: 使用手动胶片选择
                    data = meta.get_data(img_path, is_digital_mode=is_digital, manual_film=manual_film)
                else:
                    # EN: Auto-detect / CN: 自动检测
                    data = meta.get_data(img_path, is_digital_mode=is_digital)
                
                # EN: Apply custom layout params if provided / CN: 如果提供了自定义布局参数则应用
                if custom_layout:
                    if 'layout' in data:
                        data['layout'].update(custom_layout)
                    else:
                        data['layout'] = custom_layout
                
                # EN: Apply manual EXIF overrides / CN: 应用手动 EXIF 覆盖
                if manual_exif:
                    for k, v in manual_exif.items():
                        if v:
                            data[k] = v
                
                # EN: Final Rendering / CN: 最终渲染
                renderer.process_image(img_path, data, output_dir)
                processed += 1
                
                # EN: Report progress / CN: 报告进度
                if progress_callback:
                    progress_callback(idx, total, img_name)
                    
            except Exception as e:
                failed.append((img_name, str(e)))
                if progress_callback:
                    progress_callback(idx, total, _t(f"{img_name}（失败: {e}）", f"{img_name} (Failed: {e})"))
        
        # EN: Return result / CN: 返回结果
        return {
            'success': len(failed) < total,  # Success if at least one processed
            'processed': processed,
            'failed': failed,
            'message': _t(f"已处理 {processed}/{total} 张照片", f"Processed {processed}/{total} photos")
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'processed': 0,
            'failed': [],
            'message': f"{_t('错误', 'Error')}: {e}\n{traceback.format_exc()}"
        }


if __name__ == "__main__":
    run_border_tool()