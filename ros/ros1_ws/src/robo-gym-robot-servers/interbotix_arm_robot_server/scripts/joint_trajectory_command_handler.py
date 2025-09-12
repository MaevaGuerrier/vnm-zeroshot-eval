#!/usr/bin/env python
import rospy
from trajectory_msgs.msg import JointTrajectoryPoint, JointTrajectory
from interbotix_xs_msgs.msg import JointGroupCommand
from queue import Queue

class JointTrajectoryCH:
    def __init__(self):
        rospy.init_node('joint_trajectory_command_handler')
        self.real_robot = rospy.get_param("~real_robot")
        ac_rate = rospy.get_param("~action_cycle_rate")
        self.rate = rospy.Rate(ac_rate)

        self.robot_model = rospy.get_param('/robot_server/robot_model')

        # Publisher to JointTrajectory robot controller
        if self.real_robot:
            self.jt_pub = rospy.Publisher(self.robot_model + '/commands/joint_group', JointGroupCommand, queue_size=10)
        else:
            self.jt_pub = rospy.Publisher(self.robot_model + '/arm_controller/command', JointTrajectory, queue_size=10)

        # Subscriber to JointTrajectory Command coming from Environment
        rospy.Subscriber('env_arm_command', JointTrajectory, self.callback_env_joint_trajectory, queue_size=1)
        self.msg = JointTrajectory()
        # Queue with maximum size 1
        self.queue = Queue(maxsize=1)
        # Flag used to publish empty JointTrajectory message only once when interrupting execution
        self.stop_flag = False 

    def callback_env_joint_trajectory(self, data):
        try:
            # Add to the Queue the next command to execute
            self.queue.put(data)
        except:
            pass

    def joint_trajectory_publisher(self):

        while not rospy.is_shutdown():
            # If a command from the environment is waiting to be executed,
            # publish the command, otherwise preempt trajectory
            if self.queue.full():
                if self.real_robot:
                    trajectory = self.queue.get()
                    command_msg = JointGroupCommand()
                    command_msg.name = 'arm'
                    command_msg.cmd = trajectory.points[0].positions
                    self.jt_pub.publish(command_msg)
                else:
                    self.jt_pub.publish(self.queue.get())
                self.stop_flag = False 
            else:
                # If the empty JointTrajectory message has not been published, publish it and
                # set the stop_flag to True, else pass
                if not self.stop_flag:
                    if self.real_robot:
                        self.jt_pub.publish(JointGroupCommand())
                    else:
                        self.jt_pub.publish(JointTrajectory())
                    self.stop_flag = True 
                else: 
                    pass 
            self.rate.sleep()


if __name__ == '__main__':
    try:
        ch = JointTrajectoryCH()
        ch.joint_trajectory_publisher()
    except rospy.ROSInterruptException:
        pass
