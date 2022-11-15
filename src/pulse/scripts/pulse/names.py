"""
Utils for working with naming conventions.
"""

import re


def to_title(name: str) -> str:
    """
    Return a string formatted to 'Title Case'
    """
    return re.sub("([A-Z])", " \\1", name).title()


def to_pascal(name: str) -> str:
    """
    Return a string formatted to 'PascalCase'
    """
    return to_title(name).replace(" ", "")


def to_camel(name: str) -> str:
    """
    Return a string formatted to 'camelCase'
    """
    split = name.split()
    split[0] = f"{split[0][0].lower()}{split[0][1:]}"
    return "".join(split)
