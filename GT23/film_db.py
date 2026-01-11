import json
import os
import re

class FilmDatabase:
    """
    EN: Film database with weighted matching, digit validation, and uppercase output.
    CN: 中英双语：带有权重匹配、数字校验且统一大写输出的胶卷数据库。
    """
    def __init__(self, config_path="config/films.json"):
        self.config_path = config_path
        self.library = self._load_db()

    def _load_db(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                print(f"CN: [!] 胶卷库加载失败: {e}")
                return {}
        return {}

    def match(self, raw_input):
        """
        EN: Advanced fuzzy match with digit-guard logic.
        CN: 中英双语：带有数字守卫逻辑的高级模糊匹配。
        """
        if not raw_input: return None
        
        # EN: Normalize: Uppercase and remove spaces for matching
        # CN: 规范化：转大写并去除空格进行逻辑比对
        q = str(raw_input).upper().replace(" ", "")
        q_digits = "".join(re.findall(r'\d+', q))
        
        best_match = None
        highest_score = 0

        for brand, films in self.library.items():
            for std_name, keywords in films.items():
                # EN: Combine standard name and keywords
                # CN: 汇总标准名称和关键词
                targets = [std_name.upper()] + [str(k).upper() for k in keywords]
                
                for t in targets:
                    t_clean = t.replace(" ", "")
                    t_digits = "".join(re.findall(r'\d+', t_clean))
                    
                    score = 0
                    # 1. EN: Exact match / CN: 完全匹配
                    if q == t_clean:
                        score = 100
                    
                    # 2. EN: Substring match / CN: 子串包含匹配
                    elif q in t_clean or t_clean in q:
                        score = 60
                        
                        # EN: Digit Guard: If digits exist, they MUST be identical
                        # CN: 数字守卫：如果双方都有数字，则必须完全一致，否则一票否决
                        if q_digits and t_digits:
                            if q_digits != t_digits:
                                score = 0 
                            else:
                                score += 20 
                        
                        # EN: Length proximity bonus / CN: 长度接近加分
                        score += (len(q) / len(t_clean) * 5)

                    if score > highest_score:
                        highest_score = score
                        best_match = f"{brand} {std_name}"
        
        # EN: Final output is always forced to UPPERCASE
        # CN: 最终输出统一强制转为全大写
        return best_match.upper() if best_match else None