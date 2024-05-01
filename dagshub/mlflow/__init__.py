import sys


def wrap_fn(fn):
    print(f"Calling {fn}")


class MlflowMonkeyPatch:
    def __init__(self, original_mlflow):
        self._original_mlflow = original_mlflow

    # TODO: wrap the function wrapper, that handles specific exceptions we want to handle (find out which ones btw)
    # Exception to wrap:
    # - mlflow.exceptions.MlflowException

    def __getattr__(self, item):
        print(f"Getting item: {item}")
        # TODO:
        # - Handle functions
        # - Handle modules (need to also mock out the module)
        return getattr(self._original_mlflow, item)


def patch_mlflow():
    import mlflow

    patch = MlflowMonkeyPatch(mlflow)
    # sys.modules["mlflow"] = patch

    print(mlflow)
    return patch
