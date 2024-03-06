"""
Just a simple CNN for MNIST.
Note that you need to define which values you want to log when returning from training_step, validation_end
"""

from pathlib import Path
import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader
from torchvision.datasets import MNIST
import torchvision.transforms as transforms
from argparse import ArgumentParser

import pytorch_lightning as pl


class MnistModel(pl.LightningModule):

    def __init__(self, batch_size, learning_rate, data_dir=None):
        super(MnistModel, self).__init__()
        # not the best model...
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.conv1 = torch.nn.Conv2d(1, 16, 3)
        self.relu1 = torch.nn.ReLU()
        self.conv2 = torch.nn.Conv2d(16, 8, 3)
        self.relu2 = torch.nn.ReLU()
        self.maxpool2 = torch.nn.MaxPool2d(3)
        self.fc = torch.nn.Linear(8 * 8 * 8, 10)
        # Default to examples/MNIST dir, relative to this script
        self.data_dir = data_dir or Path(__file__).parents[1]

    def forward(self, x):
        layer1 = self.relu1(self.conv1(x))
        layer2 = self.maxpool2(self.relu2(self.conv2(layer1)))
        return self.fc(layer2.view(layer2.shape[0], -1))

    def training_step(self, batch, batch_idx):
        # REQUIRED
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        return self.log("loss", loss)

    def validation_step(self, batch, batch_idx):
        # OPTIONAL
        x, y = batch
        y_hat = self.forward(x)
        return {"val_loss": F.cross_entropy(y_hat, y)}

    def validation_end(self, outputs):
        # OPTIONAL
        avg_loss = torch.stack([x["val_loss"] for x in outputs]).mean()
        return self.log("avg_val_loss", avg_loss, prog_bar=True)

    def configure_optimizers(self):
        # REQUIRED
        # can return multiple optimizers and learning_rate schedulers
        return torch.optim.Adam(self.parameters(), lr=self.learning_rate)

    def train_dataloader(self):
        # REQUIRED
        return DataLoader(
            MNIST(self.data_dir, train=True, download=True, transform=transforms.ToTensor()), batch_size=self.batch_size
        )

    def val_dataloader(self):
        # OPTIONAL
        return DataLoader(
            MNIST(self.data_dir, train=True, download=True, transform=transforms.ToTensor()), batch_size=self.batch_size
        )

    def test_dataloader(self):
        # OPTIONAL
        return DataLoader(
            MNIST(self.data_dir, train=True, download=True, transform=transforms.ToTensor()), batch_size=self.batch_size
        )

    @staticmethod
    def add_model_specific_args(parent_parser):
        """
        Specify the hyperparams for this LightningModule
        """
        # MODEL specific
        parser = ArgumentParser(parents=[parent_parser])
        parser.add_argument("--learning_rate", default=0.02, type=float)
        parser.add_argument("--batch_size", default=32, type=int)

        # training specific (for this model)
        parser.add_argument("--max_nb_epochs", default=2, type=int)

        return parser
