"""
This file runs the main training/val loop, etc... using Lightning Trainer    
"""

from argparse import ArgumentParser
from pytorch_lightning import Trainer
from pytorch_lightning_dagshub import DAGsHubLogger


def import_model():
    """
    Ugly hack to be able to import the model from ../mnist_model.py
    """
    import os
    examples_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    import sys
    sys.path.append(examples_dir)
    from mnist_model import MnistModel
    return MnistModel


if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--gpus', type=str, default=None)

    MnistModel = import_model()

    # give the module a chance to add own params
    # good practice to define LightningModule speficic params in the module
    parser = MnistModel.add_model_specific_args(parser)

    # parse params
    hparams = parser.parse_args()

    # init module
    model = MnistModel(hparams)

    # most basic trainer, uses good defaults
    trainer = Trainer(
        max_nb_epochs=hparams.max_nb_epochs,
        gpus=hparams.gpus,
        val_check_interval=0.2,
        logger=DAGsHubLogger(),  # This is the main point - use the DAGsHub logger!
        default_save_path='lightning_logs',
    )
    trainer.fit(model)
