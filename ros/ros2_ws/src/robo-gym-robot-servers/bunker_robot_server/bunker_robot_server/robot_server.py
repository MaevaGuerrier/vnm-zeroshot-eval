#!/usr/bin/env python3
import grpc
import rclpy
from rclpy.node import Node
from concurrent import futures
from bunker_robot_server.ros_bridge import BunkerRosBridge
from robo_gym_server_modules.robot_server.grpc_msgs.python import robot_server_pb2, robot_server_pb2_grpc
import time


class RobotServerServicer(robot_server_pb2_grpc.RobotServerServicer):
    def __init__(self, node: Node):
        self.prev_action = None
        self.node = node
        self.rosbridge = BunkerRosBridge(node)
        
    def GetState(self, request, context):
        try:
            self.node.get_logger().debug('Getting state...')
            return self.rosbridge.get_state()
        except Exception as e:
            self.node.get_logger().error(f'Failed to get state: {e}')
            return robot_server_pb2.State(success=0)

    def SetState(self, request, context):
        try:
            self.node.get_logger().debug('Setting state...')
            self.rosbridge.set_state(state_msg=request)
            return robot_server_pb2.Success(success=1)
        except Exception as e:
            self.node.get_logger().error(f'Failed to set state: {e}')
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
            # print(f"PREV ACTION: {self.prev_action}")
            self.node.get_logger().info(f"PREV ACTION: {self.prev_action}")
            self.node.get_logger().info('Sending action...')
            executed_action = self.rosbridge.send_action(self.prev_action)
            return robot_server_pb2.Success(success=1)
        except:
            self.node.get_logger().error('Failed to send action', exc_info=True)
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
            # print(f"PREV ACTION: {self.prev_action}")
            self.node.get_logger().info(f"PREV ACTION: {self.prev_action}")
            self.node.get_logger().info('Sending action and getting state...')
            self.rosbridge.send_action(self.prev_action)
            return self.rosbridge.get_state()
        except Exception as e:
            self.node.get_logger().error(f'Failed to send action and get state: {e}')
            return robot_server_pb2.State(success=0)




class RobotServerNode(Node):
    def __init__(self):
        super().__init__('robot_server')

        self.declare_parameter('server_port', 50051)
        self.declare_parameter('real_robot', True)
        self.declare_parameter('robot_model', 'bunker')

        self.server_port = str(self.get_parameter('server_port').value)
        self.real_robot = self.get_parameter('real_robot').value
        self.robot_model = self.get_parameter('robot_model').value

        self.get_logger().info(f'Waiting 5 seconds before starting robot server...')
        time.sleep(5)
        self.serve()

    def serve(self):
        self.get_logger().info('Starting Bunker Robot Server...')
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        robot_server_pb2_grpc.add_RobotServerServicer_to_server(
            RobotServerServicer(self),
            server
        )
        server.add_insecure_port(f'[::]:{self.server_port}')
        server.start()
        msg = 'Real Robot' if self.real_robot else 'Sim Robot'
        self.get_logger().info(f'{self.robot_model} {msg} Server started at port {self.server_port}')

        try:
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.1)
        except KeyboardInterrupt:
            self.get_logger().info('Shutting down server...')
            server.stop(0)

def main(args=None):
    rclpy.init(args=args)
    node = RobotServerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()