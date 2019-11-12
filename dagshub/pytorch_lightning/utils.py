import yaml

from argparse import Namespace


def read_hparams(path: str) -> Namespace:
    """
    Use to read some hyperparameters which were previously saved as YAML.
    This is the format used by DAGsHubLogger, and the returned Namespace is compatible with pytorch-lightning models.
    """
    with open(path) as f:
        params = yaml.safe_load(f)
        return Namespace(**params)
