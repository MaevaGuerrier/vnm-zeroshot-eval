#!/bin/bash
# source ~/.bashrc
source /opt/ros/humble/setup.bash
source /workspace/ros2_ws/install/setup.bash
export PYTHONPATH=$CONDA_PREFIX/lib/python3.10/site-packages:$PYTHONPATH
export ROS_DOMAIN_ID=20

exec "$@"
