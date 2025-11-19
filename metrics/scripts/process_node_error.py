import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_config
import pandas as pd
import numpy as np

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




def plot_trajectory_node_comparison(reference_df, actual_df, title="Trajectory Comparison", show=True):
    """
    Plot reference nodes and actual trajectory with predicted nodes.
    
    Parameters:
    -----------
    reference_df : DataFrame
        Columns: ['node_idx', 'node_x_odom', 'node_y_odom']
    actual_df : DataFrame
        Columns: ['pose_x', 'pose_y', 'closest_node']
    title : str
        Plot title
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Extract data
    ref_x = reference_df['node_x_odom'].values
    ref_y = reference_df['node_y_odom'].values
    ref_idx = reference_df['node_idx'].values
    
    actual_x = actual_df['pose_x'].values
    actual_y = actual_df['pose_y'].values
    predicted_nodes = actual_df['closest_node'].values


    length_check = min(len(actual_x), len(predicted_nodes))
    actual_x = actual_x[:length_check]
    actual_y = actual_y[:length_check]
    predicted_nodes = predicted_nodes[:length_check]
    
    # 1. Plot reference trajectory (ground truth)
    ax.plot(ref_x, ref_y, 'b-', linewidth=0.5, alpha=0.6, label='Reference Trajectory', zorder=1)
    ax.scatter(ref_x, ref_y, c='blue', s=100, marker='o', 
               edgecolors='darkblue', linewidths=2, 
               label='Reference Nodes', zorder=3, alpha=0.7)
    
    # Annotate some reference nodes (every Nth to avoid clutter)
    step = max(1, len(ref_idx) // 10)  # Show ~10 labels
    for i in range(0, len(ref_idx), step):
        ax.annotate(f'{ref_idx[i]}', 
                   (ref_x[i], ref_y[i]), 
                   xytext=(5, 5), 
                   textcoords='offset points',
                   fontsize=8, 
                   color='darkgreen',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
    
    # 2. Plot actual trajectory
    ax.plot(actual_x, actual_y, 'r-', linewidth=2, alpha=0.6, 
            label='Actual Trajectory', zorder=2)
    # ax.scatter(actual_x, actual_y, c='red', s=10, marker='x', 
    #            linewidths=0.5, label='Actual Poses', zorder=4, alpha=0.7)
    
    step = max(1, len(predicted_nodes) // 10)  # Show ~10 labels
    # Annotate sampled predicted nodes and ensure the last predicted node is annotated
    indices = list(range(0, len(predicted_nodes), step))
    last_idx = len(predicted_nodes) - 1
    if last_idx >= 0 and last_idx not in indices:
        indices.append(last_idx)

    for i in indices:
        ax.annotate(f'{predicted_nodes[i]}', 
                   (actual_x[i], actual_y[i]), 
                   xytext=(5, 5), 
                   textcoords='offset points',
                   fontsize=8, 
                   color='darkblue',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))

    ax.scatter(ref_x[0], ref_y[0], c='green', s=200, marker='*', 
               edgecolors='darkgreen', linewidths=2, 
               label='Start (Reference)', zorder=5)
    ax.scatter(actual_x[0], actual_y[0], c='lime', s=200, marker='*', 
               edgecolors='darkgreen', linewidths=2, 
               label='Start (Actual)', zorder=5)
    
    ax.scatter(ref_x[-1], ref_y[-1], c='purple', s=200, marker='s', 
               edgecolors='darkviolet', linewidths=1, 
               label='End (Reference)', zorder=5)
    ax.scatter(actual_x[-1], actual_y[-1], c='magenta', s=200, marker='s', 
               edgecolors='darkviolet', linewidths=1, 
               label='End (Actual)', zorder=5)
    
    # Styling
    ax.set_xlabel('X Position (m)', fontsize=12)
    ax.set_ylabel('Y Position (m)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()

    plt.show() if show else None

    return fig, ax

def plot_single_node_comparaison(df, reference_df, robot="limo", environment="clearpath_playpen", augmentation="no_augmentation", title="Reference vs Actual Trajectory"):
    actual_df = df[(df["robot"] == robot) & (df["environment"] == environment) & (df["augmentation"] == augmentation)]
    fig1, ax1 = plot_trajectory_node_comparison(reference_df, actual_df, 
                                           "Reference vs Actual Trajectory")    
    plt.show()

def plot_trajectory_with_errors(reference_df, actual_df, node_errors=None, title="Trajectory with Node Errors", show=True):
    """
    Plot trajectory with color-coded error visualization.
    
    Parameters:
    -----------
    reference_df : DataFrame
        Columns: ['node_idx', 'node_x_odom', 'node_y_odom']
    actual_df : DataFrame
        Columns: ['pose_x', 'pose_y', 'closest_node']
    node_errors : array-like, optional
        Node prediction errors (closest_node - true_node)
    title : str
        Plot title
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Extract data
    ref_x = reference_df['node_x_odom'].values
    ref_y = reference_df['node_y_odom'].values
    ref_idx = reference_df['node_idx'].values
    
    actual_x = actual_df['pose_x'].values
    actual_y = actual_df['pose_y'].values
    predicted_nodes = actual_df['closest_node'].values

    length_check = min(len(actual_x), len(predicted_nodes))
    actual_x = actual_x[:length_check]
    actual_y = actual_y[:length_check]
    predicted_nodes = predicted_nodes[:length_check]
    
    # Plot reference trajectory
    ax.plot(ref_x, ref_y, 'b-', linewidth=0.5, alpha=0.6, label='Reference Trajectory', zorder=1)
    ax.scatter(ref_x, ref_y, c='blue', s=100, marker='o', 
               edgecolors='darkblue', linewidths=2, 
               label='Reference Nodes', zorder=3, alpha=0.7)
    
    # Annotate some reference nodes (every Nth to avoid clutter)
    step = max(1, len(ref_idx) // 10)  # Show ~10 labels
    for i in range(0, len(ref_idx), step):
        ax.annotate(f'{ref_idx[i]}', 
                   (ref_x[i], ref_y[i]), 
                   xytext=(5, 5), 
                   textcoords='offset points',
                   fontsize=8, 
                   color='darkgreen',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))

    
    # Plot actual trajectory with error coloring if provided
    if node_errors is not None:
        abs_errors = np.abs(node_errors)
        scatter = ax.scatter(actual_x, actual_y, c=abs_errors, s=100, 
                           cmap='RdYlGn_r', marker='.', 
                           edgecolors='black', linewidths=0.1,
                           label='Actual Poses (colored by error)', 
                           zorder=2, alpha=0.8)
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Absolute Node Error', fontsize=11)
        
        # Draw trajectory line
        ax.plot(actual_x, actual_y, 'k-', linewidth=1.5, alpha=0.3, zorder=1)
    else:
        ax.scatter(actual_x, actual_y, c='red', s=100, marker='o', 
                  edgecolors='darkred', linewidths=1.5,
                  label='Actual Poses', zorder=3, alpha=0.7)
        ax.plot(actual_x, actual_y, 'r-', linewidth=1.5, alpha=0.5, zorder=1)

    step = max(1, len(predicted_nodes) // 10)  # Show ~10 labels
    # Annotate sampled predicted nodes and ensure the last predicted node is annotated
    indices = list(range(0, len(predicted_nodes), step))
    last_idx = len(predicted_nodes) - 1
    if last_idx >= 0 and last_idx not in indices:
        indices.append(last_idx)

    for i in indices:
        ax.annotate(f'{predicted_nodes[i]}', 
                   (actual_x[i], actual_y[i]), 
                   xytext=(5, 5), 
                   textcoords='offset points',
                   fontsize=8, 
                   color='darkblue',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))



    # Highlight start and end
    ax.scatter(ref_x[0], ref_y[0], c='green', s=200, marker='*', 
               edgecolors='darkgreen', linewidths=2, 
               label='Start (Reference)', zorder=5)
    ax.scatter(actual_x[0], actual_y[0], c='lime', s=200, marker='*', 
               edgecolors='darkgreen', linewidths=2, 
               label='Start (Actual)', zorder=5)
    
    ax.scatter(ref_x[-1], ref_y[-1], c='purple', s=200, marker='s', 
               edgecolors='darkviolet', linewidths=1, 
               label='End (Reference)', zorder=5)
    ax.scatter(actual_x[-1], actual_y[-1], c='magenta', s=200, marker='s', 
               edgecolors='darkviolet', linewidths=1, 
               label='End (Actual)', zorder=5)
    
    # Styling
    ax.set_xlabel('X Position (m)', fontsize=12)
    ax.set_ylabel('Y Position (m)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    plt.show() if show else None
    return fig, ax





if __name__ == "__main__":

    reference_header = 'reference'
    csv_name = "all_data_20251118-231029.csv"

    config = load_config()
    root_path = config["paths"]["dataframes_dir"]
    df = pd.read_csv(f"{root_path}{csv_name}") 

    #TODO need to be automated

    bunker_mist_office_17nov_nodes_reference_df = pd.read_csv(f"{root_path}closest_node_analysis/bunker_mist_office_17nov_nodes_reference.csv") 

    reference_nodes = {
    ("bunker", "mist_office_17nov"): bunker_mist_office_17nov_nodes_reference_df,
        # add more if needed
    }



    all_data_with_errors = compute_node_errors(df, reference_nodes)
    print(all_data_with_errors.head(50))



    # #SINGLE PLOT EXAMPLES
    # actual_df = df[(df["robot"] == "bunker") & (df["environment"] == "mist_corridor") & (df["augmentation"] == "no_augmentation")]
    # reference_df = limo_clearpath_playpen_nodes_reference_df
    # plot_single_node_comparaison(df=actual_df, reference_df=reference_df)
    
    # # #Plot 2: With error visualization
    # node_errors = compute_node_errors(df, reference_nodes)
    # node_errors = node_errors[(node_errors["robot"] == "bunker") & (node_errors["environment"] == "mist_corridor") & (node_errors["augmentation"] == "no_augmentation")]["node_error"].values
    # fig2, ax2 = plot_trajectory_with_errors(reference_df, actual_df, node_errors,
    #                                        "Trajectory with Node Prediction Errors")
    
    




