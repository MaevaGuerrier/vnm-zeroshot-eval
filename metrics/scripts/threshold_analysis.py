

import pandas as pd
from bagpy import bagreader
from pathlib import Path
import re
from tqdm import tqdm
from utils import load_config
from collections import defaultdict
import time
import argparse
import sys

# TODO If time do proper logging 
# import logging

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,                 # minimum level to show
#     format="%(levelname)s: %(message)s" # show only the level and message
# )


def get_env_info(config):
    env_map = {env: env_type for env_type, env_list in config["environments"].items() for env in env_list}
    environments = list(env_map.keys())

    return env_map, environments

# since we are interested in trajectories I am not keeping track of angular velocities
def filter_start_stop(df):
    trimmed_dfs = []

    # Group by (robot, environment, augmentation)
    for (_, _, _, _, _), group in df.groupby(["robot", "environment", "threshold", "radius", "trial"], sort=False):
    
        group["lin_x_model"].fillna(0.0, inplace=True)
        group["lin_y_model"].fillna(0.0, inplace=True)
        group['goal'].fillna(False, inplace=True)
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


def process_bag_to_df(bag_path:str, topics: dict):
    print(f"[INFO] Processing bag: {bag_path}")
    bag = bagreader(bag_path)
    
    for topic_name, topic in topics.items():  

        try:
            csvfile = bag.message_by_topic(topic)
            df = pd.read_csv(csvfile)        
        except Exception as e:
            print(f"[WARN] Error processing {topic_name}: The topic may be missing in the bag. This is skipping this topic.")
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

def create_dataframe_from_all_data(base_dir, config):
    base_dir = Path(base_dir)
    all_data = []
    env_map, environments = get_env_info(config)

    # TODO for now I did not see any better way to handle all config and file structure
    # If possible reduce for loop depth
    for conf_dir in base_dir.iterdir():

        if not conf_dir.is_dir():
            continue

        config_name = conf_dir.name
        if config_name not in config['setup_configs']:
            continue

        # print(f"Processing config {config_name}")

        for run in conf_dir.iterdir():

            if not run.is_dir():
                continue


            robot = run.name.split("_")[0]
            # print(f"Current robot: {curr_robot}")

            if robot not in config["robots"]:
                print(f"[WARN] Unknown robot '{robot}' in {run.name}, skipping.")
                continue

            env_name = next((env for env in environments if env in run.name), None)
            if not env_name:
                print(f"[WARN] No known environment found in {run.name}")
                continue


            dfs = []
            ref_df = None

            robot_cfg = config["robots"][robot]
            config_data_header = robot_cfg["data_header"]

            all_target_columns = []
            for submap in config_data_header.values():
                all_target_columns.extend(submap.keys())
            all_target_columns = list(dict.fromkeys(all_target_columns))

            # print(f"all_target_columns: {all_target_columns}")

            env_type = env_map.get(env_name, "unknown")


            threshold = re.search(rf"thres_(\d+)_", run.name).group(1) 
            num_int = int(threshold)
            threshold = num_int / (10 ** (len(threshold) - len(str(num_int))))
            
            radius = re.search(rf"rad_(\d+)_", run.name).group(1)
            
            trial = re.search(rf"trial_(.+)$", run.name).group(1) # trial is last var in file name

            
            # print(f"Processing bag: {run.name}, Robot: {robot}, Environment: {env}, Threshold: {threshold}, Radius: {radius}, Trial: {trial}")

            for csv_file in run.glob(f"*.csv"):
                # print(f"Found csv {csv_file}")
                df = pd.read_csv(csv_file)
                topic_key = re.search(rf"(.+)\.csv", csv_file.name).group(1)
                # print(f"Topic key: {topic_key}")

                if topic_key == "cmd_vel_navigate":
                    topic_key = "cmd_model"
                elif topic_key == "cmd_vel_teleop":
                    topic_key = "cmd_teleop"
                elif topic_key == "topoplan-reached_goal":
                    topic_key = "reached_goal"
                

                # print(f"Topic key: {topic_key}")

                if topic_key in config_data_header:
                    rename_map = config_data_header[topic_key]
                    rename_map = {v: k for k, v in rename_map.items()}
                    # print(f"rename_map topic {topic_key}:")
                    # print(rename_map)
                    df = df.rename(columns=rename_map)
                    df = df[list(rename_map.values())]                    

                if topic_key == "odom":
                    odom_df = df.copy()
                    continue
            
                dfs.append(df)

            # if aug_name == "reference":
            #     ref_df = odom_df.copy()
            #     ref_df["robot"] = robot_name
            #     ref_df["environment"] = env_name
            #     ref_df["env_type"] = env_type
            #     ref_df["augmentation"] = aug_name
            #     # print("REFERENCE COLUMNS:")
            #     # print(ref_df.columns)

            if not dfs:
                continue


            merged_df = odom_df
            for df in dfs:
                merged_df = pd.merge_asof(
                    merged_df,
                    df,
                    on="Time",
                    direction="nearest",
                    tolerance=0.2,
                )

            ensure_columns(merged_df, all_target_columns)
            merged_df = merged_df[all_target_columns]

            merged_df["robot"] = robot
            merged_df["environment"] = env_name
            merged_df["env_type"] = env_type
            merged_df["threshold"] = threshold
            merged_df["radius"] = radius
            merged_df["trial"] = trial
            merged_df["configuration"] = config_name

            all_data.append(merged_df)
            if ref_df is not None:
                all_data.append(ref_df)
            
    if not all_data:
        raise ValueError("No data found!")

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df


