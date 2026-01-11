import os
from GT23.metadata import MetadataHandler
from GT23.film_db import FilmDatabase
from GT23.renderer import FilmRenderer

def run_workflow():
    # EN: Initialization / CN: 初始化各组件
    meta = MetadataHandler()
    db = FilmDatabase()
    renderer = FilmRenderer()
    
    # EN: Folder configuration / CN: 路径配置
    input_dir = "photos_in"
    output_dir = "photos_out"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # EN: Scan for images / CN: 扫描输入文件夹
    valid_exts = ('.jpg', '.jpeg', '.png')
    images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_exts)]
    
    if not images:
        print(f"CN: [!] 在 {input_dir} 中没找到图片。")
        return

    print(f"CN: >>> 准备处理 {len(images)} 张照片...")

    for img_name in images:
        img_path = os.path.join(input_dir, img_name)
        
        # 1. EN: Extract EXIF / CN: 提取元数据
        data = meta.get_data(img_path)
        
        # 2. EN: Film matching logic / CN: 胶卷匹配逻辑
        # EN: db.match already returns uppercase
        # CN: db.match 内部已处理为全大写
        matched = db.match(data['Film'])
        
        if matched:
            data['Film'] = matched
            print(f"CN: [✔] {img_name} -> 匹配成功: {matched}")
        else:
            print(f"CN: [?] {img_name} 无法识别胶卷 (EXIF: '{data['Film']}')")
            user_input = input("   >>> 请手动输入胶卷名称 (或回车跳过): ").strip()
            if user_input:
                # EN: Try to match user input, fallback to raw input if no match
                # CN: 尝试匹配用户输入，若库里没有则使用原样输入，并转大写
                data['Film'] = (db.match(user_input) or user_input).upper()
            else:
                data['Film'] = (data['Film'] or "UNKNOWN FILM").upper()

        # 3. EN: Render output / CN: 渲染出图
        try:
            renderer.process_image(img_path, data, output_dir)
            print(f"CN: [DONE] 已生成: {img_name}")
        except Exception as e:
            print(f"CN: [ERROR] 处理 {img_name} 失败: {e}")

if __name__ == "__main__":
    run_workflow()