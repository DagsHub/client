# Hyperparameters as DVC outputs

This example how to set up your hyperparameter file as a [DVC](https://dvc.org) __output__ of the training stage.

This means that you can keep using `pytorch-lightning` directly from the command line, specifying non-default hyperparameters
as command-line arguments. For example:
```bash
python3 mnist_trainer.py --learning-rate 0.004
```

The DAGsHub logger will ensure that these custom hyperparameters are recorded and saved to [`params.yml`](params.yml), so you can save them
in a git commit for knowledge preservation and smart visualization in DAGsHub.  

After the training run finishes, you're happy with the results and want to commit them to git, DVC, and DAGsHub, you can
take a snapshot of the current state with: 
```bash
dvc commit -f ./train.dvc
``` 

The relevant files are:
* [mnist_trainer.py](mnist_trainer.py) - the main script, defines the `pytorch-lightning` Trainer and connects it to the
    [DAGsHubLogger](../../pytorch_lightning_dagshub/logger.py).
* [params.yml](params.yml) - Hyperparameters that were used in the last training run.
    This YAML format is supported by DAGsHub, for smart experiment comparison and display.
* [metrics.csv](metrics.csv) - Output metrics from the training stage. <br/>
    This CSV format is supported by DAGsHub, for smart experiment comparison and display.
* [train.dvc](train.dvc) - The DVC stage file. 

---

Made with 🐶 by [DAGsHub](https://dagshub.com/).
