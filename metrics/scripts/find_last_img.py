import rosbag # conda install -c conda-forge ros-rosbag 
from cv_bridge import CvBridge
import cv2

def get_last_rgb_image(bag_path, image_topic):
    bridge = CvBridge()
    last_img = None
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[image_topic]):
            last_img = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    return last_img





if __name__ == "__main__":

    reference_bag_name = "bunker_mist_corridor_reference.bag"
    actual_bag_name = "bunker_mist_corridor_blur.bag"


    reference_path = f"/workspace/metrics/bags/{reference_bag_name}"
    actual_path = f"/workspace/metrics/bags/{actual_bag_name}"

    img_topic = "/usb_cam/image_raw"


    # Example
    ref_img = get_last_rgb_image(reference_path, img_topic)
    act_img = get_last_rgb_image(actual_path, img_topic)

    # Save for inspection
    cv2.imwrite("/workspace/metrics/medias/reference_last.png", ref_img)
    cv2.imwrite("/workspace/metrics/medias/actual_last.png", act_img)
