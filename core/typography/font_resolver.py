import os
import sys
from ..utils.text import contains_chinese
from .engine import TypoEngine

class FontResolver:
    """
    EN: Responsible for font discovery, CJK detection and fallback.
    CN: 负责字体发现、CJK 字符检测与备用字体降级。
    """
    def __init__(self, font_dir, default_main="assets/fonts/palab.ttf", default_sub="assets/fonts/gara.ttf"):
        self.font_dir = font_dir
        self.default_main = default_main
        self.default_sub = default_sub

    def resolve(self, main_text, sub_text, custom_main=None, custom_sub=None):
        """
        EN: Resolve final font paths including CJK fallback.
        CN: 解析最终字体路径，包括中文字体降级逻辑。
        """
        resolved_main = custom_main or self.default_main
        resolved_sub = custom_sub or self.default_sub
        
        # EN: Detect Chinese / CN: 检查中文并降级字库
        if contains_chinese(main_text) or contains_chinese(sub_text):
            cjk_path = self._get_system_cjk_font()
            if cjk_path:
                resolved_main = cjk_path
                resolved_sub  = cjk_path
        
        return self._full_resolve(resolved_main, self.default_main), \
               self._full_resolve(resolved_sub, self.default_sub)

    def _full_resolve(self, p, default_val):
        """EN: Deep resolution of font paths. / CN: 深度解析字体路径。"""
        if not p or p == "Default": 
            p = default_val
            
        # EN: Prioritize fonts in asset directory for simple filenames
        # CN: 对于简单文件名，优先在资产目录中检索
        if not os.path.isabs(p) and not p.startswith("assets"):
            test_path = os.path.join(self.font_dir, p)
            if os.path.exists(test_path): return test_path
        
        # EN: Fallback to TypoEngine's path resolution
        return TypoEngine._resolve_font_path(p)

    def _get_system_cjk_font(self):
        """EN: Find Microsoft YaHei or similar on Windows. / CN: 在 Windows 上寻找微软雅黑。"""
        if sys.platform == "win32":
            paths = [
                "C:\\Windows\\Fonts\\msyh.ttc",    # Microsoft YaHei
                "C:\\Windows\\Fonts\\msyhbd.ttc",  # YaHei Bold
                "C:\\Windows\\Fonts\\simhei.ttf"   # SimHei
            ]
            for p in paths:
                if os.path.exists(p): return p
        return None
