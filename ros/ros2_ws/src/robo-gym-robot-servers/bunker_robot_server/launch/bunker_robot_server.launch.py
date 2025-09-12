from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def launch_setup(context, *args, **kwargs):
    rviz_gui = LaunchConfiguration('rviz_gui')
    server_port = LaunchConfiguration('server_port')
    real_robot = LaunchConfiguration('real_robot')
    action_cycle_rate = LaunchConfiguration('action_cycle_rate')
    robot_model = LaunchConfiguration('robot_model')

    nodes = [
        Node(
            package='bunker_robot_server',
            executable='robot_server.py',
            name='robot_server',
            parameters=[{
                'server_port': server_port,
                'action_cycle_rate': action_cycle_rate,
                'robot_model': robot_model,
                'real_robot': real_robot,
            }],
            respawn=False,
            output='screen'
        ),
    ]

    return nodes


def generate_launch_description():

    declared_arguments = [
        DeclareLaunchArgument('rviz_gui', default_value='false'),
        DeclareLaunchArgument('server_port', default_value='50051'),
        DeclareLaunchArgument('real_robot', default_value='true'),
        DeclareLaunchArgument('action_cycle_rate', default_value='10.0'),
        DeclareLaunchArgument('robot_model', default_value='bunker'),
    ]

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])