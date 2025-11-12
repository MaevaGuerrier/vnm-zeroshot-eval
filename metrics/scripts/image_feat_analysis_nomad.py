import argparse
import os
import torch
import yaml


from utils_nomad import load_model, transform_images, to_numpy

import PIL.Image as PILImage
from typing import List, Tuple
import numpy as np

      

def _load_topomap(topomap_dir: str, topomap_name: str, goal_node: int) -> Tuple[List[PILImage.Image], int]:
    topomap_filenames = sorted(
        os.listdir(os.path.join(topomap_dir, topomap_name)),
        key=lambda x: int(x.split(".")[0]),
    )
    topomap_dir = f"{topomap_dir}/{topomap_name}"
    num_nodes = len(os.listdir(topomap_dir))
    topomap = []
    for i in range(num_nodes):
        image_path = os.path.join(topomap_dir, topomap_filenames[i])
        topomap.append(PILImage.open(image_path))

    assert -1 <= goal_node < len(topomap), "Invalid goal index for the topomap"
    if goal_node == -1:
        goal_node = len(topomap) - 1

    return topomap, goal_node



def get_image_features(model, model_config, image: PILImage.Image, goal_image: PILImage.Image, device: torch.device) -> torch.Tensor:
    context_queue = []
    features = None

    while len(context_queue) <= model_config["context_size"]:
        context_queue.append(image)
    
    # same
    # print(model.vision_encoder.context_size)
    # print(model_config["context_size"])

    if len(context_queue) > model_config["context_size"]:

        obs_images = transform_images(context_queue, model_config["image_size"], center_crop=False)
        obs_images = torch.split(obs_images, 3, dim=1)
        obs_images = torch.cat(obs_images, dim=1) 
        obs_images = obs_images.to(device)

        with torch.no_grad():
            # Preprocess both obs and goal images the same way as training
            obs_img = transform_images(context_queue, model_config["image_size"], center_crop=False).to(device)
            goal_img = transform_images(goal_image, model_config["image_size"], center_crop=False).to(device)

            # Concatenate last observation frame with the goal image (same as in forward)
            obsgoal_img = torch.cat([obs_img[:, 3*model_config["context_size"]:, :, :], goal_img], dim=1)

            # Extract goal features exactly as the model does
            features = model.vision_encoder.goal_encoder.extract_features(obsgoal_img)
            features = model.vision_encoder.goal_encoder._avg_pooling(features)

            if model.vision_encoder.goal_encoder._global_params.include_top:
                features = features.flatten(start_dim=1)
                features = model.vision_encoder.goal_encoder._dropout(features)

            features = model.vision_encoder.compress_goal_enc(features)

    return features








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


    model, model_config = load_model(model_weights_path, model_config_path, device)

    
    # topomap, goal_node = _load_topomap(topomap_dir=model_info["topomap_path"], topomap_name=args.topomap, goal_node=args.goal_node)
    

    # print(model.__dict__)
    # print(model.vision_encoder.goal_encoder.__dict__)
  

    # goal_img = topomap[goal_node]

    goal_img_path = "/workspace/metrics/medias/ref_bunker_mist_corridor_3.png"
    goal_image = PILImage.open(goal_img_path)

    obs_img_path = "/workspace/metrics/medias/act_bunker_mist_corridor_3.png"
    obs_last_img = PILImage.open(obs_img_path)


    feat_obs = get_image_features(model=model, model_config=model_config, image=obs_last_img, goal_image=goal_image, device=device)
    feat_obs = feat_obs.cpu().numpy()

    feat_ref = get_image_features(model=model, model_config=model_config, image=goal_image, goal_image=goal_image, device=device)
    feat_ref = feat_ref.cpu().numpy()
    

    print("Feature of the observed image:", feat_obs.shape)
    print("Feature of the goal image:", feat_ref.shape)


    feat_obs = feat_obs.squeeze()
    feat_ref = feat_ref.squeeze()

    # Euclidean distance
    # euclidean_dist = np.linalg.norm(feat_obs - feat_ref)

    # # Cosine similarity
    # cosine_sim = np.dot(feat_obs, feat_ref) / (np.linalg.norm(feat_obs) * np.linalg.norm(feat_ref))

    # # L1 distance (Manhattan)
    # l1_dist = np.sum(np.abs(feat_obs - feat_ref))

    # # Normalized Euclidean (so you can compare across scales)
    # normed_euc = euclidean_dist / (np.linalg.norm(feat_obs) + np.linalg.norm(feat_ref))


    # Cosine similarity → how aligned the two embeddings are (1.0 means same direction, 0 means orthogonal).
    # Euclidean distance → how far apart they are in the latent space.
    # L1 distance → how much activation pattern differs dimension-wise.
    # print(f"Euclidean distance: {euclidean_dist:.4f}") but I need more data
    # print(f"Cosine similarity: {cosine_sim:.4f}") # Two vectors are orthogonal if their cosine similarity is 0 — meaning they encode completely independent information.
    # print(f"L1 distance: {l1_dist:.4f}")
    # print(f"Normalized Euclidean: {normed_euc:.4f}")



    import matplotlib.pyplot as plt
    from sklearn.decomposition import PCA
    import numpy as np

    # Suppose feat_obs and feat_ref are (1,256)
    features = np.vstack([feat_obs, feat_ref])

    pca = PCA(n_components=2)
    proj = pca.fit_transform(features)

    plt.scatter(proj[0,0], proj[0,1], color='blue', label='Observation')
    plt.scatter(proj[1,0], proj[1,1], color='red', label='Goal')
    plt.plot(proj[:,0], proj[:,1], 'k--', alpha=0.5)
    plt.legend()
    plt.title("PCA Projection of Feature Vectors")
    plt.show()























if __name__ == "__main__":
    parser = argparse.ArgumentParser(
    description="Image and feature analysis script for NOMAD model")
    parser.add_argument(
        "--model",
        "-m",
        default="nomad",
        type=str,
        help="model name (only nomad is supported) (hint: check ../config/models.yaml) (default: nomad)",
    )

    parser.add_argument(
        "--topomap",
        "-t",
        default=None,
        type=str,
        help="Name of the topomap (topomap folder path is specified in ../config/features.yaml) (default: sim_test)",
    )

    parser.add_argument(
        "--goal-node",
        "-g",
        default=-1,
        type=int,
        help="""goal node index in the topomap (if -1, then the goal node is 
        the last node in the topomap) (default: -1)""",
    )

    args = parser.parse_args()
    main(args)



