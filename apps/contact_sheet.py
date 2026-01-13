# apps/contact_sheet.py
import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont

# EN: Path setup / CN: 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from core.metadata import MetadataHandler

class ContactSheetPro:
    def __init__(self):
        self.meta = MetadataHandler()
        try:
            self.font = ImageFont.truetype("consola.ttf", 44)
        except:
            self.font = ImageFont.load_default()

    def create_tight_text(self, text, rotate_angle=90, color=(245, 130, 35, 210)):
        left, top, right, bottom = self.font.getbbox(text)
        w, h = right - left, bottom - top
        txt_img = Image.new('RGBA', (w + 10, h + 10), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_img)
        draw.text((5, 0), text, font=self.font, fill=color)
        return txt_img.rotate(rotate_angle, expand=True)

    def create_stretched_triangle(self, color):
        tri_raw = self.create_tight_text("▲", 0, color=color)
        w, h = tri_raw.size
        stretched = tri_raw.resize((w, int(h * 1.8)), Image.Resampling.LANCZOS)
        return stretched.rotate(180, expand=True)

    def run(self):
        print("\n" + "="*50)
        print("CN: >>> 120 胶片索引页：极致物理复刻版 (645 频率标识重构版) <<<")
        print("="*50)

        input_dir = os.path.join(project_root, "photos_in")
        output_dir = os.path.join(project_root, "photos_out")
        img_list = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        
        if not img_list:
            print("CN: [!] 文件夹内未发现图片。")
            return

        user_emulsion = input("CN: 请输入乳剂号 (如 049): ").strip()

        cfg = self.meta.get_contact_layout("66")
        canvas_w, canvas_h = 4800, 6000
        m_x, m_y_t, m_y_b = cfg['margin_x'], cfg['margin_y_top'], cfg['margin_y_bottom']
        c_gap, r_gap = cfg['col_gap'], cfg['row_gap']
        cols, rows = cfg['cols'], 4 

        canvas = Image.new("RGB", (canvas_w, canvas_h), (235, 235, 235))
        draw = ImageDraw.Draw(canvas)

        strip_w_max = (canvas_w - 2 * m_x - (cols - 1) * c_gap) // cols
        photo_slot_h = (canvas_h - m_y_t - m_y_b) // rows
        FILM_RATIO = 61.5 / 56.0 
        side_length = min(int(strip_w_max / FILM_RATIO), photo_slot_h - r_gap)
        strip_w = int(side_length * FILM_RATIO)

        # --- EN: PRE-CALCULATE COLUMN PARAMS / CN: 预计算列参数与黑边范围 ---
        col_drifts = [random.randint(-150, 150) for _ in range(cols)]
        strip_top = m_y_t - 80
        strip_bottom = m_y_t + rows * (side_length + r_gap) + 40
        # EN: 645 step is ~0.75 of 66 length / CN: 645 步进约为 66 长度的 0.75 倍
        step_645 = int(side_length * 0.75)

        # EN: Get universal film info from the first image / CN: 从第一张图获取全卷统一的胶片信息
        sample_data = self.meta.get_data(os.path.join(input_dir, img_list[0]))
        edge_name = sample_data.get("EdgeCode", "SAFETY FILM")
        cur_color = sample_data.get("ContactColor", (245, 130, 35, 210))
        left_layer = self.create_tight_text(f"{user_emulsion}  {edge_name}", 90, color=cur_color)

        # --- EN: PHASE 1: RENDER BLACK STRIPS & LEFT MARKINGS / CN: 第一阶段：渲染黑边与左侧标识 ---
        for c in range(cols):
            col_center_x = m_x + (strip_w_max // 2) + c * (strip_w_max + c_gap)
            s_x1 = col_center_x - (strip_w // 2)
            
            # EN: Draw Black Strip / CN: 绘制黑边
            draw.rectangle([s_x1, strip_top, s_x1 + strip_w, strip_bottom], fill=(12, 12, 12))
            
            # EN: Fill markings based on 645 frequency / CN: 按 645 频率填充标识
            curr_marker_y = strip_top + col_drifts[c]
            while curr_marker_y < strip_bottom:
                # EN: Safety clamp / CN: 安全约束
                if curr_marker_y > strip_top + 10 and (curr_marker_y + left_layer.height) < strip_bottom - 10:
                    canvas.paste(left_layer, (int(s_x1 + 8), int(curr_marker_y)), left_layer)
                curr_marker_y += step_645

        # --- EN: PHASE 2: RENDER PHOTOS & RIGHT NUMBERS / CN: 第二阶段：渲染照片与右侧序号 ---
        for i, img_name in enumerate(img_list):
            if i >= (cols * rows): break
            c, r = i // rows, i % rows
            
            col_center_x = m_x + (strip_w_max // 2) + c * (strip_w_max + c_gap)
            s_x1 = col_center_x - (strip_w // 2)
            row_top_y = m_y_t + r * (side_length + r_gap)
            
            img_path = os.path.join(input_dir, img_name)
            with Image.open(img_path) as img:
                img.thumbnail((side_length, side_length), Image.Resampling.LANCZOS)
                tw, th = img.size
                curr_x, curr_y = col_center_x - (tw // 2), row_top_y
                canvas.paste(img, (int(curr_x), int(curr_y)))

                # EN: Right side (Tri + Num) follows the photo / CN: 右侧（三角+序号）跟随照片位置
                tri_layer = self.create_stretched_triangle(color=cur_color)
                num_layer = self.create_tight_text(str(i + 1), 90, color=cur_color)
                layer_w = num_layer.width
                right_x = s_x1 + strip_w - layer_w - 8
                center_y = curr_y + (th // 2)
                
                canvas.paste(tri_layer, (int(right_x), int(center_y - 60)), tri_layer)
                canvas.paste(num_layer, (int(right_x), int(center_y + 40)), num_layer)

            print(f"CN: [✔] {i+1}: {img_name} (喷码:{edge_name})")

        if not os.path.exists(output_dir): os.makedirs(output_dir)
        save_path = os.path.join(output_dir, "Physical_Fuji_Contact_Sheet.jpg")
        canvas.save(save_path, quality=95)
        print(f"\nCN: [FINISH] 物理复刻索引页已完成。")

# EN: Export the function required by main.py
# CN: 中英双语：导出 main.py 所需的入口函数
def run_contact_sheet():
    app = ContactSheetPro()
    app.run()

if __name__ == "__main__":
    run_contact_sheet()