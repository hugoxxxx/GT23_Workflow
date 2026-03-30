import os
import sys
# Add parent dir to path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.asset_sync import _sync_via_web

def test_sync():
    success, msg = _sync_via_web()
    print(f"Success: {success}")
    print(f"Message: {msg}")

if __name__ == "__main__":
    test_sync()
