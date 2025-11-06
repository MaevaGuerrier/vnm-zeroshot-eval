import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_config
import pandas as pd
import numpy as np

import plotly.graph_objects as go

def plot_odometry_wo_overtake(df, title, save_path, show=False):  
    sns.set(style="darkgrid", context="talk")
    plt.figure(figsize=(8, 6))
    # sns.lineplot(
    #     x="pose_x",
    #     y="pose_y",
    #     linewidth=2.5,
    #     hue="augmentation",
    #     palette="tab10",
    #     data=df
    # )
    sns.lineplot(
        x="pose_x",
        y="pose_y",
        linewidth=2.0,
        hue="augmentation",
        style="augmentation",
        palette="tab10",
        data=df,
        alpha=0.7
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



# FUNC THAT OPENS LOCALHOST TO VIEW THE 3D PLOT
def plot_3d_trajectories(df, palette=None):

    df = df.copy()
    df["timestep"] = df.groupby(["robot", "environment", "augmentation"]).cumcount()
    
    if palette is None:
        # You can define a custom palette if you want specific colors
        palette = {
        "blur": "#F0F38C", 
        "brightness": "#EB8E75", 
        "fog": "#93EF98",
        "no_augmentation": "#F3C282",
        "rain": "#82F1F5", 
        "rain_drizzle":  "#11BFFE",
        "rain_heavy":  "#7EF9AF",
        "rain_torrential":  '#06D6A0',
        "reference":  "#FF90F9",
        "sunFlare_overlay":  "#EFB6FF",
        "sunFlare_physic":  "#F74269"
        }

    fig = go.Figure()

    for aug_name, group in df.groupby("augmentation"):
        color = palette.get(aug_name, None)

        fig.add_trace(go.Scatter3d(
            x=group["pose_x"],
            y=group["pose_y"],
            z=group["timestep"],
            mode='lines',
            name=aug_name,
            line=dict(width=5, color=color),
            opacity=0.85
        ))

    fig.update_layout(
        title=f"3D Trajectories",
        scene=dict(
            xaxis_title="X position [m]",
            yaxis_title="Y position [m]",
            zaxis_title="Timestep",
            aspectmode='cube'
        ),
        legend=dict(
            title="Augmentation",
            x=1.05,
            y=1,
            borderwidth=1
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    fig.show()
    return fig



def plot_odometry_w_overtake(df, title, save_path=None, show=True):
    """
    Plot odometry trajectory with augmentation color and highlight shaded regions
    where teleoperation (user overtake) occurred.
    """
    sns.set(style="darkgrid", context="talk")
    plt.figure(figsize=(8, 6))

    # Base trajectory
    sns.lineplot(
        x="pose_x",
        y="pose_y",
        linewidth=2.5,
        hue="augmentation",
        palette="tab10",
        data=df,
        legend="full"
    )

    # Identify overtake indices
    overtake_mask = ((df["lin_x_teleop"].fillna(0.0) != 0.0) | (df["lin_y_teleop"].fillna(0.0) != 0.0))
    if overtake_mask.any():
        overtake_indices = np.where(overtake_mask)[0]

        # Group consecutive indices into continuous segments
        segments = np.split(
            overtake_indices, 
            np.where(np.diff(overtake_indices) != 1)[0] + 1
        )

        for seg in segments:
            if len(seg) < 2:
                continue
            plt.plot(
                df.loc[seg, "pose_x"],
                df.loc[seg, "pose_y"],
                color="black",
                linewidth=4,
                alpha=0.8,
                label="User Overtake" if "User Overtake" not in plt.gca().get_legend_handles_labels()[1] else ""
            )

    plt.title(title)
    plt.xlabel("X position [m]")
    plt.ylabel("Y position [m]")
    plt.axis("equal")
    plt.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()


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


def plot_dist_to_goal(df: pd.DataFrame,
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





# def compute_node_errors(all_data, reference_nodes):
#     """
#     all_data: dataframe containing pose_x, pose_y, closest_node, robot, environment, augmentation
#     reference_nodes: dictionary mapping (robot, env) -> reference dataframe with node_idx, node_x_odom, node_y_odom
#     """
#     results = []

#     # Iterate per (robot, environment, augmentation)
#     for (robot, env, aug), df_group in all_data.groupby(["robot", "environment", "augmentation"]):
#         ref_key = (robot, env)
#         if ref_key not in reference_nodes:
#             print(f"No reference nodes for ({robot}, {env})")
#             continue

#         ref_df = reference_nodes[ref_key]

#         ref_positions = ref_df[["node_x_odom", "node_y_odom"]].to_numpy()
#         poses = df_group[["pose_x", "pose_y"]].to_numpy()

#         # Compute pairwise distances
#         distances = np.linalg.norm(poses[:, None, :] - ref_positions[None, :, :], axis=2)  # shape (n_poses, n_nodes)

#         # Find index of closest node
#         closest_ref_idx = np.argmin(distances, axis=1)
#         true_nodes = ref_df.iloc[closest_ref_idx]["node_idx"].values

#         # Compute node prediction error
#         df_group = df_group.copy()
#         df_group["true_node"] = true_nodes
#         df_group["node_error"] = df_group["closest_node"] - df_group["true_node"]

#         results.append(df_group)

#     # Merge all groups back together
#     return pd.concat(results, ignore_index=True)





if __name__ == "__main__":

    reference_header = 'reference'

    config = load_config()
    root_path = config["paths"]["dataframes_dir"] # TODO 
    df_limo = pd.read_csv(f"../dataframes/all_data_20251014-180242.csv") #Index(['pose_x', 'pose_y', 'goal', 'robot', 'environment', 'env_type','augmentation'],
    df_bunker = pd.read_csv(f"../dataframes/all_data_20251029-030058.csv") 


   
    df_bunker['augmentation'].replace({'sunFlare_physic': 'sunflare'}, inplace=True)
    df_bunker['augmentation'].replace({'rain_torrential': 'rain'}, inplace=True)

    df = df_bunker

    print(df["augmentation"].unique())

    #PLOTS ODOMETRY BY ROBOT AND ENVIRONMENT
    for robot in df["robot"].unique():
        robot_df = df[df["robot"] == robot]
        for env in robot_df["environment"].unique():
            env_df = robot_df[robot_df["environment"] == env]
            # import ipdb; ipdb.set_trace()
            ref_df = pd.read_csv("/workspace//metrics/dataframes/bunker/mist_corridor/reference/bunker_mist_corridor_reference_odom.csv")
            ref_df = ref_df[['pose.pose.position.x', 'pose.pose.position.y']].rename(columns={
                'pose.pose.position.x': 'pose_x',
                'pose.pose.position.y': 'pose_y'
            })
            ref_df['augmentation'] = 'reference'
            env_df = pd.concat([env_df, ref_df], ignore_index=True)

            plot_odometry_wo_overtake(df=env_df, title=f"{robot} - {env}", save_path=f"../medias/odometry_{robot}_{env}.png")
            # plot_closest_node(df=env_df, title=f"{robot} - {env}", save_path=f"../medias/closest_node_{robot}_{env}.png")
            # plot_3d_trajectories(df)


    # # PLOT DISTANCE FROM GOAL BASED ON LAST POSITION IN DF
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
    # plot_dist_to_goal(final_df, ref_augment=reference_header)

