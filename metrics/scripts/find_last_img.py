import rosbag # conda install -c conda-forge ros-rosbag 
from cv_bridge import CvBridge
import cv2

import numpy as np
from typing import List

def get_last_rgb_image(bag_path:str, image_topic:str) -> np.ndarray:
    bridge = CvBridge()
    last_img = None
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, time in bag.read_messages(topics=[image_topic]):
            last_img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    return last_img


def get_last_n_rgb_images(bag_path:str, image_topic:str, n=4) -> List[np.ndarray]:
    """
    Retrieve the last n RGB images from a given ROS bag topic.
    
    Args:
        bag_path (str): Path to the ROS bag file.
        image_topic (str): Image topic name to extract from.
        n (int): Number of most recent images to retrieve (default = 4).
    
    Returns:
        List[np.ndarray]: List of RGB images in chronological order (oldest to newest).
    """
    bridge = CvBridge()
    images = []

    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, time in bag.read_messages(topics=[image_topic]):
            img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            images.append(img)
            if len(images) > n:
                # Keep only the last n images to save memory
                images.pop(0)

    return images



if __name__ == "__main__":

    reference_bag_name = "bunker_mist_corridor_reference.bag"
    actual_bag_name = "bunker_mist_corridor_blur.bag"


    reference_path = f"/workspace/metrics/bags/{reference_bag_name}"
    actual_path = f"/workspace/metrics/bags/{actual_bag_name}"

    img_topic = "/usb_cam/image_raw"


    # Example
    # ref_img = get_last_rgb_image(reference_path, img_topic)
    # act_img = get_last_rgb_image(actual_path, img_topic)
    ref_imgs = get_last_n_rgb_images(reference_path, img_topic, n=4)
    act_imgs = get_last_n_rgb_images(actual_path, img_topic, n=4)

    # print(f"Retrieved {len(ref_imgs)} reference images and {len(act_imgs)} actual images.")
    # print(f"ref img elm {type(ref_imgs[0])}")
    # print(f"act img elm {type(act_imgs[0])}")
    # print(f"ref {type(ref_imgs)}")
    # print(f"act {type(act_imgs)}")


    # Save for inspection
    # cv2.imwrite("/workspace/metrics/medias/reference_last.png", ref_img)
    # cv2.imwrite("/workspace/metrics/medias/actual_last.png", act_img)

    # for i in range(len(ref_imgs)):
    #     cv2.imwrite(f"/workspace/metrics/medias/ref_bunker_mist_corridor_{i}.png", ref_imgs[i])
    #     cv2.imwrite(f"/workspace/metrics/medias/act_bunker_mist_corridor_{i}.png", act_imgs[i])
