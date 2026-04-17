from PIL import Image
import numpy as np
import os

def measure(img_path):
    img = Image.open(img_path).convert('L')
    arr = np.array(img)
    h, w = arr.shape
    
    # EN: Project pixels to axes / CN: 将像素投影到坐标轴
    h_proj = np.mean(arr, axis=0) # Width-wise
    v_proj = np.mean(arr, axis=1) # Height-wise
    
    threshold = 250 # White constant
    h_white = h_proj > threshold
    v_white = v_proj > threshold
    
    def get_ranges(bars):
        ranges = []
        start = None
        for i, b in enumerate(bars):
            if b and start is None:
                start = i
            elif not b and start is not None:
                ranges.append((start, i - 1))
                start = None
        if start is not None:
            ranges.append((start, len(bars) - 1))
        return ranges

    x_ranges = get_ranges(h_white)
    y_ranges = get_ranges(v_white)
    
    print(f"Image Size: {w}x{h}")
    print(f"Horizontal (X) White Gaps: {x_ranges}")
    print(f"Vertical (Y) White Gaps: {y_ranges}")
    
    # EN: Extract ratios / CN: 提取比例
    if len(x_ranges) >= 2:
        margin_x_left = x_ranges[0][1] - x_ranges[0][0] + 1
        margin_x_right = x_ranges[-1][1] - x_ranges[-1][0] + 1
        print(f"Left Margin: {margin_x_left} ({margin_x_left/w:.2%})")
        print(f"Right Margin: {margin_x_right} ({margin_x_right/w:.2%})")
        
        if len(x_ranges) > 2:
            gap_x = x_ranges[1][1] - x_ranges[1][0] + 1
            print(f"X Gap: {gap_x} ({gap_x/w:.2%})")

    if len(y_ranges) >= 2:
        margin_y_top = y_ranges[0][1] - y_ranges[0][0] + 1
        margin_y_bottom = y_ranges[-1][1] - y_ranges[-1][0] + 1
        print(f"Top Margin: {margin_y_top} ({margin_y_top/h:.2%})")
        print(f"Bottom Margin: {margin_y_bottom} ({margin_y_bottom/h:.2%})")
        
        if len(y_ranges) > 2:
            gap_y = y_ranges[1][1] - y_ranges[1][0] + 1
            print(f"Y Gap: {gap_y} ({gap_y/h:.2%})")

if __name__ == "__main__":
    path = r'C:\Users\Administrator\.gemini\antigravity\brain\e40b13d6-315a-434c-bbcb-3c0f00d59d6a\media__1775558628798.jpg'
    measure(path)
