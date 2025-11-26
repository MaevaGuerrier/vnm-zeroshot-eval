#!/bin/bash

source /opt/ros/noetic/setup.bash
# source /workspace/ros1_ws/install/setup.bash
target="/workspace/.packages_nomad"
export PYTHONPATH=$target:$PYTHONPATH
# export ROS_MASTER_URI=http://192.168.1.178:11311 # BUNKER1
export ROS_MASTER_URI=http://192.168.1.23:11311 # BUNKER2 ASLAN
export ROS_IP=192.168.1.23
exec "$@"
    
