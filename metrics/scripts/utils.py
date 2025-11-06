import yaml
import torch
import os


def load_config(config_path: str ="../config/", config_name: str ="experiments.yaml"):
    with open(os.path.join(config_path, config_name), "r") as f:
        return yaml.safe_load(f)
    


