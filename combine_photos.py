import os
from PIL import Image, ImageOps

def create_collage(src_dir, output_path, target_ratio=(3, 4), cols=3, rows=4):
    # 1. EN: List files / CN: 获取文件列表
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    files = [os.path.join(src_dir, f) for f in os.listdir(src_dir) 
             if f.lower().endswith(valid_exts)]
    files.sort()
    files = files[:12] # Limit to 12
    
    if not files:
        print("No images found in source directory.")
        return

    # 2. EN: Canvas Setup (Calculated from 768x1024 reference)
    # CN: 根据 768x1024 样片精确计算测得的比例 (Scaled to 3000x4000)
    target_w = 3000
    target_h = 4000
    
    # Ratios: Side Margin 8.98%, Top/Bot 2.54%, Gap ~1%
    margin_x = int(target_w * 0.0898) # ~270
    margin_y = int(target_h * 0.0254) # ~102
    gap = int(target_w * 0.0104)      # ~31
    
    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    
    # 3. EN: Calculate cell size using measured grid / CN: 基于测绘格点计算单元格
    cell_w = (target_w - 2 * margin_x - (cols - 1) * gap) // cols
    cell_h = (target_h - 2 * margin_y - (rows - 1) * gap) // rows
    
    grid_w = cols * cell_w + (cols - 1) * gap
    grid_h = rows * cell_h + (rows - 1) * gap
    
    start_x = (target_w - grid_w) // 2
    start_y = (target_h - grid_h) // 2
    
    # 4. EN: Paste images / CN: 粘贴图片
    for i, file_path in enumerate(files):
        c = i % cols
        r = i // cols
        
        try:
            img = Image.open(file_path)
            img = ImageOps.exif_transpose(img)
            
            # EN: Preserve aspect ratio and fit in square / CN: 不裁切，保留原图比例并居中
            img.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            
            # Calculate offset to center within the cell
            off_x = (cell_w - img.width) // 2
            off_y = (cell_h - img.height) // 2
            
            x = start_x + c * (cell_w + gap) + off_x
            y = start_y + r * (cell_h + gap) + off_y
            
            canvas.paste(img, (x, y))
            print(f"Added {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    # 5. EN: Save / CN: 保存
    canvas.save(output_path, "JPEG", quality=95)
    print(f"\nSUCCESS: Collage saved to {output_path}")

if __name__ == "__main__":
    SRC = r"D:\Projects\test"
    OUT = os.path.join(SRC, "collage_3x4.jpg")
    create_collage(SRC, OUT)
