#!/bin/bash

source /opt/ros/noetic/setup.bash

# export ROS_MASTER_URI=http://192.168.1.178:11311 # BUNKER1
export ROS_MASTER_URI=http://192.168.1.141:11311 # BUNKER2 ASLAN
export ROS_IP=192.168.1.215

# source /opt/ros/humble/setup.bash

# # source /opt/ros/noetic/setup.bash
# source /opt/ros/humble/setup.bash
# export ROS_MASTER_URI=http://192.168.1.178:11311 # noetic

# export ROS_DOMAIN_ID=10 # TODO DO IT ON THE ROBOT AS WELL


# exec rviz -d /workspace/.devcontainer/remotevisualizer/config.rviz # noetic
exec /bin/bash