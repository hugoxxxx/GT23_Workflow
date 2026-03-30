import cairosvg
import os

try:
    svg_path = r"d:\Projects\GT23_Workflow\assets\contax-logo-svg-vector.svg"
    output_png = r"d:\Projects\GT23_Workflow\test_contax.png"
    cairosvg.svg2png(url=svg_path, write_to=output_png)
    print(f"Success: {output_png} created.")
    print(f"Size: {os.path.getsize(output_png)} bytes")
except Exception as e:
    print(f"Error: {e}")
