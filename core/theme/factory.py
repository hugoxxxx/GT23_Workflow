from .classic import ClassicTheme
from .frosted import FrostedTheme
from .slate_teal import SlateTealTheme
from .gradient import GradientTheme
from .rainbow import RainbowTheme

class ThemeFactory:
    """
    EN: Factory for creating theme instances.
    CN: 创建主题实例的工厂类。
    """
    @staticmethod
    def get_theme(theme_name, img_path=""):
        theme_name = theme_name.lower()
        
        if theme_name == "dark":
            return ClassicTheme(mode="dark")
        elif theme_name == "frosted":
            return FrostedTheme()
        elif theme_name == "slate_teal":
            return SlateTealTheme()
        elif theme_name == "macaron":
            return GradientTheme(theme_type="macaron", img_path=img_path)
        elif theme_name == "sakura":
            return GradientTheme(theme_type="sakura", img_path=img_path)
        elif theme_name == "rainbow":
            return RainbowTheme()
        else:
            # Default Light Theme
            return ClassicTheme(mode="light")
