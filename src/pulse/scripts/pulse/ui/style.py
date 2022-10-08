from ..vendor.Qt import QtGui


class UIColors(object):
    RED = (120, 60, 60, 1)
    GREEN = (60, 110, 60, 1)
    BLUE = (60, 80, 120, 1)
    DARKGRAY = (20, 20, 20, 1)
    HELPTEXT = (255, 255, 255, 0.25)
    WARNING = (200, 180, 120, 1)
    ERROR = (240, 60, 60, 1)
    WHITE = (255, 255, 255, 1)

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

    @staticmethod
    def asFGColor(color):
        """
        Return a color formatted for use as a stylesheet modifying foreground-color
        """
        return 'color:{0};'.format(UIColors.asStyleSheet(color))


class UIFonts(object):

    @staticmethod
    def getHelpTextFont():
        font = QtGui.QFont()
        font.setItalic(True)
        return font
