def lerp_color(c1, c2, t):
    """
    EN: Linear interpolation between two RGB colors.
    CN: 两个 RGB 颜色之间的线性插值。
    """
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
