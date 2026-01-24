#!/bin/bash

# CAREFUL MAKE SURE TARGET DIR IS CORRECT
target_dir=/workspace/.packages_nomad_ros2
PROJECT_DIR="visualnav-transformer"

# We had issues when changing package contents, remaining build files would interfere when installing again.
# Clean everything
echo "Cleaning all build artifacts"
rm -rf "$target_dir" # CAREFUL MAKE SURE TARGET DIR IS CORRECT
find /workspace/src/$PROJECT_DIR/ -type d \( -name "build" -o -name "dist" -o -name "*.egg-info" -o -name "__pycache__" \) -exec rm -rf {} + 2>/dev/null


echo "Installing packages to $target_dir"
pip install third_party/diffusion_policy/ --target=$target_dir
pip install src/visualnav-transformer/train --target=$target_dir
pip install src/visualnav-transformer/deployment --target=$target_dir


LAUNCH_SCRIPT_DIR="/workspace/src/$PROJECT_DIR/deployment/src/ros2/"
LAUNCH_SCRIPT="navigate.sh"

# Create aliases that pass predefined first argument and allow additional args
alias gnm="cd ${LAUNCH_SCRIPT_DIR} && ./${LAUNCH_SCRIPT} gnm_onnx"
alias vint="cd ${LAUNCH_SCRIPT_DIR} && ./${LAUNCH_SCRIPT} vint_onnx"
alias nomad="cd ${LAUNCH_SCRIPT_DIR} && ./${LAUNCH_SCRIPT} nomad_onnx"

# Add more aliases as needed