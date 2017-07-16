
import re

__all__ = [
    'toCamel',
    'toTitle',
]

def toTitle(name):
    """
    Return a string formatted to 'Title Case'
    """
    if not isinstance(name, basestring):
        return
    return re.sub('([A-Z])', ' \\1', name).title()

def toCamel(name):
    """
    Return a string formatted to 'camelCase'
    """
    split = name.split()
    split[0] = '{0}{1}'.format(split[0][0].lower(), split[0][1:])
    return ''.join(split)
