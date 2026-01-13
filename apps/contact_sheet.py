import os
from PIL import Image
from core.metadata import MetadataHandler
from core.renderers.renderer_66 import Renderer66
from core.renderers.renderer_645 import Renderer645

class ContactSheetPro:
    def __init__(self):
        self.meta = MetadataHandler()
        self.renderers = {
            "66": Renderer66(),
            "645": Renderer645()
        }

    def run(self):
        print("\n" + "="*50)
        print("CN: >>> 120 胶片索引页：645 物理排版全自动版 <<<")
        print("="*50)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        input_dir = os.path.join(project_root, "photos_in")
        output_dir = os.path.join(project_root, "photos_out")
        
        img_paths = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if not img_paths: 
            print("CN: [!] 文件夹为空，请放入照片。")
            return

        layout_key = self.meta.detect_batch_layout(img_paths)
        cfg = self.meta.get_contact_layout(layout_key)
        renderer = self.renderers.get(layout_key, self.renderers["66"])
        
        # 初始准备画布
        canvas, user_emulsion = renderer.prepare_canvas(cfg.get("canvas_w", 4800), cfg.get("canvas_h", 6000))
        
        # 执行渲染 (渲染器内部可能会根据 L/P 方案重塑 canvas 并返回)
        canvas = renderer.render(canvas, img_paths, cfg, self.meta, user_emulsion)
        
        # 处理保存后缀
        suffix = f"_{cfg['output_suffix']}" if 'output_suffix' in cfg else ""
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        
        save_path = os.path.join(output_dir, f"ContactSheet_{layout_key}{suffix}.jpg")
        canvas.save(save_path, "JPEG", quality=95)
        print(f"CN: [✔] 渲染完成! 后缀: {suffix} | 路径: {save_path}")

if __name__ == "__main__":
    app = ContactSheetPro()
    app.run()