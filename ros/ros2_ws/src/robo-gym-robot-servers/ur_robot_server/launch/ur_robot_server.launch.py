from launch import LaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, PythonExpression
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)


def launch_setup(context, *args, **kwargs):
    from launch.utilities import perform_substitutions

    rviz_config = PathJoinSubstitution([
        LaunchConfiguration('rviz_config_path'),
        LaunchConfiguration('rviz_config_file')
    ])

    gui_and_gazebo_gui = PythonExpression([
        "'true' if '", LaunchConfiguration('gui'), "' == 'true' and '",
        LaunchConfiguration('gazebo_gui'), "' == 'true' else 'false'"
    ])
    gui_and_rviz_gui = PythonExpression([
        "'true' if '", LaunchConfiguration('gui'), "' == 'true' and '",
        LaunchConfiguration('rviz_gui'), "' == 'true' else 'false'"
    ])
    world_name_split= PythonExpression([
        "'", LaunchConfiguration('world_name'), "'.replace('.world', '')"
    ])
    robot_sim = IncludeLaunchDescription(
        condition=UnlessCondition(LaunchConfiguration('real_robot')),
        launch_description_source=PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('ur_robot_server'),
                    'launch',
                    'inc',
                    'ur_sim_control.launch.py'
                ])
            ),
            launch_arguments={
                'robot_description_file': LaunchConfiguration('robot_description_file'),
                'robot_description_package': LaunchConfiguration('robot_description_package'),
                'gui': LaunchConfiguration('gui'),
                'gazebo_gui': gui_and_gazebo_gui,
                'launch_rviz': gui_and_rviz_gui,
                'ur_tyoe': LaunchConfiguration('ur_model'),
                'world_file': LaunchConfiguration('world_name'),
                'x': LaunchConfiguration('x'),
                'y': LaunchConfiguration('y'),
                'z': LaunchConfiguration('z'),
                'roll': LaunchConfiguration('roll'),
                'pitch': LaunchConfiguration('pitch'),
                'yaw': LaunchConfiguration('yaw'),
                'camera1_gazebo': LaunchConfiguration('camera1_gazebo'),
                'camera1_link_x': LaunchConfiguration('camera1_link_x'),
                'camera1_link_y': LaunchConfiguration('camera1_link_y'),
                'camera1_link_z': LaunchConfiguration('camera1_link_z'),
                'camera1_link_roll': LaunchConfiguration('camera1_link_roll'),
                'camera1_link_pitch': LaunchConfiguration('camera1_link_pitch'),
                'camera1_link_yaw': LaunchConfiguration('camera1_link_yaw'),
            }.items()
        )
    nodes = [
        Node(
            package='ur_robot_server',
            executable='joint_trajectory_command_handler.py',
            name='joint_trajectory_command_handler',
            parameters=[{
                'real_robot': LaunchConfiguration('real_robot'),
                'action_cycle_rate': LaunchConfiguration('action_cycle_rate')
            }],
            output='screen'
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="log",
            arguments=["-d", rviz_config],
            condition=IfCondition(gui_and_rviz_gui),
        ),
        Node(
            package='ur_robot_server',
            executable='robot_server.py',
            name='robot_server',
            parameters=[{
                'server_port': LaunchConfiguration('server_port'),
                'real_robot': LaunchConfiguration('real_robot'),
                'ur_model': LaunchConfiguration('ur_model'),
                'max_velocity_scale_factor': LaunchConfiguration('max_velocity_scale_factor'),
                'action_cycle_rate': LaunchConfiguration('action_cycle_rate'),
                'reference_frame': LaunchConfiguration('reference_frame'),
                'ee_frame': LaunchConfiguration('ee_frame'),
                'target_mode': LaunchConfiguration('target_mode'),
                'rs_mode': LaunchConfiguration('rs_mode'),
                'action_mode': LaunchConfiguration('action_mode'),
                'use_voxel_occupancy': LaunchConfiguration('use_voxel_occupancy'),
                'n_objects': LaunchConfiguration('n_objects'),
                'object_0_frame': LaunchConfiguration('object_0_frame'),
                'object_1_frame': LaunchConfiguration('object_1_frame'),
                'object_0_model_name': LaunchConfiguration('object_0_model_name'),
                'object_1_model_name': LaunchConfiguration('object_1_model_name'),
                'objects_controller': LaunchConfiguration('objects_controller'),
            }],
            output='screen'
        ),
        Node(
            condition=IfCondition(LaunchConfiguration('objects_controller')),
            package='simulation_objects',
            executable='objects_controller.py',
            name='objects_controller',
            parameters=[{
                'real_robot': LaunchConfiguration('real_robot'),
                'reference_frame': LaunchConfiguration('reference_frame'),
                'object_trajectory_file_name': LaunchConfiguration('object_trajectory_file_name'),
                'n_objects': LaunchConfiguration('n_objects'),
                'object_1_model_name': LaunchConfiguration('object_1_model_name'),
                'object_1_frame': LaunchConfiguration('object_1_frame'),
                'object_0_model_name': LaunchConfiguration('object_0_model_name'),
                'object_0_frame': LaunchConfiguration('object_0_frame'),
                'world_name': world_name_split,
            }],
            output='screen'
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='isaac_tool_publisher',
            arguments=['0', '0', '0', '3.1415', '-1.5707', '0', 'tool0', 'tool1'],
            output='screen'
        )
    ]

    return [robot_sim] + nodes 


