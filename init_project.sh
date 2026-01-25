#!/bin/bash

# CAREFUL MAKE SURE TARGET DIR IS CORRECT
target_dir="/workspace/.packages_naivibridger_ros2"
PROJECT_DIR="NaiviBridger"

# We had issues when changing package contents, remaining build files would interfere when installing again.
# Clean everything
echo "Cleaning all build artifacts"
rm -rf "$target_dir" # CAREFUL MAKE SURE TARGET DIR IS CORRECT
find /workspace/src/$PROJECT_DIR/ -type d \( -name "build" -o -name "dist" -o -name "*.egg-info" -o -name "__pycache__" \) -exec rm -rf {} + 2>/dev/null


echo "Installing packages to $target_dir"
pip install /workspace/third_party/diffusion_policy/ --target="$target_dir"
pip install /workspace/src/NaiviBridger/deployment/ --target="$target_dir"
pip install /workspace/src/NaiviBridger/train/ --target="$target_dir"


LAUNCH_SCRIPT_DIR="/workspace/src/$PROJECT_DIR/deployment/src/ros2/"
LAUNCH_SCRIPT="navigate.sh"

# Create aliases that pass predefined first argument and allow additional args
alias bridger="cd ${LAUNCH_SCRIPT_DIR} && ./${LAUNCH_SCRIPT} onnx"

alias creatopo="cd ${LAUNCH_SCRIPT_DIR} && ./create_topomap.sh"

# Add more aliases as needed