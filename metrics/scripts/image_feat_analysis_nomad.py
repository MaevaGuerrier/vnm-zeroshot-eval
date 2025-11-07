import argparse
import os
import torch
import yaml


from utils_nomad import load_model



def _load_model(model_path: str, model_config_path:str, device: torch.device):
    
    with open(model_config_path, "r") as f:
        model_config = yaml.safe_load(f)

    model = load_model(model_path, model_config, device).to(device).eval()
    return model, model_config        



def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load feature config
    with open("../config/features.yaml", "r") as f:
        features_config = yaml.safe_load(f)

    model_info = features_config["models"].get(args.model.lower())
    if model_info is None:
        raise ValueError(f"Model {args.model} not found in features config.")

    model_weights_path = model_info["weights_path"]
    model_config_path = model_info["model_config_path"]


    model, model_config = _load_model(model_weights_path, model_config_path, device)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description="Code to run GNM DIFFUSION EXPLORATION on the locobot")
    parser.add_argument(
        "--model",
        "-m",
        default="nomad",
        type=str,
        help="model name (only nomad is supported) (hint: check ../config/models.yaml) (default: nomad)",
    )

    parser.add_argument(
        "--dir",
        "-d",
        default="sim_test",
        type=str,
        help="path to topomap images",
    )


    args = parser.parse_args()
    main(args)



