import os
import sys
from utils.config_manager import config_manager

print(f"Config directory: {config_manager.config_dir}")
print(f"Config path: {config_manager.config_path}")
print(f"Config content: {config_manager.config}")