def generate_launch_description():
    ur_model = LaunchConfiguration('ur_model')

    robot_description_filename = PythonExpression([
        "'load_", LaunchConfiguration('ur_model'), ".launch.py'"
    ])
    robot_controller_filename = PythonExpression([
        "'", LaunchConfiguration('ur_model'), "_controllers.yaml'"
    ])

    declared_arguments = [
        DeclareLaunchArgument('ur_model', default_value='ur5e'),
        DeclareLaunchArgument('real_robot', default_value='false'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz_gui', default_value='false'),
        DeclareLaunchArgument('gazebo_gui', default_value='true'),
        DeclareLaunchArgument('world_name', default_value='empty.world'),
        DeclareLaunchArgument('max_velocity_scale_factor', default_value='1.0'),
        DeclareLaunchArgument('server_port', default_value='50051'),
        DeclareLaunchArgument('action_cycle_rate', default_value='25.0'),
        DeclareLaunchArgument('reference_frame', default_value='base_link'),
        DeclareLaunchArgument('ee_frame', default_value='tool0'),
        DeclareLaunchArgument('target_mode', default_value='only_robot'),
        DeclareLaunchArgument('rs_mode', default_value='false'),
        DeclareLaunchArgument('action_mode', default_value='abs_pos'),
        DeclareLaunchArgument("activate_joint_controller", default_value="true", description="Enable headless mode for robot control"),
        DeclareLaunchArgument("initial_joint_controller", default_value="joint_trajectory_controller", description="Robot controller to start."),
        DeclareLaunchArgument('use_voxel_occupancy', default_value='false'),
        DeclareLaunchArgument('objects_controller', default_value='false'),
        DeclareLaunchArgument('n_objects', default_value='0'),
        DeclareLaunchArgument('object_trajectory_file_name', default_value='no_file'),
        DeclareLaunchArgument('object_0_model_name', default_value=''),
        DeclareLaunchArgument('object_0_frame', default_value='target'),
        DeclareLaunchArgument('object_1_model_name', default_value=''),
        DeclareLaunchArgument('object_1_frame', default_value=''),
        DeclareLaunchArgument('rviz_config_path', default_value=PathJoinSubstitution([
            FindPackageShare('ur_robot_server'), 'rviz'])),
        DeclareLaunchArgument('rviz_config_file', default_value='ur_rl.rviz'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.1'),
        DeclareLaunchArgument('roll', default_value='0.0'),
        DeclareLaunchArgument('pitch', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('camera1_gazebo', default_value='False'),
        DeclareLaunchArgument('camera1_link_x', default_value='0.0'),
        DeclareLaunchArgument('camera1_link_y', default_value='0.0'),
        DeclareLaunchArgument('camera1_link_z', default_value='0.0'),
        DeclareLaunchArgument('camera1_link_roll', default_value='0.0'),
        DeclareLaunchArgument('camera1_link_pitch', default_value='0.0'),
        DeclareLaunchArgument('camera1_link_yaw', default_value='0.0'),
        DeclareLaunchArgument('robot_description_file', default_value="ur.urdf.xacro"),
        DeclareLaunchArgument('robot_description_package', default_value="ur_robot_server"),
        DeclareLaunchArgument('joint_limit_params', default_value=PathJoinSubstitution([
            FindPackageShare('ur_description'),
            'config',
            ur_model,
            'joint_limits.yaml'
        ])),
        DeclareLaunchArgument('kinematics_params', default_value=PathJoinSubstitution([
            FindPackageShare('ur_description'),
            'config',
            ur_model,
            'default_kinematics.yaml'
        ])),
        DeclareLaunchArgument('physical_params', default_value=PathJoinSubstitution([
            FindPackageShare('ur_description'),
            'config',
            ur_model,
            'physical_parameters.yaml'
        ])),
        DeclareLaunchArgument('visual_params', default_value=PathJoinSubstitution([
            FindPackageShare('ur_description'),
            'config',
            ur_model,
            'visual_parameters.yaml'
        ])),
        DeclareLaunchArgument('initial_positions_file', default_value=PathJoinSubstitution([
            FindPackageShare('ur_description'),
            'config',
            'initial_positions.yaml'
        ])),
        DeclareLaunchArgument('controller_config_file', default_value=PathJoinSubstitution([
            FindPackageShare('ur_robot_server'),
            'config',
            robot_controller_filename
        ])),
        DeclareLaunchArgument('controllers', default_value='joint_state_controller eff_joint_traj_controller'),
        DeclareLaunchArgument('stopped_controllers', default_value='joint_group_eff_controller'),
    ]
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
