def get_center_offset(canvas_size, element_size):
    \"\"\"
    EN: Calculate top-left coordinates to center an element.
    CN: 计算居中对齐所需的左上角坐标。
    \"\"\"
    return (canvas_size[0] - element_size[0]) // 2, (canvas_size[1] - element_size[1]) // 2
