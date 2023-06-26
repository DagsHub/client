import rich.console


def _inside_notebook():
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ModuleNotFoundError:
        return False


force_terminal = False if _inside_notebook() else None

rich_console = rich.console.Console(force_terminal=force_terminal)
