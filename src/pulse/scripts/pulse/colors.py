__all__ = [
    'hexToRGB01',
    'RGB01ToHex',
]


def RGB01ToHex(rgb):
    """
    Return an RGB color value as a hex color string.
    """
    return '#%02x%02x%02x' % tuple([int(x * 255) for x in rgb])


def hexToRGB01(hexColor):
    """
    Return a hex color string as an RGB tuple of floats in the range 0..1
    """
    h = hexColor.lstrip('#')
    return tuple([x / 255.0 for x in [int(h[i:i + 2], 16) for i in (0, 2, 4)]])
