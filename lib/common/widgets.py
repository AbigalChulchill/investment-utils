from typing import Any

from rich.progress import track as _rich_track
from rich.console import Console


def track(*args: Any, **kwargs: Any):
    """a transient monochromatic progress bar
    """
    return _rich_track(*args, **kwargs, transient=True, console=Console(no_color=True))