def create_dataframes_from_bags():
    config = load_config(config_name="parameters.yaml")
    _, environments = get_env_info(config)
    old_env = None

    for setup in config['setup_configs']:
        bag_path = f"{config['paths']['bags_dir']}{setup}/"


        bag_files = find_bag_files(bag_path) # ASSUMPTION RUN INSIDE DOCKER THUS /workspace/metrics/bags is always present

        for bag_file in bag_files:
            bag_name = re.sub(rf'^{bag_path}|\.bag$', '', bag_file)
            # print(f"bag name: {bag_name}")
            

            robot = bag_name.split("_")[0]
            # print(f"Current robot: {curr_robot}")

            if robot not in config["robots"]:
                print(f"[WARN] Unknown robot '{robot}' in {bag_name}, skipping.")
                continue

            # --- Identify environment (based on config names, not split position) ---
            env = next((env for env in environments if env in bag_name), None)
            if not env:
                print(f"[WARN] No known environment found in {bag_name}")
                continue

            # TODO Uncomment when you have a non corrupted reference file
            # if env != old_env:
            #     ref_bag = f"{config['paths']['dataframes_dir']}{setup}/{env}_reference.bag" # ASSUME FOR PARAM ANALYSIS REF FILES IS {ENV_NAME}_reference.bag
            #     process_bag_to_df(
            #         bag_path=ref_bag,
            #         topics=config["robots"][robot]["topics"],
            #     )  
            
            # old_env = env

            process_bag_to_df(
                bag_path=bag_file,
                topics=config["robots"][robot]["topics"],
            )  




if __name__ == "__main__":

    
    parser = argparse.ArgumentParser(description="Choose exactly one option: create dataframes from bag files: --bag, " \
    "create a single unified dataframe from all data (processed by otpion b before hand): --dataframe " \
    "or plot the results: --plot")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", action="store_true", help="Process bag files")
    group.add_argument("--dataframe", action="store_true", help="Create unified dataframe")
    group.add_argument("--plot", action="store_true", help="Plot results")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.bag:
        print("You selected bag processing")
        create_dataframes_from_bags()
    elif args.dataframe:
        print("You selected dataframe creation")

        config = load_config(config_name="parameters.yaml")

        df = create_dataframe_from_all_data(f"{config['paths']['dataframes_dir']}", config)

        filtered_df = filter_start_stop(df)        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filtered_df.to_csv(f"{config['paths']['dataframes_dir']}all_data_{timestamp}.csv", index=False)

    elif args.plot:
        print("You selected plotting")












