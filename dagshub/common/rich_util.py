import rich.progress

from dagshub.common import rich_console, config


def get_rich_progress(*additional_columns):
    progress = rich.progress.Progress(rich.progress.SpinnerColumn(), *rich.progress.Progress.get_default_columns(),
                                      *additional_columns,
                                      console=rich_console, transient=True, disable=config.quiet)
    return progress
