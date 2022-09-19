import os
from dagshub.streaming import install_hooks


def test_torch_load():
    install_hooks(project_root="/Users/simonlousky/workspace/dags/projects/baby-yoda-segmentor")
    import torch
    for my_tple in os.walk("."):
        print(my_tple)



test_torch_load()
