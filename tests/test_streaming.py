import os
from dagshub.streaming import install_hooks


def test_torch_load():
    install_hooks(project_root="/Users/simonlousky/workspace/dags/user_repos/public/SavtaDepth")
    for my_tple in os.walk("src"):
        print(my_tple)



test_torch_load()
