import rich.console
from .notebook import is_inside_colab, is_inside_notebook


force_terminal = False if is_inside_notebook() else None

rich_console = rich.console.Console(force_terminal=force_terminal)

__all__ = [
    is_inside_colab.__name__,
    is_inside_notebook.__name__,
    "rich_console",
    "force_terminal",
]
