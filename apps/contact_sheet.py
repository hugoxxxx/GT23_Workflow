# contact_sheet.py
import os
from core.metadata import MetadataHandler
from core.renderers.renderer_66 import Renderer66
from core.renderers.renderer_645 import Renderer645
from core.renderers.renderer_67 import Renderer67
from core.renderers.renderer_135 import Renderer135

class ContactSheetPro:
    def __init__(self):
        self.meta = MetadataHandler()
        self.renderers = {"66": Renderer66(), "645": Renderer645(), "67": Renderer67(), "135": Renderer135()}

    def run(self):
        input_dir, output_dir = "photos_in", "photos_out"
        img_paths = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if not img_paths: return

        # 1. 胶片手动匹配与元数据预提取
        sample_data = self.meta.get_data(img_paths[0])
        if not sample_data.get('Film'):
            print("CN: [?] 无法识别胶卷，启动手动匹配...")
            user_input = input("   >>> 请输入关键字 (如 p400): ").strip()
            matched = self.meta.match_film(user_input)
            if matched:
                sample_data = self.meta.get_data(img_paths[0], manual_film=matched)

        # 2. 调度渲染器执行
        layout_key = self.meta.detect_batch_layout(img_paths)
        cfg = self.meta.get_contact_layout(layout_key)
        renderer = self.renderers.get(layout_key, self.renderers["66"])
        
        canvas, user_emulsion = renderer.prepare_canvas(cfg.get("canvas_w", 4800), cfg.get("canvas_h", 6000))
        canvas = renderer.render(canvas, img_paths, cfg, self.meta, user_emulsion)

        # 3. 保存 (无页脚)
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        save_path = os.path.join(output_dir, f"ContactSheet_{layout_key}.jpg")
        canvas.save(save_path, quality=95)
        print(f"CN: [✔] 索引页已保存至: {save_path}")

if __name__ == "__main__":
    ContactSheetPro().run()