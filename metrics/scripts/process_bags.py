import pandas as pd
from bagpy import bagreader
from pathlib import Path
import re
from tqdm import tqdm
from utils import load_config

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


    for robot_dir in tqdm(base_dir.iterdir(), desc="Processing dataframes"):
        if not robot_dir.is_dir():
            continue
        robot_name = robot_dir.name

        for env_dir in robot_dir.iterdir():
            if not env_dir.is_dir():
                continue
            env_name = (env_dir.name).replace(" ", "")  # Handle spaces in directory names
            env_type = env_map[env_name]

            for aug_dir in env_dir.iterdir():
                if not aug_dir.is_dir():
                    continue
                aug_name = aug_dir.name

                for csv_file in aug_dir.glob("*.csv"):
                    try:
                        df = pd.read_csv(csv_file)
                        df = df[keep_cols]
                        df = df.rename(columns=rename_headers)
                        df["robot"] = robot_name
                        df["environment"] = env_name
                        df["env_type"] = env_type
                        df["augmentation"] = aug_name
                        all_data.append(df)
                    except Exception as e:
                        print(f"[WARN] Skipping {csv_file}: {e}")

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
    print(df.head())


if __name__ == "__main__":
    main()
