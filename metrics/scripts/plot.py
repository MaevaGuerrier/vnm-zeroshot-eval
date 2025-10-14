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
    df_ref_traj = df[df['augmentation'] == 'reference'].copy()
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




def plot_envtype_environments(df: pd.DataFrame,
                              ref_augment: str = 'reference',
                              figsize_per_env=(5, 5)):
    """
    Plot (pose_x, pose_y) results grouped by env_type.
    Each env_type has a single figure containing one subplot per environment.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ['pose_x', 'pose_y', 'robot', 'environment', 'env_type', 'augmentation', 'dist_to_goal'].
    ref_augment : str, optional
        Reference augmentation name (default: 'original').
    figsize_per_env : tuple, optional
        Size of each subplot (default: (5, 5)).
    """

    required_cols = ['pose_x', 'pose_y', 'robot', 'environment', 'env_type', 'augmentation', 'dist_to_goal']
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    df = df.copy()
    env_types = df['env_type'].unique()

    for env_type in env_types:
        subset = df[df['env_type'] == env_type]
        envs = subset['environment'].unique()
        n_envs = len(envs)

        # Compute subplot grid
        ncols = min(3, n_envs)
        nrows = int(np.ceil(n_envs / ncols))

        fig, axes = plt.subplots(
            nrows, ncols,
            figsize=(figsize_per_env[0]*ncols, figsize_per_env[1]*nrows),
            squeeze=False
        )

        sns.set(style="whitegrid")
        palette = sns.color_palette("tab10", n_colors=subset['augmentation'].nunique())
        color_map = dict(zip(subset['augmentation'].unique(), palette))

        for i, env_name in enumerate(envs):
            ax = axes[i // ncols, i % ncols]
            env_df = subset[subset['environment'] == env_name]
            robots = env_df['robot'].unique()

            for robot in robots:
                robot_df = env_df[env_df['robot'] == robot]
                ref_row = robot_df[robot_df['augmentation'] == ref_augment]

                if ref_row.empty:
                    continue

                ref_x = ref_row['pose_x'].values[0]
                ref_y = ref_row['pose_y'].values[0]

                for _, row in robot_df.iterrows():
                    aug = row['augmentation']
                    color = color_map.get(aug, 'gray')

                    if aug == ref_augment:
                        ax.scatter(ref_x, ref_y, color='black', s=120, marker='o', label=f"{robot} ({ref_augment})")
                    else:
                        ax.scatter(row['pose_x'], row['pose_y'], color=color, s=60, marker='x', label=f"{robot}-{aug}")
                        ax.plot([row['pose_x'], ref_x], [row['pose_y'], ref_y],
                                color=color, linestyle='--', linewidth=1.2)
                        if not pd.isna(row['dist_to_goal']):
                            dist_text = f"{row['dist_to_goal']:.2e}"
                            mid_x = (row['pose_x'] + ref_x) / 2
                            mid_y = (row['pose_y'] + ref_y) / 2
                            ax.text(mid_x, mid_y, dist_text, fontsize=8, color=color,
                                    ha='center', va='bottom')

            ax.set_title(f"{robot} - {env_name}", fontsize=10)
            ax.set_xlabel("Pose X")
            ax.set_ylabel("Pose Y")
            ax.grid(True)
            ax.legend(fontsize=7, loc='upper right')

        # Remove unused subplots
        for j in range(i+1, nrows*ncols):
            fig.delaxes(axes[j // ncols, j % ncols])

        fig.suptitle(f"Environment Type: {env_type}", fontsize=14, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()




if __name__ == "__main__":

    reference_header = 'reference'

    config = load_config()
    root_path = config["paths"]["dataframes_dir"]
    df = pd.read_csv(f"{root_path}all_data_20251014-143507.csv") #Index(['pose_x', 'pose_y', 'goal', 'robot', 'environment', 'env_type','augmentation'],

    # print(df.head())

    # PLOTS ODOMETRY BY ROBOT AND ENVIRONMENT
    for robot in df["robot"].unique():
        robot_df = df[df["robot"] == robot]
        for env in robot_df["environment"].unique():
            env_df = robot_df[robot_df["environment"] == env]
            print(env_df.head())
            plot_odometry(df=env_df, title=f"{robot} - {env}", save_path=f"../plots/odometry_{robot}_{env}.png")

    # PLOT DISTANCE FROM GOAL BASED ON LAST POSITION IN DF
    # results = []
    # for robot in df["robot"].unique():
    #     robot_df = df[df["robot"] == robot]
    #     for env in robot_df["environment"].unique():
    #         env_df = robot_df[robot_df["environment"] == env]
    #         last_positions_df = env_df.groupby(['robot', 'environment', 'augmentation']).last().reset_index()
    #         # print(last_positions_df)
    #         ref_traj = last_positions_df[last_positions_df["augmentation"] == reference_header]
    #         ref_traj.reset_index(drop=True, inplace=True) # this has to be done since we access by index below
    #         if ref_traj.empty:
    #             raise ValueError(f"No reference trajectory found for robot {robot} in environment {env}")

    #         augmentations = last_positions_df["augmentation"].unique()
    #         augmentations = np.delete(augmentations, np.where(augmentations == reference_header)) # remove reference from augmentations to compute distance to goal

    #         for aug in augmentations:
    #             curr_df = last_positions_df[last_positions_df["augmentation"] == aug]
    #             curr_df.reset_index(drop=True, inplace=True) # this has to be done since we access by index to compute distance
    #             last_positions_df.loc[last_positions_df["augmentation"] == aug, "dist_to_goal"] = np.sqrt(
    #                 (curr_df.iloc[0]["pose_x"] - ref_traj.iloc[0]["pose_x"]) ** 2 + (curr_df.iloc[0]["pose_y"] - ref_traj.iloc[0]["pose_y"]) ** 2
    #             )
                

            
    #         results.append(last_positions_df)
                
    # final_df = pd.concat(results, ignore_index=True)
    # # print(final_df.head())
    # plot_envtype_environments(final_df, ref_augment=reference_header)

