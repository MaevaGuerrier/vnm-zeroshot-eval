#!/bin/bash

source /opt/ros/humble/setup.bash
source /workspace/ros2_ws/install/setup.bash
export PYTHONPATH=/workspace/.packages_crossformer:$PYTHONPATH
alias bunker_server='ros2 launch bunker_robot_server bunker_robot_server.launch'
exec "$@"
