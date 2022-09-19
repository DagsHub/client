import os
from dagshub.streaming import install_hooks


def test_torch_load():
    install_hooks(project_root="/Users/simonlousky/workspace/dags/projects/baby-yoda-segmentor")
    import torch
    model = torch.load("models/model.pth", map_location=torch.device('cpu'))


test_torch_load()
