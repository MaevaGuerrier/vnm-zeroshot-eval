#!/bin/bash
# source ~/.bashrc
# source 
target_dir="/workspace/.packages_naivibridger_ros2"
source /opt/ros/humble/setup.bash
export PYTHONPATH=${target_dir}:$PYTHONPATH

# export ROS_MASTER_URI=http://192.168.1.178:11311 # BUNKER1
# export ROS_MASTER_URI=http://192.168.1.139:11311 # BUNKER2 ASLAN
# export ROS_IP=192.168.1.139

exec "$@"
