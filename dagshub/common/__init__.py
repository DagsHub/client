import rich.console


def is_inside_notebook():
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except ModuleNotFoundError:
        return False


def is_inside_colab():
    if not is_inside_notebook():
        return False
    from IPython import get_ipython

    return "google.colab" in get_ipython().extension_manager.loaded


force_terminal = False if is_inside_notebook() else None

rich_console = rich.console.Console(force_terminal=force_terminal)
