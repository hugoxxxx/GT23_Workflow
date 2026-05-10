from abc import ABC, abstractmethod
from PIL import Image

class BaseThemeRenderer(ABC):
    \"\"\"
    EN: Base class for all theme renderers.
    CN: 所有主题渲染器的基类。
    \"\"\"
    @abstractmethod
    def apply(self, canvas, img, layout_config, theme_config):
        pass
