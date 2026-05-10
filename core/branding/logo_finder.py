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
                
            # 1. EN: Try precise model match with various separators
            # CN: 尝试多种分隔符进行精准型号匹配
            if model_u:
                # EN: Generate candidates based on common naming conventions
                # CN: 基于常见的命名惯例生成候选文件名
                clean_model = model_u.replace(" ", "").replace("/", "").replace("-", "").replace("_", "")
                
                # EN: Try MAKE-MODEL, MAKE_MODEL, and MAKEMODEL
                candidates = [
                    f"{make_u}-{clean_model}.png",
                    f"{make_u}_{clean_model}.png",
                    f"{make_u}{clean_model}.png",
                    f"{make_u}-{model_u.replace(' ', '-')}.png",
                    f"{make_u}_{model_u.replace(' ', '_')}.png"
                ]
                
                for cand in candidates:
                    target_path = os.path.join(l_dir, cand)
                    if os.path.exists(target_path):
                        return target_path
                        
                # 1.1 EN: Try Normalized match (ignore all separators in filename)
                # CN: 尝试去重匹配（忽略文件名中的所有分隔符和空格）
                try:
                    files = os.listdir(l_dir)
                    def _norm(s): return "".join(c for c in s if c.isalnum()).upper()
                    norm_target = _norm(make_u + clean_model)
                    
                    for f in files:
                        f_up = f.upper()
                        if f_up.endswith(('.PNG', '.SVG', '.JPG')):
                            if norm_target == _norm(os.path.splitext(f_up)[0]):
                                return os.path.join(l_dir, f)
                            # EN: Also allow if model is contained and brand matches
                            if make_u in f_up and clean_model in _norm(f_up):
                                return os.path.join(l_dir, f)
                except:
                    pass
            
            # 2. EN: Try brand match (MAKE.svg or MAKE.png)
            if make_u:
                for ext in [".svg", ".png", ".jpg"]:
                    brand_path = os.path.join(l_dir, f"{make_u}{ext}")
                    if os.path.exists(brand_path):
                        return brand_path
            
            # 3. EN: Fuzzy brand match (Last resort, only if we can't find a brand-only logo)
            # CN: 模糊品牌匹配（作为最后手段，且尽可能寻找纯品牌 Logo）
            try:
                files = os.listdir(l_dir)
                # EN: Sort files to ensure stable matching / CN: 排序确保匹配稳定性
                files.sort()
                
                # EN: Look for a file that is EXACTLY the brand name (ignoring case/ext)
                # CN: 优先寻找文件名刚好等于品牌名的文件
                for f in files:
                    stem = os.path.splitext(f)[0].upper()
                    if stem == make_u:
                        return os.path.join(l_dir, f)
                
                # EN: If still nothing, pick the first one that contains the brand name BUT is not another specific model
                # CN: 如果还是没有，寻找包含品牌名但不是其他特定型号的文件
                for f in files:
                    f_up = f.upper()
                    if make_u and make_u in f_up and any(f_up.endswith(ext) for ext in [".PNG", ".SVG", ".JPG"]):
                        # EN: Safety check: if there's an underscore or dash, it might be another model
                        # CN: 安全检查：如果包含下划线或横杠且不是纯品牌，可能误中其他型号
                        if ("_" not in f and "-" not in f) or f_up.startswith(make_u + "_LOGO") or f_up.startswith(make_u + "-LOGO"):
                            return os.path.join(l_dir, f)
            except:
                pass
                
        return None
