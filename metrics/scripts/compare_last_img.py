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


    # Example
    ref_img = get_last_rgb_image("reference.bag", "/camera/color/image_raw")
    act_img = get_last_rgb_image("actual.bag", "/camera/color/image_raw")

    # Save for inspection
    cv2.imwrite("reference_last.png", ref_img)
    cv2.imwrite("actual_last.png", act_img)
