import re


def to_title(name):
    """
    Return a string formatted to 'Title Case'
    """
    if not isinstance(name, str):
        return
    return re.sub("([A-Z])", " \\1", name).title()


def to_camel(name):
    """
    Return a string formatted to 'camelCase'
    """
    split = name.split()
    split[0] = f"{split[0][0].lower()}{split[0][1:]}"
    return "".join(split)
