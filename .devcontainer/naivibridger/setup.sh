#!/bin/bash
# source ~/.bashrc
# source 
target_dir="/workspace/.packages_naivibridger_ros2"
source /opt/ros/humble/setup.bash
export PYTHONPATH=${target_dir}:$PYTHONPATH

export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ZENOH_ROUTER_CHECK_ATTEMPTS=-1
export ZENOH_CONFIG_OVERRIDE='listen/endpoints=["tcp/0.0.0.0:0"];scouting/multicast/enabled=true'

exec "$@"
