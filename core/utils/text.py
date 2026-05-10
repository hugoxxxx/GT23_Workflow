import re

def contains_chinese(text):
    """
    EN: Detect if text contains CJK characters.
    CN: 检测文本是否包含中文字符。
    """
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))
