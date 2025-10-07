import yaml

def load_config(config_path="../config/experiments.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
    



