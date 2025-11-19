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



def get_goal_features(model, model_config, image: PILImage.Image, goal_image: PILImage.Image, device: torch.device, current_obs: PILImage.Image = None) -> torch.Tensor:
    context_queue = []
    goal_features = None

    # Replicating the same behavior as in navigate.py but effectively goal_obs will only look at current_obs
    while len(context_queue) < model_config["context_size"] + 1: # see navigate.py callback_obs function
        context_queue.append(image)
    
    # if current_obs is None:
    #     current_obs = image

    # context_queue.append(current_obs)  # add current observation at the end
    # print("Context queue length for goal features:", len(context_queue))

    # same
    # print(model.vision_encoder.context_size)
    # print(model_config["context_size"])

    with torch.no_grad():
        # Preprocess both obs and goal images the same way as training
        obs_img = transform_images(context_queue, model_config["image_size"], center_crop=False).to(device)
        print("obs_img shape:", obs_img.shape)
        goal_img = transform_images(goal_image, model_config["image_size"], center_crop=False).to(device)

        last_frame = obs_img[:, 3*model_config["context_size"]:, :, :] #
        obsgoal_img = torch.cat([last_frame, goal_img], dim=1)

        # obs_img shape: torch.Size([1, 18, 96, 96])
        # goal_img shape: torch.Size([1, 3, 96, 96])
        # last_frame shape: torch.Size([1, 3, 96, 96])
        # obsgoal_img shape: torch.Size([1, 6, 96, 96])

        features = model.vision_encoder.goal_encoder.extract_features(obsgoal_img)
        features = model.vision_encoder.goal_encoder._avg_pooling(features)

        if model.vision_encoder.goal_encoder._global_params.include_top:
            features = features.flatten(start_dim=1)
            features = model.vision_encoder.goal_encoder._dropout(features)

        goal_features = model.vision_encoder.compress_goal_enc(features) # see nomad_vint.py line 47

    return goal_features







