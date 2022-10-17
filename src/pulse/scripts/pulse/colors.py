from typing import Union


class LinearColor(list):
    """
    Represents a color and provides some math functionality and
    formatting to strings for use in Qt style sheets.

    LinearColor values are be represented from 0..1, and converted to 0..255
    when used in style sheet format.
    """

    @classmethod
    def from_other(cls, color: 'LinearColor') -> 'LinearColor':
        return cls(color.r, color.g, color.b, color.a)

    @classmethod
    def from_seq(cls, seq: Union[list, tuple]) -> 'LinearColor':
        return cls(*seq[:4])

    @classmethod
    def from_8bit(cls, color: Union[list, tuple]):
        """
        Make a LinearColor from an 8-bit color (0..255)
        """
        return LinearColor.from_seq([c / 255.0 for c in color])

    @classmethod
    def from_hex(cls, hex_color: str) -> 'LinearColor':
        """
        Make a LinearColor from a hex color string, e.g. '#ffbb00'
        """
        hex_color = hex_color.lstrip('#')
        color: list
        if len(hex_color) == 3:
            # 3 digit color '#fff'
            color = [int(hex_color[i] * 2, 16) for i in (0, 1, 2)]
        elif len(hex_color) == 6:
            # 6 digit color '#ffffff'
            color = [int(hex_color[i:i + 2], 16) for i in (0, 2, 4)]
        else:
            raise ValueError(f'Invalid hex color: {hex_color}')
        return LinearColor.from_8bit(color)

    def __init__(self, r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 1.0):
        super(LinearColor, self).__init__([r, g, b, a])

    def __repr__(self):
        return f'{self.__class__.__name__}({self.r}, {self.g}, {self.b}, {self.a})'

    @property
    def r(self):
        return self[0]

    @r.setter
    def r(self, value):
        self[0] = value

    @property
    def g(self):
        return self[1]

    @g.setter
    def g(self, value):
        self[1] = value

    @property
    def b(self):
        return self[2]

    @b.setter
    def b(self, value):
        self[2] = value

    @property
    def a(self):
        return self[3]

    @a.setter
    def a(self, value):
        self[3] = value

    def __mul__(self, other: Union['LinearColor', float, int]) -> 'LinearColor':
        result: LinearColor = LinearColor.from_other(self)
        if hasattr(other, '__iter__'):
            for i, v in enumerate(other):
                if i > 3:
                    break
                result[i] *= v
        else:
            for i in range(len(result)):
                result[i] *= other
        return result

    def as_8bit(self) -> tuple:
        """
        Return this linear color (0..1) as an 8 bit color (0..255).
        """
        return tuple([int(c * 255) for c in self])

    def as_hex(self) -> str:
        return '#%02x%02x%02x' % tuple(self.as_8bit()[:3])

    def as_style(self, include_alpha=True) -> str:
        if include_alpha:
            return 'rgba{0}'.format(tuple(self.as_8bit()[:4]))
        else:
            return 'rgb{0}'.format(tuple(self.as_8bit()[:3]))

    def as_fg_style(self, include_alpha=True) -> str:
        return f'color: {self.as_style(include_alpha)}'

    def as_bg_style(self, include_alpha=True) -> str:
        return f'background-color: {self.as_style(include_alpha)}'
