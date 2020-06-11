from typing import Tuple


def hex_to_rgb(s: str) -> Tuple[int, int, int]:
    """Converts hex color str to R, G, B values
    >>> hex_to_rgb('#ff00aa')
    (255, 0, 170)
    """
    s = s.lstrip("#")

    if len(s) == 6:  # e.g. ff00aa
        return tuple([int(s[i : i + 2], 16) for i in range(0, len(s), 2)])
    elif len(s) == 3:  # e.g. f0a -> ff00aa
        return tuple([int(i * 2, 16) for i in s])

    raise ValueError("Should be in #xxxxxx or #xxx format")
