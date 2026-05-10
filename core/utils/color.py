def interpolate_color(c1, c2, t):
    \"\"\"
    EN: Linear interpolation between two colors.
    CN: 颜色线性插值。
    \"\"\"
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
