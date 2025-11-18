import rosbag # conda install -c conda-forge ros-rosbag 

import numpy as np

def get_last_distances(bag_path:str, distance_topic:str) -> np.ndarray:
    dists = None
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, time in bag.read_messages(topics=[distance_topic]):
            dists = np.array(msg.data)
    return dists



if __name__ == "__main__":
    
    aug = "rain_torrential"
    actual_bag_name = f"bunker_mist_office_17nov_{aug}_rad_10_trial_4.bag"

    actual_path = f"/workspace/metrics/bags/{actual_bag_name}"

    distance_topic = "/distances"
    distances = get_last_distances(actual_path, distance_topic)
    print("Last distances:", distances)
    np.save(f"/workspace/metrics/medias/bunker_mist_office_17nov_{aug}_rad_10_trial_4_last_distances.npy", distances)