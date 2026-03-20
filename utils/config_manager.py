# utils/config_manager.py
import os
import sys
import json

class ConfigManager:
    """
    EN: Manages application configuration and user preferences.
    CN: 官理应用程序配置和用户偏好。
    """
    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.config = self._load()

    def _get_config_dir(self):
        if getattr(sys, 'frozen', False):
            # Portability: keep config next to EXE for packaged versions
            return os.path.dirname(sys.executable)
        else:
            # Standard: AppData for development/installed versions
            app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
            path = os.path.join(app_data, "GT23_Workflow")
            os.makedirs(path, exist_ok=True)
            return path

    def _load(self):
        default_config = {
            "custom_asset_path": "",
            "preferred_sync_source": "gitee",  # gitee or github
            "auto_check_updates": True
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception:
                pass
        return default_config

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"CN: [!] 无法保存配置文件: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

# Global instance
config_manager = ConfigManager()
