
import pymel.core as pm

__all__ = [
    'optionVarProperty',
]


def optionVarProperty(key, default):
    """
    Create a property that is saved in the user's preferences
    by using Maya optionVars.

    Args:
        key (str): The option var key for the property
        default: The default value of the property
    """

    def fget(self):
        return pm.optionVar.get(key, default)

    def fset(self, value):
        pm.optionVar[key] = value

    def fdel(self):
        if key in pm.optionVar:
            del pm.optionVar[key]

    return property(fget, fset, fdel, 'Get or set the optionVar: {0}'.format(key))
