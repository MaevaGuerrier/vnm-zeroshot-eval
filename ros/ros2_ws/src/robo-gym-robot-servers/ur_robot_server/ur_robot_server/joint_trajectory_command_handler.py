#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory
from queue import Queue


class JointTrajectoryCH(Node):
    def __init__(self):
        super().__init__('joint_trajectory_command_handler')

        self.declare_parameter('real_robot', False)
        self.declare_parameter('action_cycle_rate', 10.0)

        self.real_robot = self.get_parameter('real_robot').get_parameter_value().bool_value
        ac_rate = self.get_parameter('action_cycle_rate').get_parameter_value().double_value

        if self.real_robot:
            topic = '/scaled_pos_joint_traj_controller/command'
        else:
            topic = '/joint_trajectory_controller/joint_trajectory'
        self.jt_pub = self.create_publisher(JointTrajectory, topic, 10)

        self.subscription = self.create_subscription(
            JointTrajectory,
            'env_arm_command',
            self.callback_env_joint_trajectory,
            10
        )

        self.queue = Queue(maxsize=1)
        self.stop_flag = False

        self.timer = self.create_timer(1.0 / ac_rate, self.joint_trajectory_publisher)

    def callback_env_joint_trajectory(self, msg):
        try:
            self.queue.put_nowait(msg)
        except:
            pass

    def joint_trajectory_publisher(self):
        if self.queue.full():
            msg = self.queue.get()
            self.jt_pub.publish(msg)
            self.stop_flag = False
        else:
            if not self.stop_flag:
                self.jt_pub.publish(JointTrajectory())
                self.stop_flag = True


def main(args=None):
    rclpy.init(args=args)
    node = JointTrajectoryCH()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
