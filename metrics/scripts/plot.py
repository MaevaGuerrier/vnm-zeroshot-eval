import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_config
import pandas as pd
import numpy as np

def plot_odometry(df, title="", save_path="../plots/", show=False):  
    sns.set(style="darkgrid", context="talk")
    plt.figure(figsize=(8, 6))
    sns.lineplot(
        x=df['pose_x'],
        y=df['pose_y'],
        linewidth=2.5,
        hue=df['augmentation'],
        palette="tab10"
    )
    plt.title(title)
    plt.xlabel("X position [m]")
    plt.ylabel("Y position [m]")
    plt.axis('equal')
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    if show:
        plt.show()
    plt.close()


# sim_reference = bagreader("bags/deploy_normal.bag")
# sim_sun = bagreader("bags/deploy_sun.bag")
# sim_rain = bagreader("bags/deploy_rain.bag")
# # sim_deploy = bagreader('cave_tunnel_v2_nomad.bag')

# odom_reference = sim_reference.message_by_topic("/odom")
# odom_rain = sim_rain.message_by_topic("/odom")
# odom_sun = sim_sun.message_by_topic("/odom")

# df_odom_reference = pd.read_csv(odom_reference)
# df_odom_rain = pd.read_csv(odom_rain)
# df_odom_sun = pd.read_csv(odom_sun)

# x_ref = df_odom_reference["pose.pose.position.x"].to_numpy()
# y_ref = df_odom_reference["pose.pose.position.y"].to_numpy()

# x_rain = df_odom_rain["pose.pose.position.x"].to_numpy()
# y_rain = df_odom_rain["pose.pose.position.y"].to_numpy()

# x_sun = df_odom_sun["pose.pose.position.x"].to_numpy()
# y_sun = df_odom_sun["pose.pose.position.y"].to_numpy()

# # Plot trajectory
# plt.figure(figsize=(8, 6))
# plt.plot(x_ref, y_ref, label="normal deploy")
# plt.plot(x_rain, y_rain, label="rain deploy")
# plt.plot(x_sun, y_sun, label="sun deploy")
# plt.xlabel("X position (m)")
# plt.ylabel("Y position (m)")
# plt.title("comparison")
# plt.legend()
# plt.axis("equal")  # equal scaling for x and y
# plt.grid(True)
# plt.savefig("simple.png")


def get_final_goal_positions(df, goal_col='goal', group_cols=['robot', 'environment', 'augmentation', 'pose_x', 'pose_y']):
    """
    Return the final (pose_x, pose_y) positions for each robot-environment-augmentation combination
    where the goal condition is True.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing ['pose_x', 'pose_y', 'goal', 'robot', 'environment', ...].
    goal_col : str, optional
        Name of the goal column.
    group_cols : list of str, optional
        Columns to group by (e.g., robot, environment, augmentation).

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per group containing the last pose_x, pose_y
        where goal == True.
    """

    df_goal = df[df[goal_col] == True].copy() # HANLDLE OTHER STOPPING CONDITIONS
    df_ref_traj = df[df['augmentation'] == 'original'].copy()
    df_goal = pd.concat([df_goal, df_ref_traj])

    last_goal_df = (
        df_goal
        .sort_values(group_cols)
        .groupby(group_cols, as_index=False)
        .last()[group_cols]
    )

    return last_goal_df



def summarize_goal_distances(df, group_cols=['robot', 'environment', 'augmentation']):
    """
    Summarize distance-to-goal statistics per robot/environment/augmentation combination.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain 'distance_to_goal' and grouping columns.
    group_cols : list of str, optional
        Columns to group by (default: ['robot', 'environment', 'augmentation']).

    Returns
    -------
    pd.DataFrame
        Table with mean, std (or NaN if single sample), and count per group.
    """
    # Safety check
    required_cols = set(group_cols + ['distance_to_goal'])
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns: {required_cols - set(df.columns)}")

    # Group and aggregate
    grouped = (
        df.groupby(group_cols)
        .agg(
            mean_distance=('distance_to_goal', 'mean'),
            std_distance=('distance_to_goal', 'std'),
            count=('distance_to_goal', 'count')
        )
        .reset_index()
    )

    # Replace std with NaN or "—" where count == 1
    grouped.loc[grouped['count'] == 1, 'std_distance'] = np.nan  # or "—" if you prefer
    return grouped




if __name__ == "__main__":

    reference_header = 'original'

    config = load_config()
    root_path = config["paths"]["dataframes_dir"]
    df = pd.read_csv(f"{root_path}all_data_20251008-160502.csv") #Index(['pose_x', 'pose_y', 'goal', 'robot', 'environment', 'env_type','augmentation'],


    # PLOTS ODOMETRY BY ROBOT AND ENVIRONMENT
    # for robot in df["robot"].unique():
    #     robot_df = df[df["robot"] == robot]
    #     for env in robot_df["environment"].unique():
    #         env_df = robot_df[robot_df["environment"] == env]
    #         plot_odometry(df=env_df, title=f"{robot} - {env}", save_path=f"../plots/odometry_{robot}_{env}.png")

    # PLOT DISTANCE FROM GOAL BASED ON LAST POSITION IN DF
    results = []
    for robot in df["robot"].unique():
        robot_df = df[df["robot"] == robot]
        for env in robot_df["environment"].unique():
            env_df = robot_df[robot_df["environment"] == env]
            last_positions_df = env_df.groupby(['robot', 'environment', 'augmentation']).last().reset_index()
            # print(last_positions_df)
            ref_traj = last_positions_df[last_positions_df["augmentation"] == reference_header]
            ref_traj.reset_index(drop=True, inplace=True) # this has to be done since we access by index below
            if ref_traj.empty:
                raise ValueError(f"No reference trajectory found for robot {robot} in environment {env}")

            augmentations = last_positions_df["augmentation"].unique()
            augmentations = np.delete(augmentations, np.where(augmentations == reference_header)) # remove reference from augmentations to compute distance to goal

            for aug in augmentations:
                curr_df = last_positions_df[last_positions_df["augmentation"] == aug]
                curr_df.reset_index(drop=True, inplace=True) # this has to be done since we access by index to compute distance
                last_positions_df.loc[last_positions_df["augmentation"] == aug, "dist_to_goal"] = np.sqrt(
                    (curr_df.iloc[0]["pose_x"] - ref_traj.iloc[0]["pose_x"]) ** 2 + (curr_df.iloc[0]["pose_y"] - ref_traj.iloc[0]["pose_y"]) ** 2
                )
                

            
            results.append(last_positions_df)
                
    final_df = pd.concat(results, ignore_index=True)
    print(final_df.head())