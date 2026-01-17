# contact_sheet.py
import os
import sys
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
            print("CN: [?] 无法识别胶卷，启动手动匹配...")
            user_keyword = input("   >>> 请输入关键字 (如 p400): ").strip()
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
            print(f"CN: [✔] 索引页已保存至: {save_path}")
            
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

if __name__ == "__main__":
    ContactSheetPro().run()