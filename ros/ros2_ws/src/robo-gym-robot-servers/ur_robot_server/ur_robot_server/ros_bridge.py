import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.qos import QoSProfile
from threading import Event
import time

from std_msgs.msg import Int32MultiArray, Bool, Header
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from visualization_msgs.msg import Marker
from gazebo_msgs.msg import ContactsState
from tf2_ros import Buffer, TransformListener, StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped
from robo_gym_server_modules.robot_server.grpc_msgs.python import robot_server_pb2

import PyKDL
import numpy as np
import copy


class UrRosBridge:
    def __init__(self, node):
        self.node = node
        self.node.get_logger().info('Initializing URRosBridge...')
        self.reset = Event()
        self.reset.clear()
        self.get_state_event = Event()
        self.get_state_event.set()

        self.node.declare_parameter('action_cycle_rate', 125.0)
        self.node.declare_parameter('max_velocity_scale_factor', 1.0)
        self.node.declare_parameter('reference_frame', 'base_link')
        self.node.declare_parameter('ee_frame', 'tool0')
        self.node.declare_parameter('rs_mode', '')
        self.node.declare_parameter('target_mode', '1object')
        self.node.declare_parameter('action_mode', 'abs_pos')
        self.node.declare_parameter('objects_controller', False)
        self.node.declare_parameter('n_objects', 0)
        self.node.declare_parameter('use_voxel_occupancy', False)

        self.real_robot = self.node.get_parameter('real_robot').value
        self.ur_model = self.node.get_parameter('ur_model').value
        self.target = [0.0] * 3

        self.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        self.joint_position = dict.fromkeys(self.joint_names, 0.0)
        self.joint_velocity = dict.fromkeys(self.joint_names, 0.0)

        self.node.create_subscription(JointState, 'joint_states', self._on_joint_states, 10)
        self.target_pub = self.node.create_publisher(Marker, 'target_marker', 10)
        self.arm_cmd_pub = self.node.create_publisher(JointTrajectory, 'env_arm_command', 10)

        self.rate = self.node.get_parameter('action_cycle_rate').value
        self.control_rate = self.node.create_timer(1.0 / self.rate, lambda: None)

        self.max_velocity_scale_factor = float(self.node.get_parameter('max_velocity_scale_factor').value)
        self.min_traj_duration = 0.5
        self.joint_velocity_limits = self._get_joint_velocity_limits()

        self.reference_frame = self.node.get_parameter('reference_frame').value
        self.ee_frame = self.node.get_parameter('ee_frame').value

        self.tf2_buffer = Buffer()
        self.tf2_listener = TransformListener(self.tf2_buffer, self.node)
        self.static_tf2_broadcaster = StaticTransformBroadcaster(self.node)

        self.path_frame = 'base_link'

        self.collision_sensors = dict.fromkeys([
            "shoulder", "upper_arm", "forearm",
            "wrist_1", "wrist_2", "wrist_3"
        ], False)

        if not self.real_robot:
            self.node.create_subscription(ContactsState, 'shoulder_collision', self._on_shoulder_collision, 10)
            self.node.create_subscription(ContactsState, 'upper_arm_collision', self._on_upper_arm_collision, 10)
            self.node.create_subscription(ContactsState, 'forearm_collision', self._on_forearm_collision, 10)
            self.node.create_subscription(ContactsState, 'wrist_1_collision', self._on_wrist_1_collision, 10)
            self.node.create_subscription(ContactsState, 'wrist_2_collision', self._on_wrist_2_collision, 10)
            self.node.create_subscription(ContactsState, 'wrist_3_collision', self._on_wrist_3_collision, 10)

        self.rs_mode = self.node.get_parameter('rs_mode').value or self.node.get_parameter('target_mode').value
        self.action_mode = self.node.get_parameter('action_mode').value
        self.objects_controller = self.node.get_parameter('objects_controller').value
        self.n_objects = self.node.get_parameter('n_objects').value

        if self.objects_controller:
            self.move_objects_pub = self.node.create_publisher(Bool, 'move_objects', 10)
            self.objects_model_name = []
            for i in range(self.n_objects):
                self.node.declare_parameter(f"object_{i}_model_name", '')
                self.objects_model_name.append(self.node.get_parameter(f"object_{i}_model_name").value)

        self.objects_frame = []
        for i in range(self.n_objects):
            self.node.declare_parameter(f"object_{i}_frame", 'target')
            self.objects_frame.append(self.node.get_parameter(f"object_{i}_frame").value)

        self.use_voxel_occupancy = self.node.get_parameter('use_voxel_occupancy').value
        if self.use_voxel_occupancy:
            self.node.create_subscription(Int32MultiArray, 'occupancy_state', self._on_occupancy_state, 10)
            if self.rs_mode == '1moving1point_2_2_4_voxel':
                self.voxel_occupancy = [0.0] * 16

    def get_state(self):
        self.get_state_event.clear()
        # Get environment state
        state =[]
        state_dict = {}

        if self.rs_mode == 'only_robot':
            # Joint Positions and Joint Velocities
            joint_position = copy.deepcopy(self.joint_position)
            joint_velocity = copy.deepcopy(self.joint_velocity)
            state += self._get_joint_ordered_value_list(joint_position)
            state += self._get_joint_ordered_value_list(joint_velocity)
            state_dict.update(self._get_joint_states_dict(joint_position, joint_velocity))

            # ee to ref transform
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rclpy.time.Time(), timeout=Duration(seconds=2.0))
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))
        
            # Collision sensors
            ur_collision = any(self.collision_sensors.values())
            state += [ur_collision]
            state_dict['in_collision'] = float(ur_collision)

        elif self.rs_mode == '1object':
            # Object 0 Pose
            object_0_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.objects_frame[0], rclpy.time.Time())
            object_0_trans_list = self._transform_to_list(object_0_trans)
            state += object_0_trans_list
            state_dict.update(self._get_transform_dict(object_0_trans, 'object_0_to_ref'))
            # Joint Positions and Joint Velocities
            joint_position = copy.deepcopy(self.joint_position)
            joint_velocity = copy.deepcopy(self.joint_velocity)
            state += self._get_joint_ordered_value_list(joint_position)
            state += self._get_joint_ordered_value_list(joint_velocity)
            state_dict.update(self._get_joint_states_dict(joint_position, joint_velocity))

            # ee to ref transform
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rclpy.time.Time())
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))

            # Collision sensors
            ur_collision = any(self.collision_sensors.values())
            state += [ur_collision]
            state_dict['in_collision'] = float(ur_collision)

        elif self.rs_mode == '1moving2points':
            # Object 0 Pose 
            object_0_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.objects_frame[0], rclpy.time.Time())
            object_0_trans_list = self._transform_to_list(object_0_trans)
            state += object_0_trans_list
            state_dict.update(self._get_transform_dict(object_0_trans, 'object_0_to_ref'))
            
            # Joint Positions and Joint Velocities
            joint_position = copy.deepcopy(self.joint_position)
            joint_velocity = copy.deepcopy(self.joint_velocity)
            state += self._get_joint_ordered_value_list(joint_position)
            state += self._get_joint_ordered_value_list(joint_velocity)
            state_dict.update(self._get_joint_states_dict(joint_position, joint_velocity))

            # ee to ref transform
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rclpy.time.Time())
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))
        
            # Collision sensors
            ur_collision = any(self.collision_sensors.values())
            state += [ur_collision]
            state_dict['in_collision'] = float(ur_collision)

            # forearm to ref transform
            forearm_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, 'forearm_link', rclpy.time.Time())
            forearm_to_ref_trans_list = self._transform_to_list(forearm_to_ref_trans)
            state += forearm_to_ref_trans_list
            state_dict.update(self._get_transform_dict(forearm_to_ref_trans, 'forearm_to_ref'))

        elif self.rs_mode == '2objects2points':
            # Object 0 Pose 
            object_0_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.objects_frame[0], rclpy.time.Time())
            object_0_trans_list = self._transform_to_list(object_0_trans)
            state += object_0_trans_list
            state_dict.update(self._get_transform_dict(object_0_trans, 'object_0_to_ref'))

            # Object 1 Pose 
            object_1_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.objects_frame[1], rclpy.time.Time())
            object_1_trans_list = self._transform_to_list(object_1_trans)
            state += object_1_trans_list
            state_dict.update(self._get_transform_dict(object_1_trans, 'object_1_to_ref'))
            
            # Joint Positions and Joint Velocities
            joint_position = copy.deepcopy(self.joint_position)
            joint_velocity = copy.deepcopy(self.joint_velocity)
            state += self._get_joint_ordered_value_list(joint_position)
            state += self._get_joint_ordered_value_list(joint_velocity)
            state_dict.update(self._get_joint_states_dict(joint_position, joint_velocity))

            # ee to ref transform
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rclpy.time.Time())
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))
        
            # Collision sensors
            ur_collision = any(self.collision_sensors.values())
            state += [ur_collision]
            state_dict['in_collision'] = float(ur_collision)

            # forearm to ref transform
            forearm_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, 'forearm_link', rclpy.time.Time())
            forearm_to_ref_trans_list = self._transform_to_list(forearm_to_ref_trans)
            state += forearm_to_ref_trans_list
            state_dict.update(self._get_transform_dict(forearm_to_ref_trans, 'forearm_to_ref'))

        else: 
            raise ValueError('rs_mode not recognized')
                    
        self.get_state_event.set()

        msg = robot_server_pb2.State(state=state, state_dict=state_dict, success= True)
       
        return msg

    def set_state(self, state_msg):
        if 'object_0_x' in state_msg.float_params and 'object_0_y' in state_msg.float_params and 'object_0_z' in state_msg.float_params:
            self.target = [state_msg.float_params['object_0_x'], state_msg.float_params['object_0_y'], state_msg.float_params['object_0_z']]

        self.publish_target_marker(self.target)

        if all (j in state_msg.state_dict for j in ('base_joint_position','shoulder_joint_position', 'elbow_joint_position', \
                                                     'wrist_1_joint_position', 'wrist_2_joint_position', 'wrist_3_joint_position')):
            state_dict = True
        else:
            state_dict = False 

        self.reset.clear()

        if self.objects_controller:
            msg = Bool()
            msg.data = False
            self.move_objects_pub.publish(msg)

            if state_msg.string_params:
                for param_name, param_value in state_msg.string_params.items():
                    if not self.node.has_parameter(param_name):
                        self.node.declare_parameter(param_name, param_value)
                    else:
                        self.node.set_parameters([
                            rclpy.parameter.Parameter(param_name, rclpy.parameter.Parameter.Type.STRING, param_value)
                        ])
            if state_msg.float_params:
                for param_name, param_value in state_msg.float_params.items():
                    if not self.node.has_parameter(param_name):
                        self.node.declare_parameter(param_name, param_value)
                    else:
                        self.node.set_parameters([
                            rclpy.parameter.Parameter(param_name, rclpy.parameter.Parameter.Type.DOUBLE, param_value)
                        ])

        # UR Joints Positions
        if state_dict:
            goal_joint_position = [state_msg.state_dict['base_joint_position'], state_msg.state_dict['shoulder_joint_position'], \
                                            state_msg.state_dict['elbow_joint_position'], state_msg.state_dict['wrist_1_joint_position'], \
                                            state_msg.state_dict['wrist_2_joint_position'], state_msg.state_dict['wrist_3_joint_position']]
        else:
            goal_joint_position = state_msg.state[6:12]
        self.set_joint_position(goal_joint_position)
        
        if not self.real_robot:
            # Reset collision sensors flags
            self.collision_sensors.update(dict.fromkeys(["shoulder", "upper_arm", "forearm", "wrist_1", "wrist_2", "wrist_3"], False))
        # Start movement of objects
        if self.objects_controller:
            msg = Bool()
            msg.data = True
            self.move_objects_pub.publish(msg)

        self.reset.set()

        for _ in range(20):
            time.sleep(1/self.rate)

        return 1

    def publish_target_marker(self, target_pose):
        # Publish Target RViz Marker
        t_marker = Marker()
        t_marker.type = 2  # =>SPHERE
        t_marker.scale.x = 0.15
        t_marker.scale.y = 0.15
        t_marker.scale.z = 0.15
        t_marker.action = 0
        t_marker.frame_locked = True
        t_marker.pose.position.x = target_pose[0]
        t_marker.pose.position.y = target_pose[1]
        t_marker.pose.position.z = target_pose[2]
        rpy_orientation = PyKDL.Rotation.RPY(0.0, 0.0, 0.0)
        q_orientation = rpy_orientation.GetQuaternion()
        t_marker.pose.orientation.x = q_orientation[0]
        t_marker.pose.orientation.y = q_orientation[1]
        t_marker.pose.orientation.z = q_orientation[2]
        t_marker.pose.orientation.w = q_orientation[3]
        t_marker.id = 0
        t_marker.header.stamp = rclpy.time.Time().to_msg()
        t_marker.header.frame_id = self.path_frame
        t_marker.color.a = 1.0
        t_marker.color.r = 0.0
        t_marker.color.g = 1.0
        t_marker.color.b = 0.0
        self.target_pub.publish(t_marker)

    def send_action(self, action):
        if self.action_mode == 'abs_pos':
            executed_action = self.publish_env_arm_cmd(action)
        
        elif self.action_mode == 'delta_pos':
            executed_action = self.publish_env_arm_delta_cmd(action)

        return executed_action

    def set_joint_position(self, goal_joint_position):
        """Set robot joint positions to a desired value
        """        

        position_reached = False

        while not position_reached:
            self.publish_env_arm_cmd(goal_joint_position)
            self.get_state_event.clear()
            joint_position = copy.deepcopy(self.joint_position)
            position_reached = np.isclose(goal_joint_position, self._get_joint_ordered_value_list(joint_position), atol=0.05).all()
            self.get_state_event.set()

    def publish_env_arm_cmd(self, position_cmd):
        """Publish environment JointTrajectory msg.
        """
        msg = JointTrajectory()
        msg.header = Header()
        msg.joint_names = self.joint_names
        msg.points = [JointTrajectoryPoint()]
        msg.points[0].positions = position_cmd
        dur = []
        for idx, name in enumerate(msg.joint_names):
            pos = self.joint_position[name]
            cmd = position_cmd[idx]
            max_vel = self.joint_velocity_limits[name]
            dur.append(max(abs(cmd-pos)/max_vel, self.min_traj_duration))
        msg.points[0].time_from_start = Duration(seconds=max(dur)).to_msg()
        self.arm_cmd_pub.publish(msg)
        time.sleep(1/self.rate)
        return position_cmd

    def publish_env_arm_delta_cmd(self, delta_cmd):
        """Publish environment JointTrajectory msg.
        """

        msg = JointTrajectory()
        msg.header = Header()
        msg.joint_names = self.joint_names
        msg.points=[JointTrajectoryPoint()]
        # msg.points[0].positions = position_cmd
        position_cmd = []
        dur = []
        for idx, name in enumerate(msg.joint_names):
            pos = self.joint_position[name]
            cmd = delta_cmd[idx]
            max_vel = self.joint_velocity_limits[name]
            dur.append(max(abs(cmd)/max_vel, self.min_traj_duration))
            position_cmd.append(pos + cmd)
        msg.points[0].positions = position_cmd
        msg.points[0].time_from_start = Duration.from_sec(max(dur)).to_msg()
        self.arm_cmd_pub.publish(msg)
        time.sleep(1/self.rate)
        return position_cmd


    def _on_joint_states(self, msg):
        if self.get_state_event.is_set():
            for idx, name in enumerate(msg.name):
                if name in self.joint_names:
                    self.joint_position[name] = msg.position[idx]
                    self.joint_velocity[name] = msg.velocity[idx]

    def _on_shoulder_collision(self, data):
        if data.states:
            self.collision_sensors["shoulder"] = True

    def _on_upper_arm_collision(self, data):
        if data.states:
            self.collision_sensors["upper_arm"] = True

    def _on_forearm_collision(self, data):
        if data.states:
            self.collision_sensors["forearm"] = True

    def _on_wrist_1_collision(self, data):
        if data.states:
            self.collision_sensors["wrist_1"] = True

    def _on_wrist_2_collision(self, data):
        if data.states:
            self.collision_sensors["wrist_2"] = True

    def _on_wrist_3_collision(self, data):
        if data.states:
            self.collision_sensors["wrist_3"] = True

    def _on_occupancy_state(self, msg):
        if self.get_state_event.is_set():
            self.voxel_occupancy = msg.data

    def _get_joint_states_dict(self, joint_position, joint_velocity):

        d = {}
        d['base_joint_position'] = joint_position['shoulder_pan_joint']
        d['shoulder_joint_position'] = joint_position['shoulder_lift_joint']
        d['elbow_joint_position'] = joint_position['elbow_joint']
        d['wrist_1_joint_position'] = joint_position['wrist_1_joint']
        d['wrist_2_joint_position'] = joint_position['wrist_2_joint']
        d['wrist_3_joint_position'] = joint_position['wrist_3_joint']
        d['base_joint_velocity'] = joint_velocity['shoulder_pan_joint']
        d['shoulder_joint_velocity'] = joint_velocity['shoulder_lift_joint']
        d['elbow_joint_velocity'] = joint_velocity['elbow_joint']
        d['wrist_1_joint_velocity'] = joint_velocity['wrist_1_joint']
        d['wrist_2_joint_velocity'] = joint_velocity['wrist_2_joint']
        d['wrist_3_joint_velocity'] = joint_velocity['wrist_3_joint']

        return d 

    def _get_transform_dict(self, transform, transform_name):

        d = dict()
        d[transform_name + '_translation_x'] = transform.transform.translation.x
        d[transform_name + '_translation_y'] = transform.transform.translation.y
        d[transform_name + '_translation_z'] = transform.transform.translation.z
        d[transform_name + '_rotation_x'] = transform.transform.rotation.x
        d[transform_name + '_rotation_y'] = transform.transform.rotation.y
        d[transform_name + '_rotation_z'] = transform.transform.rotation.z
        d[transform_name + '_rotation_w'] = transform.transform.rotation.w

        return d

    def _transform_to_list(self, transform):

        return [transform.transform.translation.x, transform.transform.translation.y, \
                transform.transform.translation.z, transform.transform.rotation.x, \
                transform.transform.rotation.y, transform.transform.rotation.z, \
                transform.transform.rotation.w]

    def _get_joint_ordered_value_list(self, joint_values):
        return [joint_values[name] for name in self.joint_names]

    def _get_joint_velocity_limits(self):
        if self.ur_model in ['ur3', 'ur3e']:
            absolute_joint_velocity_limits = {
                'elbow_joint': 3.14, 'shoulder_lift_joint': 3.14, 'shoulder_pan_joint': 3.14,
                'wrist_1_joint': 6.28, 'wrist_2_joint': 6.28, 'wrist_3_joint': 6.28
            }
        elif self.ur_model in ['ur5', 'ur5e']:
            absolute_joint_velocity_limits = dict.fromkeys(self.joint_names, 3.14)
        elif self.ur_model in ['ur10', 'ur10e', 'ur16e']:
            absolute_joint_velocity_limits = {
                'elbow_joint': 3.14, 'shoulder_lift_joint': 2.09, 'shoulder_pan_joint': 2.09,
                'wrist_1_joint': 3.14, 'wrist_2_joint': 3.14, 'wrist_3_joint': 3.14
            }
        else:
            raise ValueError('ur_model not recognized')

        return {
            name: self.max_velocity_scale_factor * absolute_joint_velocity_limits[name]
            for name in self.joint_names
        }
