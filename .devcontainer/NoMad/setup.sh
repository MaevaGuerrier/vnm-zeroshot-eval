#!/bin/bash

source /opt/ros/humble/setup.bash
target="/workspace/.packages_nomad_ros2"
export PYTHONPATH=$target:$PYTHONPATH
export ROS_MASTER_URI=http://192.168.1.154:11311 # botman
export ROS_IP=192.168.1.154
exec "$@"
    
