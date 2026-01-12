# apps/border_tool.py
import os
import sys

# EN: Get project root / CN: 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# EN: Import from core / CN: 从 core 导入核心模块
from core.metadata import MetadataHandler
from core.renderer import FilmRenderer 

def run_border_tool():
    """
    EN: Main logic for the Border Tool (Standardized with manual matching).
    CN: 中英双语：边框工具主逻辑（支持手动输入标准化）。
    """
    print("\n" + "="*40)
    print("CN: >>> 正在运行: 边框美化工具 (Border Tool)")
    print("="*40)
    
    # 1. EN: Mode selection / CN: 模式选择
    print("CN: [SELECT] 1.胶片项目 (FILM)  2.数码项目 (DIGITAL)")
    mode_choice = input(">>> 输入数字 (默认1): ").strip()
    is_digital = (mode_choice == "2")

    # 2. EN: Initialization / CN: 初始化
    # EN: MetadataHandler now handles all film library logic
    # CN: MetadataHandler 现在负责所有的胶片库逻辑
    meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
    renderer = FilmRenderer()
    
    input_dir = os.path.join(project_root, "photos_in")
    output_dir = os.path.join(project_root, "photos_out")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 3. EN: File scanning / CN: 扫描文件
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        print(f"CN: [!] 文件夹 {input_dir} 中没有图片。")
        return

    print(f"CN: >>> 准备处理 {len(images)} 张照片...")

    # 4. EN: Batch processing / CN: 批量处理
    for img_name in images:
        img_path = os.path.join(input_dir, img_name)
        
        # EN: Extract / CN: 提取 (已经包含了自动匹配逻辑)
        data = meta.get_data(img_path, is_digital_mode=is_digital)
        
        # EN: Handle interactive input for Film / CN: 胶片模式下的手动输入
        if not is_digital and not data['Film']:
            print(f"CN: [?] {img_name} 无法识别胶卷")
            user_input = input("   >>> 请手动输入胶卷名称: ").strip()
            
            # --- EN: CORE FIX / CN: 核心修复处 ---
            # EN: Use match_film to standardize user input
            # CN: 使用 match_film 标准化用户输入
            if user_input:
                data['Film'] = meta.match_film(user_input)
                print(f"CN: [✔] 已校对标准名: {data['Film']}")
            else:
                data['Film'] = "UNKNOWN FILM"
        
        # EN: Final Rendering / CN: 最终渲染
        try:
            renderer.process_image(img_path, data, output_dir)
            print(f"CN: [DONE] 已生成: {img_name}")
        except Exception as e:
            print(f"CN: [ERROR] {img_name} 失败: {e}")

    print("\nCN: [FINISH] 边框处理全部完成！")

if __name__ == "__main__":
    run_border_tool()