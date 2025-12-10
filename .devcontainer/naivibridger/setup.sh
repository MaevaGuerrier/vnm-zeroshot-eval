#!/bin/bash
# source ~/.bashrc
# source 
target="/workspace/.packages_naivibridger"
source /opt/ros/noetic/setup.bash
export PYTHONPATH=${target}:$PYTHONPATH

# export ROS_MASTER_URI=http://192.168.1.178:11311 # BUNKER1
export ROS_MASTER_URI=http://192.168.1.139:11311 # BUNKER2 ASLAN
export ROS_IP=192.168.1.139

exec "$@"
