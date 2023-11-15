import rich.progress

from dagshub.common import rich_console, config


def get_rich_progress(*additional_columns, transient=True):
    progress = rich.progress.Progress(
        rich.progress.SpinnerColumn(),
        *rich.progress.Progress.get_default_columns(),
        *additional_columns,
        console=rich_console,
        transient=transient,
        disable=config.quiet
    )
    return progress
