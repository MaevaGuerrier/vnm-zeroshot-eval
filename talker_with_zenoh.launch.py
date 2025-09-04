from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Start the Zenoh daemon
        # ExecuteProcess(
        #     cmd=[
        #         'ros2', 'run', 'rmw_zenoh_cpp', 'rmw_zenohd'
        #     ],
        #     name='zenoh_daemon',
        #     output='screen'
        # ),

        # Start the demo talker node
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='talker',
            output='screen',
            parameters=[],
        )
    ])