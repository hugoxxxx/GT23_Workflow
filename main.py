import os
from GT23.metadata import MetadataHandler
from GT23.renderer import FilmRenderer

def run_workflow():
    # --- EN: MODE SELECTION / CN: 模式选择 ---
    print("CN: [SELECT] 请选择模式: 1.胶片项目 (FILM)  2.数码项目 (DIGITAL)")
    choice = input(">>> 输入数字 (默认1): ").strip()
    is_digital = (choice == "2")
    
    # EN: Initialization (Metadata now handles DB logic)
    # CN: 初始化 (Metadata 现在内部处理所有库逻辑)
    meta = MetadataHandler(layout_config='layouts.json', films_config='films.json')
    renderer = FilmRenderer()
    
    input_dir = "photos_in"
    output_dir = "photos_out"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    # EN: Scan images / CN: 扫描图片
    valid_exts = ('.jpg', '.jpeg', '.png')
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    
    if not images:
        print(f"CN: [!] 在 {input_dir} 中没找到图片。")
        return

    print(f"CN: >>> 准备处理 {len(images)} 张照片...")

    for img_name in images:
        img_path = os.path.join(input_dir, img_name)
        
        # 1. EN: Extract & Standardize (Mode-aware)
        # CN: 提取与标准化（感知数码/胶片模式）
        # EN: This handles: Long-word priority, Brand mapping, and Digital noise filter
        # CN: 这里处理了：长词优先匹配、品牌名映射、以及数码噪音过滤
        data = meta.get_data(img_path, is_digital_mode=is_digital)
        
        # 2. EN: Interactive Logic / CN: 交互逻辑
        if not is_digital:
            if not data['Film']:
                print(f"CN: [?] {img_name} 无法识别胶卷 (EXIF 描述为空)")
                user_input = input("   >>> 请手动输入胶卷名称 (或回车跳过): ").strip()
                data['Film'] = user_input.upper() if user_input else "UNKNOWN FILM"
            else:
                # EN: Feedback using the standardized name (Value from JSON)
                # CN: 使用标准化名称提供反馈（来自 JSON 的 Value）
                print(f"CN: [✔] {img_name} -> 匹配成功: {data['Film']}")
        else:
            print(f"CN: [✔] {img_name} -> 数码模式 (ISO {data['ISO']})")

        # 3. EN: Process / CN: 执行渲染
        try:
            renderer.process_image(img_path, data, output_dir)
            print(f"CN: [DONE] 已生成: {img_name}")
        except Exception as e:
            print(f"CN: [ERROR] 处理 {img_name} 失败: {e}")

if __name__ == "__main__":
    run_workflow()