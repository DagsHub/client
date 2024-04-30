import importlib.util

is_mlflow_installed = importlib.util.find_spec("mlflow") is not None
