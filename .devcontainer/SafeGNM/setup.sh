#!/bin/bash
# source ~/.bashrc
# source 

source /opt/ros/noetic/setup.bash
source /workspace/ros1_ws/install/setup.bash
# export RMW_IMPLEMENTATION=rmw_zenoh_cpp
# export ZENOH_ROUTER_CHECK_ATTEMPTS=-1
# export ZENOH_CONFIG_OVERRIDE='listen/endpoints=["tcp/0.0.0.0:0"];scouting/multicast/enabled=true'

exec "$@"
