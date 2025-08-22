#!/bin/bash

source /opt/ros/noetic/setup.bash
source /workspace/ros1_ws/devel/setup.bash
export PYTHONPATH=/workspace/.packages_nomad:$PYTHONPATH
alias bunker_server='roslaunch bunker_robot_server bunker_server.launch'
exec "$@"
