

def bgr_to_rgb_list(bgr):
    """Convert a Blue Greed Red long integer (BGR) into an RGB list.

    Args:
        bgr (long): long integer representing a BGR color

    Returns:
        list of int: [r, g, b]
    """
    r = bgr & 255
    g = (bgr >> 8) & 255
    b = (bgr >> 16) & 255
    return [r, g, b]
