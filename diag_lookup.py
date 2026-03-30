import os
import sys
# Add parent dir to path to import utils/core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.renderer import FilmRenderer

def diag_lookup():
    r = FilmRenderer()
    print(f"Renderer Logo Dir: {r.logo_dir}")
    print(f"Dir exists: {os.path.exists(r.logo_dir)}")
    if os.path.exists(r.logo_dir):
        print(f"Files inside: {len(os.listdir(r.logo_dir))}")
    
    # Try finding some common logos
    test_cases = [
        ("HASSELBLAD", "503CX"),
        ("CONTAX", "G2"),
        ("LEICA", "M6"),
        ("FUJIFILM", "GA645")
    ]
    
    for make, model in test_cases:
        path = r._find_logo_path(make, model)
        print(f"Lookup ({make}, {model}) -> {path}")

if __name__ == "__main__":
    diag_lookup()
