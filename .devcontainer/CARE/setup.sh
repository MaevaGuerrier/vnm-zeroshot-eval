#!/bin/bash
source /opt/ros/humble/setup.bash
source /workspace/ros2_ws/install/setup.bash
export PYTHONPATH=/workspace/.packages_care:$PYTHONPATH
exec "$@"
