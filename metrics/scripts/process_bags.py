import pandas as pd
from bagpy import bagreader
from pathlib import Path
import re
from tqdm import tqdm
from utils import load_config
from collections import defaultdict
import time

# TODO make workers for multiprocess



# TODO since we are interested in trajectories I am not keeping track of angular velocities
def filter_start_stop(df):
    trimmed_dfs = []

    # Group by (robot, environment, augmentation)
    for (robot, env, aug), group in df.groupby(["robot", "environment", "augmentation"], sort=False):
    
        group = group.sort_values("time_model").reset_index(drop=True)

        motion_mask = (group["lin_x_model"] != 0.0) | (group["lin_y_model"] != 0.0)
        start_idx = motion_mask.idxmax() if motion_mask.any() else None

        if "goal" in group.columns:
            goal_mask = group["goal"].astype(bool)
            end_idx = goal_mask.idxmax() if goal_mask.any() else None
        else:
            end_idx = None

        if start_idx is not None:
            if end_idx is not None and end_idx > start_idx:
                trimmed_group = group.loc[start_idx:end_idx]
            else:
                trimmed_group = group.loc[start_idx:]
        else:
            trimmed_group = group.copy()

        trimmed_dfs.append(trimmed_group)

    return pd.concat(trimmed_dfs, ignore_index=True)


def process_bag_to_df(bag_path, bag_name, augmentation, topics, output_dir):
    bag = bagreader(bag_path)

    dataframes = {}

    for name, topic in topics.items():  

        if augmentation == "reference" and name != "odom": # only save odom for reference trajectory
            continue
        try:
            csvfile = bag.message_by_topic(topic)
            df = pd.read_csv(csvfile)        
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_file = f"{output_dir}{bag_name}_{name}.csv"
            df.to_csv(output_file, index=False)
        except Exception as e:
            print(f"Error processing {name}: {e}")
            continue


def find_bag_files(bag_dir):
    # return list(Path(bag_dir).rglob("*.bag"))
    return [str(path) for path in Path(bag_dir).rglob("*.bag")] # done for now since bagreader needs str




# Reference trajectories won't have all columns, ensure they exist for concatenation
def ensure_columns(df, keep_cols, fill_value=None):
    for col in keep_cols:
        if col not in df.columns:
            df[col] = fill_value
    return df[keep_cols]


# TODO downslample put it as a variable

# TODO filter_by_start_stop
# TODO if reach goal then becomes stop flag
# dataframes = filter_by_start_stop(dataframes, topics.get("ready_flag"), topics.get("stop_flag"))
def load_all_data(base_dir, env_map, config):
    base_dir = Path(base_dir)
    all_data = []

    # TODO for now I did not see any better way to handle all config and file structure
    # If possible reduce for loop depth
    for robot_dir in base_dir.iterdir():
        if not robot_dir.is_dir():
            continue

        robot_name = robot_dir.name
        robot_cfg = config["robots"][robot_name]
        config_data_header = robot_cfg["data_header"]

        all_target_columns = []
        for submap in config_data_header.values():
            all_target_columns.extend(submap.keys())
        # Remove duplicates while preserving order
        all_target_columns = list(dict.fromkeys(all_target_columns))

        for env_dir in robot_dir.iterdir():
            env_name = env_dir.name
            env_type = env_map.get(env_name, "unknown")

            for aug_dir in env_dir.iterdir():
                aug_name = aug_dir.name
                dfs = []

                for csv_file in aug_dir.glob(f"{robot_name}_{env_name}_{aug_name}_*.csv"):
                    df = pd.read_csv(csv_file)
                    topic_key = re.search(rf"{aug_name}_(.+)\.csv", csv_file.name).group(1)

                    if topic_key in config_data_header:
                        rename_map = config_data_header[topic_key]
                        rename_map = {v: k for k, v in rename_map.items()}
                        df = df.rename(columns=rename_map)

                    dfs.append(df)

                if not dfs:
                    continue

                merged_df = pd.concat(dfs, axis=1)


                ensure_columns(merged_df, all_target_columns)
                merged_df = merged_df[all_target_columns]

                merged_df["robot"] = robot_name
                merged_df["environment"] = env_name
                merged_df["env_type"] = env_type
                merged_df["augmentation"] = aug_name

                merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
                all_data.append(merged_df)

    if not all_data:
        raise ValueError("No data found!")

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df


def main():
    config = load_config()
    bag_files = find_bag_files(config["paths"]["bags_dir"]) # ASSUMPTION RUN INSIDE DOCKER THUS /workspace/metrics/bags is always present
    # augmentations = config["augmentations"]
    env_map = {env: env_type for env_type, env_list in config["environments"].items() for env in env_list}
    environments = list(env_map.keys())

    # import ipdb; ipdb.set_trace()
    for bag_file in bag_files:
        bag_name = re.sub(rf'^{config["paths"]["bags_dir"]}|\.bag$', '', bag_file)
        

        # bag_name = bag_file.stem  ONLY VALID IF GO BACK TO PATH LOGIC# e.g., bunker_mist_office_v1_blur
        #print(f"[INFO] Found bag file: {bag_name}")

        # --- Identify robot (first token before '_') ---
        curr_robot = bag_name.split("_")[0]
        if curr_robot not in config["robots"]:
            print(f"[WARN] Unknown robot '{curr_robot}' in {bag_name}, skipping.")
            continue
        robot = curr_robot

        # --- Identify environment (based on config names, not split position) ---
        env = next((env for env in environments if env in bag_name), None)
        if not env:
            #print(f"[WARN] No known environment found in {bag_name}")
            continue

        aug = re.search(rf"{env}_(.+)", bag_name).group(1)
        # print(f"[INFO] Processing {bag_name}: robot={robot}, env={env}, aug={aug}")
        if aug not in config["augmentations"]:
            print(f"[WARN] No known augmentation {aug} found in {bag_name}, skipping.")
            continue
        

        process_bag_to_df(
            bag_path=bag_file,
            bag_name=bag_name,
            augmentation=aug,
            topics=config["robots"][robot]["topics"],
            output_dir=f"{config['paths']['dataframes_dir']}{robot}/{env}/{aug}/",
        )       
        

    # df = load_all_data(config["paths"]["dataframes_dir"], env_map, config)
    # filtered_df = filter_start_stop(df)
    # timestamp = time.strftime("%Y%m%d-%H%M%S")
    # filtered_df.to_csv(f"{config['paths']['dataframes_dir']}all_data_{timestamp}.csv", index=False)


if __name__ == "__main__":
    main()
