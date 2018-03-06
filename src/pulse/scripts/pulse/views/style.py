
__all__ = [
    'UIColors',
]


class UIColors(object):

    RED = (120, 60, 60, 1)
    GREEN = (60, 110, 60, 1)
    BLUE = (60, 70, 120, 1)

    @staticmethod
    def asStyleSheet(color):
        """
        Return a color formatted for use in a stylesheet
        """
        return 'rgba{0}'.format(tuple(color))

    @staticmethod
    def asBGColor(color):
        """
        Return a color formatted for use as a stylesheet modifying background-color
        """
        return 'background-color:{0};'.format(UIColors.asStyleSheet(color))
