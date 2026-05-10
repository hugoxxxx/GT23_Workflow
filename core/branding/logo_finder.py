import os
from ..utils.path import resolve_path

class LogoFinder:
    """
    EN: Responsible for locating camera brand and model logos in the assets directory.
    CN: 负责在 assets 目录下定位相机品牌及型号的 Logo 文件。
    """
    
    @staticmethod
    def find_logo_path(make, model, logo_dir=None):
        """
        EN: Finds the best matching logo for a given make/model.
        CN: 为指定的品牌/型号寻找最匹配的 Logo 路径。
        """
        # EN: Multi-path search (Primary dir + Dist fallback)
        # CN: 多路径搜索（主目录 + Dist 降级目录）
        search_dirs = []
        if logo_dir:
            search_dirs.append(logo_dir)
            
        # EN: Add common asset locations / CN: 添加通用资源位置
        search_dirs.append(resolve_path("assets/logos"))
        
        # EN: Add Dist fallback (for packaged EXE compatibility)
        # CN: 添加 Dist 降级（兼容某些打包后的资源布局）
        dist_path = resolve_path("dist/GT23_Assets/logos")
        if os.path.exists(dist_path):
            search_dirs.append(dist_path)
            
        make_u = str(make or "").strip().upper()
        model_u = str(model or "").strip().upper()
        
        if not model_u and not make_u:
            return None

        for l_dir in search_dirs:
            if not os.path.exists(l_dir):
                continue
                
            # 1. EN: Try precise model match (MAKE_MODEL.png)
            if model_u:
                sanitized_model = model_u.replace(" ", "_").replace("/", "_")
                model_file = f"{make_u}_{sanitized_model}.png"
                model_path = os.path.join(l_dir, model_file)
                if os.path.exists(model_path):
                    return model_path
            
            # 2. EN: Try brand match (MAKE.svg or MAKE.png)
            if make_u:
                for ext in [".svg", ".png", ".jpg"]:
                    brand_path = os.path.join(l_dir, f"{make_u}{ext}")
                    if os.path.exists(brand_path):
                        return brand_path
            
            # 3. EN: Fuzzy brand match in current directory
            try:
                files = os.listdir(l_dir)
                for f in files:
                    if make_u and make_u in f.upper() and any(f.lower().endswith(ext) for ext in [".png", ".svg", ".jpg"]):
                        return os.path.join(l_dir, f)
            except:
                pass
                
        return None
