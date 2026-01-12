# apps/contact_sheet.py
import os
from PIL import Image, ImageDraw
from core.metadata import MetadataHandler

def run_contact_sheet():
    """
    EN: Golden Ratio driven vertical layout with maximized photo content.
    CN: 中英双语：基于黄金分割驱动的纵向布局，并最大化照片内容。
    """
    print("\n" + "="*45)
    print("CN: >>> 底片索引：黄金分割审美模式 <<<")
    print("="*45)

    meta = MetadataHandler()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(project_root, "photos_in")
    output_dir = os.path.join(project_root, "photos_out")

    img_list = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    if not img_list: return

    # 1. EN: Canvas Setup / CN: 画布设置 (10寸 @ 600DPI)
    canvas_w, canvas_h = 4800, 6000
    canvas = Image.new("RGB", (canvas_w, canvas_h), (235, 235, 235))
    draw = ImageDraw.Draw(canvas)

    cfg = meta.get_contact_layout("66")
    cols, rows = cfg['cols'], cfg.get('rows', 4)
    c_gap, r_gap = cfg['col_gap'], cfg['row_gap']
    m_x = cfg['margin_x']
    m_y_t, m_y_b = cfg['margin_y_top'], cfg['margin_y_bottom']

    # 2. EN: Physical Model / CN: 120 物理比例
    FILM_RATIO = 61.5 / 56.0

    # 3. EN: Space Calculation / CN: 空间分配计算
    # EN: Maximize width based on side margins and gallery gutters
    available_w = canvas_w - (2 * m_x) - ((cols - 1) * c_gap)
    strip_w_max = available_w // cols
    
    # EN: Distribute vertical space using the golden ratio margins
    # CN: 使用黄金分割边距分配垂直空间
    available_h = canvas_h - m_y_t - m_y_b
    photo_slot_h = available_h // rows
    
    # EN: Optimize photo size / CN: 优化照片边长
    # EN: Photos will now be slightly larger as we rebalanced the margins.
    side_length = min(int(strip_w_max / FILM_RATIO), photo_slot_h - r_gap)
    strip_w = int(side_length * FILM_RATIO)
    
    # EN: Film leader extension / CN: 引片头尾补偿
    strip_ext = r_gap // 2

    # 4. EN: Step 1: Draw Film Strips / CN: 第一步：绘制黑条基带
    # 
    for c in range(cols):
        col_center_x = m_x + (strip_w_max // 2) + c * (strip_w_max + c_gap)
        s_x1 = col_center_x - (strip_w // 2)
        s_x2 = col_center_x + (strip_w // 2)
        
        # EN: Start from top leader / CN: 从顶部引片头开始
        y_start = m_y_t - strip_ext
        # EN: Ensure the bottom is covered by a full metadata zone
        # CN: 确保底部被完整的信息区覆盖
        y_end = m_y_t + rows * (side_length + r_gap)
        
        draw.rectangle([s_x1, y_start, s_x2, y_end], fill=(12, 12, 12))

    # 5. EN: Step 2: Paste Photos / CN: 第二步：贴入照片
    for i, img_name in enumerate(img_list):
        if i >= (cols * rows): break
        c, r = i % cols, i // cols
        
        col_center_x = m_x + (strip_w_max // 2) + c * (strip_w_max + c_gap)
        # EN: Each row starts at the top of its calculated slot
        # CN: 每行照片放在槽位的起始位置
        row_top_y = m_y_t + r * (side_length + r_gap)
        
        with Image.open(os.path.join(input_dir, img_name)) as img:
            img.thumbnail((side_length, side_length), Image.Resampling.LANCZOS)
            tw, th = img.size
            
            curr_x = col_center_x - (tw // 2)
            curr_y = row_top_y
            
            canvas.paste(img, (int(curr_x), int(curr_y)))
            # EN: Micro-edge / CN: 模拟底片物理边缘
            draw.rectangle([curr_x, curr_y, curr_x + tw, curr_y + th], outline=(35, 35, 35), width=1)
            print(f"CN: [渲染] {img_name} | 边长: {side_length}px")

    # 6. EN: Export / CN: 导出
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    save_path = os.path.join(output_dir, "Index_66_Golden_Ratio.jpg")
    canvas.save(save_path, quality=98, dpi=(600, 600))
    print(f"\nCN: [SUCCESS] 黄金分割审美版生成完毕！")

if __name__ == "__main__":
    run_contact_sheet()