def get_image_features(model, model_config, past_obs: PILImage.Image, device: torch.device, current_obs: PILImage.Image) -> torch.Tensor:
    context_queue = []
    obs_features = None

    if current_obs is None:
        current_obs = past_obs

    while len(context_queue) < model_config["context_size"] + 1: # see navigate.py callback_obs function
        context_queue.append(past_obs)
    # print("Context queue length:", len(context_queue)) # 5
    # print(model.vision_encoder.context_size) # 3
    # print(model_config["context_size"]) # 3

    # Adding current observation as the last image in the context queue
    context_queue.append(current_obs) # 6 like in the paper where 6 is current obs
 

    obs_images = transform_images(context_queue, model_config["image_size"], center_crop=False).to(device)
    obs_images = torch.split(obs_images, 3, dim=1)
    obs_images = torch.cat(obs_images, dim=0)            

    with torch.no_grad():
        # Run through observation encoder
        obs_features = model.vision_encoder.obs_encoder.extract_features(obs_images)
        obs_features = model.vision_encoder.obs_encoder._avg_pooling(obs_features)

        if model.vision_encoder.obs_encoder._global_params.include_top:
            obs_features = obs_features.flatten(start_dim=1)
            obs_features = model.vision_encoder.obs_encoder._dropout(obs_features)

        # Final projection to obs_encoding_size
        obs_features = model.vision_encoder.compress_obs_enc(obs_features) # see nomad_vint.py line 41

    return obs_features



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


    print("----------Analyzing goal image with each image in topomap: Similiraty should increase as images get closer to goal node ------------")

    # model_goal_img_path = "/workspace/metrics/medias/ref_bunker_mist_corridor_3.png"
    # model_goal_image = PILImage.open(model_goal_img_path)


    # for i in range(11):
    #     print(f"------------------- Topomap bunker_mist_corridor image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_corridor/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    #     print("Analyzing encoder output from exact same images from topomap from start to end:")
    #     feat_goal = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=obs_topomap, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")


    # model_goal_img_path = "/workspace/metrics/medias/bunker_mist_corridor_sunFlare_physic_last_obs.png"
    # model_goal_image = PILImage.open(model_goal_img_path)


    # for i in range(11):
    #     print(f"------------------- Topomap bunker_mist_corridor_sunFlare_physic image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_corridor_sunFlare_physic/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")


    # print("----------Analyzing same image passed to obs_encoder and goal encoder ------------")

    goal_img_path = "/workspace/metrics/medias/ref_bunker_mist_corridor_3.png"
    goal_image = PILImage.open(goal_img_path)

    obs_img_path = "/workspace/metrics/medias/act_bunker_mist_corridor_3.png"
    obs_last_img = PILImage.open(obs_img_path)

    # feat_obs = get_image_features(model=model, 
    #                               model_config=model_config, 
    #                               past_obs=obs_last_img, 
    #                               device=device, 
    #                               current_obs=None).cpu().numpy().squeeze()

    # feat_goal = get_goal_features(model=model, 
    #                               model_config=model_config, 
    #                               image=goal_image, 
    #                               goal_image=goal_image, 
    #                               device=device).cpu().numpy().squeeze()


    # print("Feature of the observed image:", feat_obs.shape)
    # print("Feature of the goal image:", feat_goal.shape)


    # norms = np.linalg.norm(feat_obs, axis=1)
    # print("Norms of the observation features:", norms)
    # print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    # print("Shape of goal features:", feat_goal.shape)


    # print("--------------Analyzing different images for goal encoder------------------")

    # print("Test: Similar images but not identical")
    # feat_goal = get_goal_features(model=model, 
    #                               model_config=model_config, 
    #                               image=obs_last_img, 
    #                               goal_image=goal_image, 
    #                               device=device).cpu().numpy().squeeze()
    # print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    # print("Shape of goal features:", feat_goal.shape)


    # print("Test: Closest img in topomap from actual")
    # obs_img_path = "/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_corridor/9.png"
    # obs_last_img = PILImage.open(obs_img_path)
    # feat_goal = get_goal_features(model=model, 
    #                               model_config=model_config, 
    #                               image=obs_last_img, 
    #                               goal_image=obs_last_img, 
    #                               device=device).cpu().numpy().squeeze()
    # print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    # print("Shape of goal features:", feat_goal.shape)
    

    # print("SWICTH Test: Similar images but not identical")
    # feat_goal = get_goal_features(model=model, 
    #                               model_config=model_config, 
    #                               image=goal_image, 
    #                               goal_image=obs_last_img, 
    #                               device=device).cpu().numpy().squeeze()
    # print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    # print("Shape of goal features:", feat_goal.shape)



    # print("Test: Unrelated images ")
    # goal_img_path = "/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_corridor/3.png"
    # goal_image = PILImage.open(goal_img_path)

    # obs_img_path = "/workspace/src/visualnav-transformer/deployment/topomaps/images/mist_office_v1/5.png"
    # obs_last_img = PILImage.open(obs_img_path)

    # feat_goal = get_goal_features(model=model, 
    #                               model_config=model_config, 
    #                               image=obs_last_img, 
    #                               goal_image=goal_image, 
    #                               device=device).cpu().numpy().squeeze()
    # print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    # print("Shape of goal features:", feat_goal.shape)


    # print("Test: Completely different images CSA Tunnel and Lab office")
    # goal_img_path = "/workspace/src/visualnav-transformer/deployment/topomaps/images/csa_tunnel/0.png"
    # goal_image = PILImage.open(goal_img_path)

    # obs_img_path = "/workspace/src/visualnav-transformer/deployment/topomaps/images/new_lab/7.png"
    # obs_last_img = PILImage.open(obs_img_path)

    # feat_goal = get_goal_features(model=model, 
    #                               model_config=model_config, 
    #                               image=obs_last_img, 
    #                               goal_image=goal_image, 
    #                               device=device).cpu().numpy().squeeze()
    # print("Norm of goal features:", np.linalg.norm(feat_goal), "\n")
    # print("Shape of goal features:", feat_goal.shape)


    # print("--------------Analyzing radius 10, no_aug, rain_torrential, sunFlare_physic------------------")
    # # print("NO_AUG")
    # model_goal_image_path = "/workspace/metrics/medias/bunker_mist_office_17nov_no_augmentation_rad_10_trial_1_last.png"
    # model_goal_image = PILImage.open(model_goal_image_path)
    # for i in range(10):
    #     print(f"------------------- Topomap bunker_mist_corridor_no_augmentation image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_office_17nov/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal_1 = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal_1), "\n")

    #     print(f"Reference {i}:")
    #     feat_goal_2 = get_goal_features(model=model, 
    #                                     model_config=model_config, 
    #                                     image=obs_topomap, 
    #                                     goal_image=obs_topomap, 
    #                                     device=device).cpu().numpy().squeeze()
    #     print("Norm of Reference features:", np.linalg.norm(feat_goal_2))
    #     print("Differences in norms:", np.linalg.norm(feat_goal_2) - np.linalg.norm(feat_goal_1), "\n")  

    # print("RAIN_TORRENTIAL")
    # model_goal_image_path = "/workspace/metrics/medias/bunker_mist_office_17nov_rain_torrential_rad_10_trial_1_last.png"
    # model_goal_image = PILImage.open(model_goal_image_path)
    # for i in range(10):
    #     print(f"------------------- Topomap bunker_mist_corridor_rain_torrential image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_office_17nov_rain_torrential/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal_1 = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal_1), "\n")

    #     print(f"Reference {i}:")
    #     feat_goal_2 = get_goal_features(model=model, 
    #                                     model_config=model_config, 
    #                                     image=obs_topomap, 
    #                                     goal_image=obs_topomap, 
    #                                     device=device).cpu().numpy().squeeze()
    #     print("Norm of Reference features:", np.linalg.norm(feat_goal_2))
    #     print("Differences in norms:", np.linalg.norm(feat_goal_2) - np.linalg.norm(feat_goal_1), "\n")

    # print("SUNFLARE_PHYSIC")
    # model_goal_image_path = "/workspace/metrics/medias/bunker_mist_office_17nov_sunFlare_physic_rad_10_trial_2_last.png"
    # model_goal_image = PILImage.open(model_goal_image_path)
    # for i in range(10):
    #     print(f"------------------- Topomap bunker_mist_corridor_sunFlare_physic image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_office_17nov_sunFlare_physic/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal_1 = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal_1), "\n")

    #     print(f"Reference {i}:")
    #     feat_goal_2 = get_goal_features(model=model, 
    #                                     model_config=model_config, 
    #                                     image=obs_topomap, 
    #                                     goal_image=obs_topomap, 
    #                                     device=device).cpu().numpy().squeeze()
    #     print("Norm of Reference features:", np.linalg.norm(feat_goal_2))
    #     print("Differences in norms:", np.linalg.norm(feat_goal_2) - np.linalg.norm(feat_goal_1), "\n")



    print("--------------Analyzing distances at model observe goal image and topomap images------------------")
    print("NO_AUG")
    model_goal_image_path = "/workspace/metrics/medias/bunker_mist_office_17nov_no_augmentation_rad_10_trial_4_last.png"
    model_goal_image = PILImage.open(model_goal_image_path)

    with open('/workspace/metrics/medias/bunker_mist_office_17nov_no_augmentation_rad_10_trial_4_last_distances.npy', 'rb') as f:
            dists = np.load(f)
            print("Distances:", dists)

    for i in range(10):
        print(f"------------------- Topomap bunker_mist_corridor_no_augmentation image index: {i} --------------------")

        obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_office_17nov/{i}.png"
        obs_topomap = PILImage.open(obs_img_path)

        print("Comparing observed goal from model and topomap images from start to end:")
        feat_goal_1 = get_goal_features(model=model, 
                                    model_config=model_config, 
                                    image=obs_topomap, 
                                    goal_image=model_goal_image, 
                                    device=device).cpu().numpy().squeeze()
        print("Norm of goal features:", np.linalg.norm(feat_goal_1))

        print(f"Reference {i}:")
        feat_goal_2 = get_goal_features(model=model, 
                                        model_config=model_config, 
                                        image=obs_topomap, 
                                        goal_image=obs_topomap, 
                                        device=device).cpu().numpy().squeeze()
        print("Norm of Reference features:", np.linalg.norm(feat_goal_2))
        print("Differences in norms:", np.linalg.norm(feat_goal_2) - np.linalg.norm(feat_goal_1))


    # print("RAIN_TORRENTIAL")
    # model_goal_image_path = "/workspace/metrics/medias/bunker_mist_office_17nov_rain_torrential_rad_10_trial_4_last.png"
    # model_goal_image = PILImage.open(model_goal_image_path)

    # with open('/workspace/metrics/medias/bunker_mist_office_17nov_rain_torrential_rad_10_trial_4_last_distances.npy', 'rb') as f:
    #         dists = np.load(f)
    #         print("Distances:", dists)

    # for i in range(10):
    #     print(f"------------------- Topomap bunker_mist_corridor_rain_torrential image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_office_17nov_rain_torrential/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal_1 = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal_1))

    #     print(f"Reference {i}:")
    #     feat_goal_2 = get_goal_features(model=model, 
    #                                     model_config=model_config, 
    #                                     image=obs_topomap, 
    #                                     goal_image=obs_topomap, 
    #                                     device=device).cpu().numpy().squeeze()
    #     print("Norm of Reference features:", np.linalg.norm(feat_goal_2))
    #     print("Differences in norms:", np.linalg.norm(feat_goal_2) - np.linalg.norm(feat_goal_1))

    # print("SUNFLARE_PHYSIC")
    # model_goal_image_path = "/workspace/metrics/medias/bunker_mist_office_17nov_sunFlare_physic_rad_10_trial_4_last.png"
    # model_goal_image = PILImage.open(model_goal_image_path)

    # with open('/workspace/metrics/medias/bunker_mist_office_17nov_sunFlare_physic_rad_10_trial_4_last_distances.npy', 'rb') as f:
    #         dists = np.load(f)
    #         print("Distances:", dists)

    # for i in range(10):
    #     print(f"------------------- Topomap bunker_mist_corridor_sunFlare_physic image index: {i} --------------------")

    #     obs_img_path = f"/workspace/src/visualnav-transformer/deployment/topomaps/images/bunker_mist_office_17nov_sunFlare_physic/{i}.png"
    #     obs_topomap = PILImage.open(obs_img_path)

    #     print("Comparing observed goal from model and topomap images from start to end:")
    #     feat_goal_1 = get_goal_features(model=model, 
    #                                 model_config=model_config, 
    #                                 image=obs_topomap, 
    #                                 goal_image=model_goal_image, 
    #                                 device=device).cpu().numpy().squeeze()
    #     print("Norm of goal features:", np.linalg.norm(feat_goal_1))

    #     print(f"Reference {i}:")
    #     feat_goal_2 = get_goal_features(model=model, 
    #                                     model_config=model_config, 
    #                                     image=obs_topomap, 
    #                                     goal_image=obs_topomap, 
    #                                     device=device).cpu().numpy().squeeze()
    #     print("Norm of Reference features:", np.linalg.norm(feat_goal_2))
    #     print("Differences in norms:", np.linalg.norm(feat_goal_2) - np.linalg.norm(feat_goal_1))












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



