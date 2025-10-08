import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_config
import pandas as pd


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



if __name__ == "__main__":

    config = load_config()
    root_path = config["paths"]["dataframes_dir"]
    df = pd.read_csv(f"{root_path}all_data_20251008-160502.csv")

    for robot in df["robot"].unique():
        robot_df = df[df["robot"] == robot]
        for env in robot_df["environment"].unique():
            env_df = robot_df[robot_df["environment"] == env]
            plot_odometry(df=env_df, title=f"{robot} - {env}", save_path=f"../plots/odometry_{robot}_{env}.png")




