import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_config
import pandas as pd
import numpy as np
import os
import rosbag
from typing import Any, Tuple, List, Dict
import pickle
from PIL import Image


def get_process_func(img_func_name: str, odom_func_name: str):
    img_process_func = globals()[img_func_name]
    odom_process_func = globals()[odom_func_name]
    return img_process_func, odom_process_func

def process_images(im_list: List, img_process_func) -> List:
    """
    Process image data from a topic that publishes ros images into a list of PIL images
    """
    images = []
    for img_msg in im_list:
        img = img_process_func(img_msg)
        images.append(img)
    return images

def process_custom_img(msg) -> Image:
    """
    Process image data from a topic that publishes sensor_msgs/Image to a PIL image
    """
    img = np.frombuffer(msg.data, dtype=np.uint8).reshape(
        msg.height, msg.width, -1)
    pil_image = Image.fromarray(img)
    return pil_image

def process_odom(
    odom_list: List,
    odom_process_func: Any,
    ang_offset: float = 0.0,
) -> Dict[np.ndarray, np.ndarray]:
    """
    Process odom data from a topic that publishes nav_msgs/Odometry into position and yaw
    """
    xys = []
    yaws = []
    for odom_msg in odom_list:
        xy, yaw = odom_process_func(odom_msg, ang_offset)
        xys.append(xy)
        yaws.append(yaw)
    return {"position": np.array(xys), "yaw": np.array(yaws)}

def quat_to_yaw(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    w: np.ndarray,
) -> np.ndarray:
    """
    Convert a batch quaternion into a yaw angle
    yaw is rotation around z in radians (counterclockwise)
    """
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t3, t4)
    return yaw

def nav_to_xy_yaw(odom_msg, ang_offset: float) -> Tuple[List[float], float]:
    """
    Process odom data from a topic that publishes nav_msgs/Odometry into position
    """

    position = odom_msg.pose.pose.position
    orientation = odom_msg.pose.pose.orientation
    yaw = (
        quat_to_yaw(orientation.x, orientation.y, orientation.z, orientation.w)
        + ang_offset
    )
    return [position.x, position.y], yaw



def get_images_and_odom(
    bag: rosbag.Bag,
    imtopics: List[str] or str,
    odomtopics: List[str] or str,
    img_process_func: Any,
    odom_process_func: Any,
    rate: float = .66,
    ang_offset: float = 0.0,
) -> Tuple[List, Dict[np.ndarray, np.ndarray]]:
    """
    Get image and odom data from a bag file

    Args:
        bag (rosbag.Bag): bag file
        imtopics (list[str] or str): topic name(s) for image data
        odomtopics (list[str] or str): topic name(s) for odom data
        img_process_func (Any): function to process image data
        odom_process_func (Any): function to process odom data
        rate (float, optional): rate to sample data. Defaults to 4.0.
        ang_offset (float, optional): angle offset to add to odom data. Defaults to 0.0.
    Returns:
        img_data (list): list of PIL images
        traj_data (list): list of odom data
    """
    # check if bag has both topics
    odomtopic = None
    imtopic = None
    if type(imtopics) == str:
        imtopic = imtopics
    else:
        for imt in imtopics:
            if bag.get_message_count(imt) > 0:
                imtopic = imt
                break
    if type(odomtopics) == str:
        odomtopic = odomtopics
    else:
        for ot in odomtopics:
            if bag.get_message_count(ot) > 0:
                odomtopic = ot
                break
    if not (imtopic and odomtopic):
        # bag doesn't have both topics
        return None, None

    synced_imdata = []
    synced_odomdata = []
    # get start time of bag in seconds
    currtime = bag.get_start_time()

    curr_imdata = None
    curr_odomdata = None

    for topic, msg, t in bag.read_messages(topics=[imtopic, odomtopic]):
        if topic == imtopic:
            curr_imdata = msg
        elif topic == odomtopic:
            curr_odomdata = msg
        if (t.to_sec() - currtime) >= 1.0 / rate:
            if curr_imdata is not None and curr_odomdata is not None:
                synced_imdata.append(curr_imdata)
                synced_odomdata.append(curr_odomdata)
                currtime = t.to_sec()

    img_data = process_images(synced_imdata, img_process_func)
    traj_data = process_odom(
        synced_odomdata,
        odom_process_func,
        ang_offset=ang_offset,
    )

    return img_data, traj_data


def get_bag_img_traj_data(bag, img_topic, odom_topic, process_images_fn, process_odom_fn):

    bag_img_data, bag_traj_data = get_images_and_odom(
        bag=bag,
        imtopics=img_topic,
        odomtopics=odom_topic,
        img_process_func=process_images_fn,
        odom_process_func=process_odom_fn,
    )  

    # bag_img_data is a list of images
    # bag_traj_data is a  dictionary -> dict_keys(['position', 'yaw']
    assert len(bag_img_data) == len(bag_traj_data['position']), "Number of images and odometry entries must match"
    return bag_img_data, bag_traj_data
    



def associate_topomap_node_with_odom(bag_img_data, bag_traj_data, output_dir):
    """
    Associates each image node index with odometry (x, y) and saves results.
    Returns a pandas DataFrame with columns:
        [image_index, pose_x, pose_y]
    """
    positions = bag_traj_data["position"]
    n_imgs = len(bag_img_data)
    print(f"Number of images: {n_imgs}")

    df = pd.DataFrame({
        "image_index": range(n_imgs),
        "pose_x": [pos[0] for pos in positions[:n_imgs]],
        "pose_y": [pos[1] for pos in positions[:n_imgs]],
    })
    return df



# TODO later on make checks if already processed
if __name__ == "__main__":

    reference_bag_path = "/workspace/metrics/bags"
    output_dir = "/workspace/metrics/dataframes/closest_node_analysis"

    reference_header = 'reference'

    config = load_config()
    root_path = config["paths"]["dataframes_dir"]
    df = pd.read_csv(f"{root_path}all_data_20251014-180242.csv")


    for robot in df["robot"].unique():
        robot_df = df[df["robot"] == robot]
        for env in robot_df["environment"].unique():
            env_df = robot_df[robot_df["environment"] == env]
            reference_df = env_df[env_df["augmentation"] == reference_header]
            bag_path = os.path.join(reference_bag_path, f"{robot}_{env}_reference.bag")
            print(f"Processing bag: {bag_path}")
            bag = rosbag.Bag(bag_path, "r")

            img_process, odom_process = get_process_func(
                img_func_name=config["robots"][robot]["process_bag_metrics"]["img_process_func"],
                odom_func_name=config["robots"][robot]["process_bag_metrics"]["odom_process_func"]
                )

            bag_img_data, bag_traj_data = get_bag_img_traj_data(
                bag=bag,
                img_topic=config["robots"][robot]["process_bag_metrics"]["image_topic"],
                odom_topic=config["robots"][robot]["topics"]["odom"],
                process_images_fn=img_process, 
                process_odom_fn=odom_process
            )

            node_df = associate_topomap_node_with_odom(
                bag_img_data=bag_img_data,
                bag_traj_data=bag_traj_data,
                output_dir=output_dir
            )


            save_path = os.path.join(output_dir, f"{robot}_{env}_nodes_reference.csv")
            node_df.to_csv(save_path, index=False)


