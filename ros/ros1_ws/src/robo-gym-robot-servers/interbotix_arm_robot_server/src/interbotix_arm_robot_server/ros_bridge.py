#!/usr/bin/env python

import rospy
import tf2_ros
from gazebo_msgs.msg import ContactsState
from sensor_msgs.msg import JointState
from std_msgs.msg import Int32MultiArray
from trajectory_msgs.msg import JointTrajectoryPoint, JointTrajectory
from std_msgs.msg import Header, Bool
from visualization_msgs.msg import Marker
import copy
import PyKDL
from threading import Event
from robo_gym_server_modules.robot_server.grpc_msgs.python import robot_server_pb2
import numpy as np


class InterbotixArmRosBridge:

    def __init__(self, real_robot=False, robot_model='rx150'):

        # Event is clear while initialization or set_state is going on
        self.reset = Event()
        self.reset.clear()
        self.get_state_event = Event()
        self.get_state_event.set()

        self.real_robot = real_robot
        self.robot_model = robot_model

        self.target = [0.0] * 3
        # Joint States
        if robot_model == 'rx150' or robot_model == 'wx250' or robot_model == 'px150' or robot_model == 'rx200' or robot_model == 'vx250' or robot_model == 'vx300' or robot_model == 'wx200' or robot_model == 'wx250':
            self.dof = 5
        elif robot_model == 'px100':
            self.dof = 4
        elif robot_model == 'vx300s' or robot_model == 'wx250s':
            self.dof = 6
        else:
            self.dof = 5
        if self.dof == 4:
            self.joint_names = ['waist', 'shoulder', 'elbow', 'wrist_angle']
            self.joint_position_names = ['base_joint_position', 'shoulder_joint_position', 'elbow_joint_position',
                                         'wrist_angle_joint_position']
        elif self.dof == 5:
            self.joint_names = ['waist', 'shoulder', 'elbow', 'wrist_angle', 'wrist_rotate']
            self.joint_position_names = ['base_joint_position', 'shoulder_joint_position', 'elbow_joint_position',
                                         'wrist_angle_joint_position', 'wrist_rotate_joint_position']
        elif self.dof == 6:
            self.joint_names = ['waist', 'shoulder', 'elbow', 'forearm_roll', 'wrist_angle', 'wrist_rotate']
            self.joint_position_names = ['base_joint_position', 'shoulder_joint_position', 'elbow_joint_position',
                                         'forearm_roll_joint_position', 'wrist_angle_joint_position',
                                         'wrist_rotate_joint_position']

        self.joint_position = dict.fromkeys(self.joint_names, 0.0)
        self.joint_velocity = dict.fromkeys(self.joint_names, 0.0)
        rospy.Subscriber(robot_model + "/joint_states", JointState, self._on_joint_states)
        # Target RViz Marker publisher
        self.target_pub = rospy.Publisher('target_marker', Marker, latch=True, queue_size=10)

        # Robot control
        self.arm_cmd_pub = rospy.Publisher('env_arm_command', JointTrajectory, queue_size=1) # joint_trajectory_command_handler publisher
        control_rate_float = rospy.get_param("~action_cycle_rate", 125.0)
        self.control_rate = rospy.Rate(control_rate_float)
        self.max_velocity_scale_factor = float(rospy.get_param("~max_velocity_scale_factor"))
        self.min_traj_duration = 0.5 # minimum trajectory duration (s)
        self.joint_velocity_limits = self._get_joint_velocity_limits()

        # Robot frames
        self.reference_frame = rospy.get_param("~reference_frame", "base")
        default_ee_frame = self.robot_model + '/gripper_bar_link'
        self.ee_frame = rospy.get_param("~ee_frame", default_ee_frame)
        rospy.loginfo("ee frame: " + self.ee_frame)

        # TF2
        self.tf2_buffer = tf2_ros.Buffer()
        self.tf2_listener = tf2_ros.TransformListener(self.tf2_buffer)
        self.static_tf2_broadcaster = tf2_ros.StaticTransformBroadcaster()

        # Reference frame for Path
        self.path_frame = self.robot_model + '/base_link'

        # Collision detection
        if not self.real_robot:
            rospy.Subscriber(str(self.robot_model) + "/shoulder_collision", ContactsState,
                             self._on_shoulder_collision)
            rospy.Subscriber(str(self.robot_model) + "/upper_arm_collision", ContactsState,
                             self._on_upper_arm_collision)
            rospy.Subscriber(str(self.robot_model) + "/wrist_collision", ContactsState,
                             self._on_wrist_collision)
            rospy.Subscriber(str(self.robot_model) + "/gripper_collision", ContactsState,
                             self._on_gripper_collision)
            if self.dof == 6:
                rospy.Subscriber(str(self.robot_model) + "/upper_forearm_collision", ContactsState,
                                 self._on_upper_forearm_collision)
                rospy.Subscriber(str(self.robot_model) + "/lower_forearm_collision", ContactsState,
                                 self._on_lower_forearm_collision)
            elif self.dof == 5:
                rospy.Subscriber(str(self.robot_model) + "/forearm_collision", ContactsState,
                                 self._on_forearm_collision)

        self.collision_sensors = dict.fromkeys(["shoulder", "upper_arm", "wrist", "gripper"], False)
        if self.dof == 6:
            self.collision_sensors = dict.fromkeys(["shoulder", "upper_arm", "upper_forearm", "lower_forearm",
                                                    "wrist", "gripper"], False)
        elif self.dof == 5:
            self.collision_sensors = dict.fromkeys(["shoulder", "upper_arm", "forearm", "wrist", "gripper"], False)

        # Robot Server mode
        rs_mode = rospy.get_param('~rs_mode')

        if rs_mode:
            self.rs_mode = rs_mode
        else:
            self.rs_mode = rospy.get_param("~target_mode", '1object')

        # Action Mode
        self.action_mode = rospy.get_param('~action_mode')

        # Objects  Controller 
        self.objects_controller = rospy.get_param("objects_controller", False)
        self.n_objects = int(rospy.get_param("n_objects", 0))
        if self.objects_controller:
            self.move_objects_pub = rospy.Publisher('move_objects', Bool, queue_size=10)
            # Get objects model name
            self.objects_model_name = []
            for i in range(self.n_objects):
                self.objects_model_name.append(rospy.get_param("object_" + repr(i) + "_model_name"))
        # Get objects TF Frame
        self.objects_frame = []
        for i in range(self.n_objects):
            self.objects_frame.append(rospy.get_param("object_" + repr(i) + "_frame"))

        # Voxel Occupancy
        self.use_voxel_occupancy = rospy.get_param("~use_voxel_occupancy", False)
        if self.use_voxel_occupancy: 
            rospy.Subscriber("occupancy_state", Int32MultiArray, self._on_occupancy_state)
            if self.rs_mode == '1moving1point_2_2_4_voxel':
                self.voxel_occupancy = [0.0] * 16

    def get_state(self):
        self.get_state_event.clear()
        # Get environment state
        state = []
        state_dict = {}

        if self.rs_mode == 'only_robot':
            # Joint Positions and Joint Velocities
            joint_position = copy.deepcopy(self.joint_position)
            joint_velocity = copy.deepcopy(self.joint_velocity)
            state += self._get_joint_ordered_value_list(joint_position)
            state += self._get_joint_ordered_value_list(joint_velocity)
            state_dict.update(self._get_joint_states_dict(joint_position, joint_velocity))

            # ee to ref transform
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rospy.Time(0))
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))
        
            # Collision sensors
            interbotix_collision = any(self.collision_sensors.values())
            state += [interbotix_collision]
            state_dict['in_collision'] = float(interbotix_collision)

        elif self.rs_mode == '1object':
            # Object 0 Pose 
            object_0_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.objects_frame[0], rospy.Time(0))
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
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rospy.Time(0))
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))
        
            # Collision sensors
            interbotix_collision = any(self.collision_sensors.values())
            state += [interbotix_collision]
            state_dict['in_collision'] = float(interbotix_collision)

        elif self.rs_mode == '1moving2points':
            # Object 0 Pose
            object_0_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.objects_frame[0],
                                                              rospy.Time(0))
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
            ee_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, self.ee_frame, rospy.Time(0))
            ee_to_ref_trans_list = self._transform_to_list(ee_to_ref_trans)
            state += ee_to_ref_trans_list
            state_dict.update(self._get_transform_dict(ee_to_ref_trans, 'ee_to_ref'))

            # Collision sensors
            interbotix_collision = any(self.collision_sensors.values())
            state += [0]
            state_dict['in_collision'] = float(0)

            # forearm to ref transform
            forearm_to_ref_trans = self.tf2_buffer.lookup_transform(self.reference_frame, str(self.robot_model) + '/forearm_link', rospy.Time(0))
            forearm_to_ref_trans_list = self._transform_to_list(forearm_to_ref_trans)
            state += forearm_to_ref_trans_list
            state_dict.update(self._get_transform_dict(forearm_to_ref_trans, 'forearm_to_ref'))
        else: 
            raise ValueError
                    
        self.get_state_event.set()

        # Create and fill State message
        msg = robot_server_pb2.State(state=state, state_dict=state_dict, success=True)
       
        return msg

    def set_state(self, state_msg):
        # Set target internal value
        self.target = [state_msg.float_params['object_0_x'], state_msg.float_params['object_0_y'],
                       state_msg.float_params['object_0_z']]
        # Publish Target Marker
        self.publish_target_marker(self.target)

        if all(j in state_msg.state_dict for j in self.joint_position_names):
            state_dict = True
        else:
            state_dict = False 

        # Clear reset Event
        self.reset.clear()

        # Setup Objects movement
        if self.objects_controller:
            # Stop movement of objects
            msg = Bool()
            msg.data = False
            self.move_objects_pub.publish(msg)

            # Loop through all the string_params and float_params and set them as ROS parameters
            for param in state_msg.string_params:
                rospy.set_param(param, state_msg.string_params[param])

            for param in state_msg.float_params:
                rospy.set_param(param, state_msg.float_params[param])

        # Interbotix Joints Positions
        if state_dict:
            if self.dof == 6:
                goal_joint_position = [state_msg.state_dict['base_joint_position'], state_msg.state_dict['shoulder_joint_position'], \
                                            state_msg.state_dict['elbow_joint_position'], state_msg.state_dict['forearm_roll_joint_position'], \
                                            state_msg.state_dict['wrist_angle_joint_position'], state_msg.state_dict['wrist_rotate_joint_position']]
            elif self.dof == 5:
                goal_joint_position = [state_msg.state_dict['base_joint_position'], state_msg.state_dict['shoulder_joint_position'], \
                                            state_msg.state_dict['elbow_joint_position'], \
                                            state_msg.state_dict['wrist_angle_joint_position'], state_msg.state_dict['wrist_rotate_joint_position']]
            else:
                goal_joint_position = [state_msg.state_dict['base_joint_position'], state_msg.state_dict['shoulder_joint_position'], \
                                            state_msg.state_dict['elbow_joint_position'], state_msg.state_dict['wrist_angle_joint_position']]
        else:
            goal_joint_position = state_msg.state[6:12]

        self.set_joint_position(goal_joint_position)
        
        if not self.real_robot:
            # Reset collision sensors flags
            self.collision_sensors.update(dict.fromkeys(self.joint_names, False))
        # Start movement of objects
        if self.objects_controller:
            msg = Bool()
            msg.data = True
            self.move_objects_pub.publish(msg)

        self.reset.set()

        for _ in range(20):
            self.control_rate.sleep()

        return 1

    def publish_target_marker(self, target_pose):
        # Publish Target RViz Marker
        t_marker = Marker()
        t_marker.type = 2  # =>SPHERE
        t_marker.scale.x = 0.15
        t_marker.scale.y = 0.15
        t_marker.scale.z = 0.15
        t_marker.action = 0
        t_marker.frame_locked = 1
        t_marker.pose.position.x = target_pose[0]
        t_marker.pose.position.y = target_pose[1]
        t_marker.pose.position.z = target_pose[2]
        rpy_orientation = PyKDL.Rotation.RPY(0.0, 0.0, target_pose[2])
        q_orientation = rpy_orientation.GetQuaternion()
        t_marker.pose.orientation.x = q_orientation[0]
        t_marker.pose.orientation.y = q_orientation[1]
        t_marker.pose.orientation.z = q_orientation[2]
        t_marker.pose.orientation.w = q_orientation[3]
        t_marker.id = 0
        t_marker.header.stamp = rospy.Time.now()
        t_marker.header.frame_id = self.path_frame
        t_marker.color.a = 1.0
        t_marker.color.r = 0.0  # red
        t_marker.color.g = 1.0
        t_marker.color.b = 0.0
        self.target_pub.publish(t_marker)

    def send_action(self, action):
        if self.action_mode == 'abs_pos':
            executed_action = self.publish_env_arm_cmd(action)
        
        elif self.action_mode == 'delta_pos':
            executed_action = self.publish_env_arm_delta_cmd(action)
        else:
            executed_action = []

        return executed_action

    def set_joint_position(self, goal_joint_position):
        """Set robot joint positions to a desired value
        """        

        position_reached = False

        while not position_reached:
            self.publish_env_arm_cmd(goal_joint_position)
            self.get_state_event.clear()
            joint_position = copy.deepcopy(self.joint_position)
            position_reached = np.isclose(goal_joint_position, self._get_joint_ordered_value_list(joint_position),
                                          atol=0.15).all()
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
        msg.points[0].time_from_start = rospy.Duration.from_sec(max(dur))
        self.arm_cmd_pub.publish(msg)
        self.control_rate.sleep()
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
        msg.points[0].time_from_start = rospy.Duration.from_sec(max(dur))
        self.arm_cmd_pub.publish(msg)
        self.control_rate.sleep()
        return position_cmd

    def _on_joint_states(self, msg):
        if self.get_state_event.is_set():
            for idx, name in enumerate(msg.name):
                if name in self.joint_names:
                    self.joint_position[name] = msg.position[idx]
                    self.joint_velocity[name] = msg.velocity[idx]

    def _on_shoulder_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["shoulder"] = True

    def _on_upper_arm_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["upper_arm"] = True

    def _on_forearm_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["forearm"] = True

    def _on_upper_forearm_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["upper_forearm"] = True

    def _on_lower_forearm_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["lower_forearm"] = True

    def _on_wrist_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["wrist"] = True

    def _on_gripper_collision(self, data):
        if data.states == []:
            pass
        else:
            self.collision_sensors["gripper"] = True

    def _on_occupancy_state(self, msg):
        if self.get_state_event.is_set():
            # occupancy_3d_array = np.reshape(msg.data, [dim.size for dim in msg.layout.dim])
            self.voxel_occupancy = msg.data
        else:
            pass

    def _get_joint_states_dict(self, joint_position, joint_velocity):

        d = {}
        if self.dof <= 6:
            d['base_joint_position'] = joint_position['waist']
            d['shoulder_joint_position'] = joint_position['shoulder']
            d['elbow_joint_position'] = joint_position['elbow']
            d['wrist_angle_joint_position'] = joint_position['wrist_angle']
            d['base_joint_velocity'] = joint_velocity['waist']
            d['shoulder_joint_velocity'] = joint_velocity['shoulder']
            d['elbow_joint_velocity'] = joint_velocity['elbow']
            d['wrist_angle_joint_velocity'] = joint_velocity['wrist_angle']
        if self.dof >= 5:
            d['wrist_rotate_joint_position'] = joint_position['wrist_rotate']
            d['wrist_rotate_joint_velocity'] = joint_velocity['wrist_rotate']
        if self.dof >= 6:
            d['forearm_roll_joint_position'] = joint_position['forearm_roll']
            d['forearm_roll_joint_velocity'] = joint_velocity['forearm_roll']
        
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

        if self.dof == 4:
            absolute_joint_velocity_limits = {'waist': 2.35, 'shoulder': 2.35, 'elbow': 2.35, \
                                              'forearm_roll': 2.35, 'wrist_angle': 2.35, 'wrist_rotate': 2.35}
        elif self.dof == 5:
            absolute_joint_velocity_limits = {'waist': 2.35, 'shoulder': 2.35, 'elbow': 2.35, \
                                              'forearm_roll': 2.35, 'wrist_angle': 2.35, 'wrist_rotate': 2.35}
        elif self.dof == 6:
            absolute_joint_velocity_limits = {'waist': 2.35, 'shoulder': 2.35, 'elbow': 2.35, \
                                              'forearm_roll': 2.35, 'wrist_angle': 2.35, 'wrist_rotate': 2.35}
        else:
            raise ValueError('robot_model not recognized')

        return {name: self.max_velocity_scale_factor * absolute_joint_velocity_limits[name] for name in self.joint_names}
