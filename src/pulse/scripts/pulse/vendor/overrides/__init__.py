from .enforce import EnforceOverrides
import sys

if sys.version_info < (3, 11):
    from .final import final
else:
    from typing import final
from .overrides import __VERSION__, overrides, override


__all__ = [
    "__VERSION__",
    "override",
    "overrides",
    "final",
    "EnforceOverrides",
]
