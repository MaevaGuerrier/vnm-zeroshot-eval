#!/bin/bash

source /opt/ros/noetic/setup.bash

export ROS_MASTER_URI=http://192.168.1.23:11311



exec rviz -d /workspace/.devcontainer/remotevisualizer/config.rviz
