#!/bin/bash
target_dir="/workspace/.packages_naivibridger_ros2" # the var is also set in the dockerfile setup.sh we could remove here
echo "Target dir is set to $target_dir"
pip install third_party/diffusion_policy/ --target=$target_dir
pip install src/NaiviBridger/deployment --target=$target_dir
pip install src/NaiviBridger/train/ --target=$target_dir