#!/usr/bin/env python
import grpc
import rospy
from concurrent import futures
from bunker_robot_server.ros_bridge import BunkerRosBridge
from robo_gym_server_modules.robot_server.grpc_msgs.python import robot_server_pb2, robot_server_pb2_grpc
import time

class RobotServerServicer(robot_server_pb2_grpc.RobotServerServicer):
    def __init__(self,real_robot,robot_model):
        self.rosbridge = BunkerRosBridge(real_robot=real_robot,robot_model=robot_model)
        self.prev_action = None

    def GetState(self, request, context):
        try:
            return self.rosbridge.get_state()
        except:
            rospy.logerr('Failed to get state', exc_info=True)
            return robot_server_pb2.State(success=0)

    def SetState(self, request, context):
        try:
            self.rosbridge.set_state(state_msg=request)
            return robot_server_pb2.Success(success=1)
        except:
            rospy.logerr('Failed to set state', exc_info=True)
            return robot_server_pb2.Success(success=0)

    def SendAction(self, request, context):
        try:
            
            if self.prev_action is None:
                self.prev_action = request.action
            elif request.action != [0.0, 0.0]:
                self.prev_action = request.action
                # TODO 
            #     self.time = time.time() 
            # else:
            #     elapsed_time = time.time() - self.time
            #     if elapsed_time > 1.0:  # If more than 1 second has passed
            #         self.prev_action = [0.0, 0.0]
            #         print("NOT RECEIVING ACTION OTHER THAN 0, exiting")
            #         exit()

            print(f"PREV ACTION: {self.prev_action}")

            executed_action = self.rosbridge.send_action(self.prev_action )
            return robot_server_pb2.Success(success=1)
        except:
            rospy.logerr('Failed to send action', exc_info=True)
            return robot_server_pb2.Success(success=0)

    def SendActionGetState(self, request, context):
        try:
            if self.prev_action is None:
                self.prev_action = request.action
            elif request.action != [0.0, 0.0]:
                self.prev_action = request.action
                # self.time = time.time() 
            # else:
            #     elapsed_time = time.time() - self.time
            #     if elapsed_time > 1.0:  # If more than 1 second has passed
            #         self.prev_action = [0.0, 0.0]
            #         print("NOT RECEIVING ACTION OTHER THAN 0, exiting")
            #         exit()

            print(f"PREV ACTION: {self.prev_action}")
            executed_action = self.rosbridge.send_action(self.prev_action)
            return self.rosbridge.get_state()
        except:
            rospy.logerr('Failed to send action and get state', exc_info=True)
            return robot_server_pb2.State(success=0)


def serve():
    rospy.loginfo('Starting bunker Rover Robot Server...')
    server_port = rospy.get_param('~server_port')
    robot_model = rospy.get_param('~robot_model')
    real_robot = rospy.get_param('~real_robot')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    robot_server_pb2_grpc.add_RobotServerServicer_to_server(
        RobotServerServicer(real_robot=real_robot, robot_model=robot_model), server)
    server.add_insecure_port('[::]:'+repr(server_port))
    server.start()
    rospy.loginfo(robot_model + ' Real Robot Server started at ' + repr(server_port))

    rospy.spin()


if __name__ == '__main__':
    try:
        wait_time = 5
        rospy.init_node('robot_server')
        rospy.loginfo('Waiting {}s before starting initialization of Robot Server'.format(wait_time))
        rospy.sleep(wait_time)
        serve()
    except (KeyboardInterrupt, SystemExit):
        pass