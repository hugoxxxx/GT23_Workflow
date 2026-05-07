from PIL import Image
import os

font_dir = r"D:\Projects\GT23_Workflow\assets\fonts\1050"
test_file = os.path.join(font_dir, "1050-0.png")

if os.path.exists(test_file):
    img = Image.open(test_file).convert('RGBA')
    extrema = img.getextrema()
    print(f"Extrema: {extrema}")
    
    # Check some pixels
    pixels = list(img.getdata())
    non_zero_alphas = [p for p in pixels if p[3] > 0]
    if non_zero_alphas:
        print(f"Sample non-transparent pixel: {non_zero_alphas[0]}")
    else:
        print("Image is fully transparent!")
else:
    print("File not found")
