#!/bin/bash

source /opt/ros/humble/setup.bash
target_dir=/workspace/.packages_nomad_ros2
export PYTHONPATH=${target_dir}:$PYTHONPATH
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ZENOH_ROUTER_CHECK_ATTEMPTS=-1
export ZENOH_CONFIG_OVERRIDE='listen/endpoints=["tcp/0.0.0.0:0"];scouting/multicast/enabled=true'
exec "$@"
    
