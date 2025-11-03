import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_config
import pandas as pd
import numpy as np
import plotly.express as px




def compute_node_errors(all_data, reference_nodes):
    """
    all_data: dataframe containing pose_x, pose_y, closest_node, robot, environment, augmentation
    reference_nodes: dictionary mapping (robot, env) -> reference dataframe with node_idx, node_x_odom, node_y_odom
    """
    results = []

    # Iterate per (robot, environment, augmentation)
    for (robot, env, _), df_group in all_data.groupby(["robot", "environment", "augmentation"]):
        ref_key = (robot, env)
        if ref_key not in reference_nodes:
            print(f"No reference nodes for ({robot}, {env})")
            continue

        ref_df = reference_nodes[ref_key]

        ref_positions = ref_df[["node_x_odom", "node_y_odom"]].to_numpy()
        poses = df_group[["pose_x", "pose_y"]].to_numpy()

        # Compute pairwise distances
        distances = np.linalg.norm(poses[:, None, :] - ref_positions[None, :, :], axis=2)  # shape (n_poses, n_nodes)

        # Find index of closest node
        closest_ref_idx = np.argmin(distances, axis=1)
        true_nodes = ref_df.iloc[closest_ref_idx]["node_idx"].values # the dataframe index of the closest node is node_idx hint look at dataframes generated in closest_node_analysis

        # Compute node prediction error
        df_group = df_group.copy()
        df_group["true_node"] = true_nodes
        df_group["node_error"] = df_group["closest_node"] - df_group["true_node"]

        results.append(df_group)

    # Merge all groups back together
    return pd.concat(results, ignore_index=True)



# TODO could be like dict where dict nomad: df, care:df
def plot_single_radar_chart(df, metrics=['node_error'], augmentation_type='rain_torrential', 
                            robot_type='limo', environment_type='clearpath_playpen', 
                            algorithm_name='Nomad', color='#FF6B6B'):
    
    filtered_df = df[
        (df['augmentation'] == augmentation_type) &
        (df['robot'] == robot_type) &
        (df['environment'] == environment_type)
    ]
    
    # Calculate mean value for each metric
    metric_values = []
    for metric in metrics:
        metric_values.append(filtered_df[metric].mean()) # mean is already computed in the dataframe
    
    # Create a dataframe for plotting
    plot_df = pd.DataFrame({
        'metric': metrics,
        'value': metric_values,
        'algorithm': [algorithm_name] * len(metrics)
    })
    
    fig = px.line_polar(
        plot_df, 
        r='value',
        theta='metric',
        color='algorithm',
        line_close=True,
        color_discrete_map={algorithm_name: color}
    )
    
    fig.update_traces(fill='toself')
    fig.show()
    
    return fig




if __name__ == "__main__":

    reference_header = 'reference'

    config = load_config()
    root_path = config["paths"]["dataframes_dir"]
    df = pd.read_csv(f"{root_path}all_data_20251014-180242.csv") #Index(['pose_x', 'pose_y', 'goal', 'robot', 'environment', 'env_type','augmentation'],
    limo_clearpath_playpen_nodes_reference_df = pd.read_csv(f"{root_path}closest_node_analysis/limo_clearpath_playpen_nodes_reference.csv") # node_idx, node_x_odom, node_y_odom

    reference_nodes = {
    ("limo", "clearpath_playpen"): limo_clearpath_playpen_nodes_reference_df,
        # add more if needed
    }



    all_data_with_errors = compute_node_errors(df, reference_nodes)
    # print(all_data_with_errors[all_data_with_errors['augmentation'] == 'rain_torrential'][['node_error']].describe())
    # print(all_data_with_errors[all_data_with_errors['augmentation'] == 'rain_torrential'][['node_error']].mean())
    plot_single_radar_chart(all_data_with_errors)





