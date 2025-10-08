import pandas as pd
from bagpy import bagreader
from pathlib import Path
import re
from tqdm import tqdm
from utils import load_config
from collections import defaultdict
import time

# TODO make workers for multiprocess



def filter_by_start_stop(df, start_status, stop_status):
    start_idx = df.index[df["status"] == start_status].min()  # get first matching index
    if pd.notna(start_idx):  # ensure it exists
        df = df.loc[start_idx:].reset_index(drop=True)
    stop_idx = df.index[df["status"] == stop_status].min()
    if pd.notna(stop_idx):
        df = df.loc[:stop_idx].reset_index(drop=True)

    return df


def process_bag_to_df(bag_path, bag_name, topics, output_dir):
    bag = bagreader(bag_path)

    dataframes = {}

    for name, topic in topics.items():
        if name in ["status", "ready_flag", "stop_flag", "intervention_flag"]: # TODO remove status one done when collecting bags
            continue   
        csvfile = bag.message_by_topic(topic)
        df = pd.read_csv(csvfile)        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = f"{output_dir}{bag_name}_{name}.csv"
        df.to_csv(output_file, index=False)


def find_bag_files(bag_dir):
    # return list(Path(bag_dir).rglob("*.bag"))
    return [str(path) for path in Path(bag_dir).rglob("*.bag")] # done for now since bagreader needs str


# TODO filter_by_start_stop
# TODO if reach goal then becomes stop flag
# dataframes = filter_by_start_stop(dataframes, topics.get("ready_flag"), topics.get("stop_flag"))

def load_all_data(base_dir, env_map, config_data_header):
    base_dir = Path(base_dir)
    all_data = []
    keep_cols = list(config_data_header.values()) 
    rename_headers = {v: k for k, v in config_data_header.items()} # we have a uniform data structure but odom pose for example is robot dependant, see config experiments.yaml data_header tag


    for robot_dir in base_dir.iterdir():
        robot_name = robot_dir.name
        for env_dir in robot_dir.iterdir():
            env_name = env_dir.name
            env_type = env_map.get(env_name, "unknown")
            for aug_dir in env_dir.iterdir():
                aug_name = aug_dir.name

                dfs = [pd.read_csv(f) for f in aug_dir.glob(f"{robot_name}_{env_name}_{aug_name}_*.csv")]
                merged_df = pd.concat(dfs, axis=1)  # TODO use merge if columns overlap later on when adding more topics
                merged_df = merged_df[keep_cols]
                merged_df = merged_df.rename(columns=rename_headers)
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
    augmentations = config["augmentations"]
    env_map = {env: env_type for env_type, env_list in config["environments"].items() for env in env_list}
    environments = list(env_map.keys())

    for bag_file in bag_files:
        bag_name = re.sub(rf'^{config["paths"]["bags_dir"]}|\.bag$', '', bag_file)

        # bag_name = bag_file.stem  ONLY VALID IF GO BACK TO PATH LOGIC# e.g., bunker_mist_office_v1_blur
        #print(f"[INFO] Found bag file: {bag_name}")

        # --- Identify robot (first token before '_') ---
        robot = bag_name.split("_")[0]
        if robot not in config["robots"]:
            #print(f"[WARN] Unknown robot '{robot}' in {bag_name}, skipping.")
            continue

        # --- Identify environment (based on config names, not split position) ---
        env = next((env for env in environments if env in bag_name), None)
        if not env:
            #print(f"[WARN] No known environment found in {bag_name}")
            continue

        # --- Identify augmentation (same logic) ---
        aug = next((a for a in augmentations if a in bag_name), None)
        if not aug:
            #print(f"[WARN] No known augmentation found in {bag_name}")
            continue

        env_type = env_map[env]  # 'sim', 'indoor', or 'outdoor'

        #print(f"[INFO] Robot={robot}, EnvType={env_type}, Env={env}, Aug={aug}")

        process_bag_to_df(
            bag_path=bag_file,
            bag_name=bag_name,
            topics=config["robots"][robot]["topics"],
            output_dir=f"{config['paths']['dataframes_dir']}{robot}/{env}/{aug}/",
        )       
        



    df = load_all_data(config["paths"]["dataframes_dir"], env_map, config["robots"][robot]["data_header"])
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    df.to_csv(f"{config['paths']['dataframes_dir']}all_data_{timestamp}.csv", index=False)


if __name__ == "__main__":
    main()
