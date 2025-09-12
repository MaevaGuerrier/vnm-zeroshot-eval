#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist, Pose
from sensor_msgs.msg import Image  
from nav_msgs.msg import Odometry
from std_msgs.msg import Header
import copy
from threading import Event
import cv2
from cv_bridge import CvBridge
from robo_gym_server_modules.robot_server.grpc_msgs.python import robot_server_pb2
import numpy as np
import base64

class BunkerRosBridge:

    def __init__(self, real_robot=False, robot_model='bunker'):

        # Event is clear while initialization or set_state is going on
        self.reset = Event()
        self.reset.clear()
        self.get_state_event = Event()
        self.get_state_event.set()

        self.real_robot = real_robot
        self.robot_model = robot_model
        
        self.base_cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)

        control_rate_float = rospy.get_param("~action_cycle_rate", 20.0)
        self.image_height = rospy.get_param("~image_height", 120.0)
        self.image_width = rospy.get_param("~image_width", 160.0)
        self.camera = rospy.get_param("~camera", True) 
        self.resize_image = rospy.get_param("~resize_image", True) 
        self.context_size = rospy.get_param("~context_size", 1)
        self.context_queue = [] 

        self.control_rate = rospy.Rate(control_rate_float)

        # Subscriber to Velocity Command coming from Environment
        # rospy.Subscriber('env_cmd_vel', Twist, self.callback_env_cmd_vel, queue_size=1)
        # self.queue = Queue(maxsize=1)

        self.image = None
        self.bridge = CvBridge()
        self.image_encoding = 'rgb8'
        
        self.base_pose = Pose()
             
        rospy.Subscriber("/lvi_sam/lidar/mapping/odometry", Odometry, self._on_odom)
        # TODO specify your camera topic
        rospy.Subscriber("/usb_cam/image_raw", Image, self._on_image) # "/oak/rgb/image_raw"
        

    # def callback_env_cmd_vel(self, data):
    #     try:
    #         # Add to the Queue the next command to execute
    #         self.queue.put(data)
    #     except:
    #         pass

    # def cmd_vel_publisher(self):
    #         while not rospy.is_shutdown():
    #             # If a command from the environment is waiting to be executed,
    #             # publish the command, otherwise publish zero velocity message
    #             if self.queue.full():
    #                 self.cmd_vel_pub.publish(self.queue.get())
    #             else:
    #                 self.cmd_vel_pub.publish(Twist())
    #             self.rate.sleep()


    def get_state(self):
        self.get_state_event.clear()
        # Get environment state
        state = []
        state_dict = {}
        string_params = {}
        base_pose = [self.base_pose.position.x, self.base_pose.position.y, self.base_pose.position.z, 
                     self.base_pose.orientation.x, self.base_pose.orientation.y, self.base_pose.orientation.z, self.base_pose.orientation.w]
        state += base_pose
        
        state_dict.update(self._get_joint_states_dict(base_pose))
        
        for i, encoded_image in enumerate(self.context_queue):
            string_params[f"camera_image_{i}"] = encoded_image

        string_params["image_count"] = str(len(self.context_queue))
        string_params["context_size"] = str(self.context_size)
        string_params["image_encoding"] = self.image_encoding

        self.get_state_event.set()
        # Create and fill State message
        msg = robot_server_pb2.State(state=state, state_dict=state_dict, string_params=string_params, success=True)
        return msg
        
    def set_state(self, state_msg):
        # Set the initial state of the robot
        # if all(j in state_msg.state_dict for j in self.joint_goal_names):
        #     state_dict = True
        # else:
        #     state_dict = False 
        
        # Clear reset Event
        self.reset.clear()
        
        # Interbotix Joints Positions

        # goal_joint_states = state_msg.state
        # self.set_initial_position(goal_joint_states)

        self.reset.set()

        # for _ in range(20):
        self.control_rate.sleep()

        return 1
    
    def send_action(self, action):
        executed_action_base = self.publish_env_base_cmd(action)

        return executed_action_base
    
    
    def _on_image(self, msg):
        self.image_encoding = msg.encoding
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        if self.resize_image:
            image_array = cv2.resize(cv_image, (int(self.image_width), int(self.image_height)), interpolation=cv2.INTER_LINEAR)
        else:
            image_array = cv_image
        _, buffer = cv2.imencode('.png', image_array)
        image_bytes = buffer.tobytes()

        image_string = base64.b64encode(image_bytes).decode('utf-8')
        if len(self.context_queue) < self.context_size + 1:
            self.context_queue.append(image_string)
        else:
            self.context_queue.pop(0)
            self.context_queue.append(image_string)
            

    
    def publish_env_base_cmd(self, goal):
        msg = Twist()
        msg.linear.x = goal[0]
        msg.angular.z = goal[1]
        self.base_cmd_pub.publish(msg)
        
        self.control_rate.sleep()
        
        return goal
    
                    
    def _on_odom(self, msg):
        if self.get_state_event.is_set():
            self.base_pose = msg.pose.pose
    
    def _get_joint_states_dict(self, base_pose):
        d = {}

        d['base_position_x'] = base_pose[0]
        d['base_position_y'] = base_pose[1]
        d['base_position_z'] = base_pose[2]
        d['base_orientation_x'] = base_pose[3]
        d['base_orientation_y'] = base_pose[4]
        d['base_orientation_z'] = base_pose[5]
        d['base_orientation_w'] = base_pose[6]
        
        return d 
        

    

