#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist, Pose
from trajectory_msgs.msg import JointTrajectoryPoint, JointTrajectory
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
import copy
from threading import Event
from robo_gym_server_modules.robot_server.grpc_msgs.python import robot_server_pb2
import numpy as np


class InterbotixRoverRosBridge:

    def __init__(self, real_robot=False, robot_model='locobot_wx250s'):

        # Event is clear while initialization or set_state is going on
        self.reset = Event()
        self.reset.clear()
        self.get_state_event = Event()
        self.get_state_event.set()

        self.real_robot = real_robot
        self.robot_model = robot_model
        self.robot_name, arm_model = robot_model.split('_')
        
        if arm_model == 'wx250s':
            self.dof = 6
        elif arm_model == 'px100':
            self.dof = 4
        else:
            self.dof = 5
        
        self.base_cmd_pub = rospy.Publisher(self.robot_name + '/cmd_vel', Twist, queue_size=1)
        self.arm_cmd_pub = rospy.Publisher('/env_arm_command', JointTrajectory, queue_size=1)

        control_rate_float = rospy.get_param("~action_cycle_rate", 125.0)
        self.control_rate = rospy.Rate(control_rate_float)

        # Joint States
        if self.dof == 4:
            self.joint_names = ['waist', 'shoulder', 'elbow', 'wrist_angle']
            self.joint_goal_names = ['base_joint_position', 'shoulder_joint_position', 'elbow_joint_position',
                                         'wrist_angle_joint_position']
        elif self.dof == 5:
            self.joint_names = ['waist', 'shoulder', 'elbow', 'wrist_angle', 'wrist_rotate']
            self.joint_goal_names = ['base_joint_position', 'shoulder_joint_position', 'elbow_joint_position',
                                         'wrist_angle_joint_position', 'wrist_rotate_joint_position']
        elif self.dof == 6:
            self.joint_names = ['waist', 'shoulder', 'elbow', 'forearm_roll', 'wrist_angle', 'wrist_rotate']
            self.joint_goal_names = ['base_joint_position', 'shoulder_joint_position', 'elbow_joint_position',
                                         'forearm_roll_joint_position', 'wrist_angle_joint_position',
                                         'wrist_rotate_joint_position']

        self.base_joint_names = ['right_wheel_joint', 'left_wheel_joint']
        
        self.joint_position = dict.fromkeys(self.joint_names + self.base_joint_names, 0.0)
        self.joint_velocity = dict.fromkeys(self.joint_names + self.base_joint_names, 0.0)
        
        self.base_pose = Pose()
        
        rospy.Subscriber(self.robot_name + "/joint_states", JointState, self._on_joint_states)       
        rospy.Subscriber(self.robot_name + "/odom", Odometry, self._on_odom)
        
        self.min_traj_duration = 0.5 # minimum trajectory duration (s)
        self.joint_velocity_limits = self._get_joint_velocity_limits()
        
    def get_state(self):
        self.get_state_event.clear()
        # Get environment state
        state = []
        state_dict = {}

        joint_position = copy.deepcopy(self.joint_position)
        joint_velocity = copy.deepcopy(self.joint_velocity)
        
        # append position and velocity as lists to state
        state += self._get_joint_ordered_value_list(joint_position)
        state += self._get_joint_ordered_value_list(joint_velocity)
        
        base_pose = [self.base_pose.position.x, self.base_pose.position.y, self.base_pose.position.z, 
                     self.base_pose.orientation.x, self.base_pose.orientation.y, self.base_pose.orientation.z, self.base_pose.orientation.w]
        state += base_pose
        
        state_dict.update(self._get_joint_states_dict(joint_position, joint_velocity, base_pose))

        self.get_state_event.set()
        # Create and fill State message
        msg = robot_server_pb2.State(state=state, state_dict=state_dict, success=True)
        return msg
        
    def set_state(self, state_msg):
        # Set the initial state of the robot
        if all(j in state_msg.state_dict for j in self.joint_goal_names):
            state_dict = True
        else:
            state_dict = False 
        
        # Clear reset Event
        self.reset.clear()
        
        # Interbotix Joints Positions
        if state_dict:
            goal_joint_states = [state_msg.state_dict[joint] for joint in self.joint_goal_names]

        else:
            goal_joint_states = state_msg.state[6:12]
        self.set_initial_position(goal_joint_states)

        self.reset.set()

        for _ in range(20):
            self.control_rate.sleep()

        return 1
    
    def send_action(self, action):
        executed_action = self.publish_env_arm_cmd(action[:-2])
        
        executed_action_base = self.publish_env_base_cmd(action[-2:])

        return executed_action + executed_action_base
    
    def set_initial_position(self, goal_joint_position):
        """Set robot joint positions to a desired value, called on reset
        """        
        arm_position_reached = False
        
        arm_goal = goal_joint_position
        
        while not arm_position_reached:
            self.publish_env_arm_cmd(arm_goal)
            self.get_state_event.clear()
            joint_position = copy.deepcopy(self.joint_position)
            arm = {k: joint_position[k] for k in joint_position.keys() - {'right_wheel_joint', 'left_wheel_joint'}}
            arm_position_reached = np.isclose(arm_goal, self._get_joint_ordered_value_list(arm),
                                          atol=0.05).all()
            
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
    
    def publish_env_base_cmd(self, goal):
        msg = Twist()
        msg.linear.x = goal[0]
        msg.angular.z = goal[1]
        self.base_cmd_pub.publish(msg)
        
        self.control_rate.sleep()
        
        return goal
    
    def _on_joint_states(self, msg):
        if self.get_state_event.is_set():
            for idx, name in enumerate(msg.name):
                if name in self.joint_names:
                    self.joint_position[name] = msg.position[idx]
                    self.joint_velocity[name] = msg.velocity[idx]
                    
    def _on_odom(self, msg):
        if self.get_state_event.is_set():
            self.base_pose = msg.pose.pose
    
    def _get_joint_states_dict(self, joint_position, joint_velocity, base_pose):

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
            
        d['right_wheel_joint_position'] = joint_position['right_wheel_joint']
        d['left_wheel_joint_position'] = joint_position['left_wheel_joint']
        d['right_wheel_joint_velocity'] = joint_velocity['right_wheel_joint']
        d['left_wheel_joint_velocity'] = joint_velocity['left_wheel_joint']
        d['base_position_x'] = base_pose[0]
        d['base_position_y'] = base_pose[1]
        d['base_position_z'] = base_pose[2]
        d['base_orientation_x'] = base_pose[3]
        d['base_orientation_y'] = base_pose[4]
        d['base_orientation_z'] = base_pose[5]
        d['base_orientation_w'] = base_pose[6]
        
        return d 
        
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

        return {name: absolute_joint_velocity_limits[name] for name in self.joint_names}
