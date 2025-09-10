#!/bin/bash
# source ~/.bashrc
# source 

source /opt/ros/humble/setup.bash
source /workspace/ros2_ws/install/setup.bash
# export RMW_IMPLEMENTATION=rmw_zenoh_cpp
# export ZENOH_ROUTER_CHECK_ATTEMPTS=-1
# export ZENOH_CONFIG_OVERRIDE='listen/endpoints=["tcp/0.0.0.0:0"];scouting/multicast/enabled=true'

exec "$@"
