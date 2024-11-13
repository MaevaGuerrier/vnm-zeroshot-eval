Inside docker 

cd mist_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3 -DPYTHON_INCLUDE_DIR=/usr/include/python3
source devel/setup.bash

If you are tryin to use this project without using the given shell scripts, make sure to run `cd /workspace/src/visualnav-transformer` and then run ` pip install -e train/` within the docker container.

If you are keeping the logic of using shell scripts you can do:
```bash
eval "$(conda shell.bash hook)"
conda activate vint_deployment
# Navigate to the directory containing the package
cd /workspace/src/visualnav-transformer
# Install the package in editable mode
pip install -e train/

# Change back the directory to the working dir with the navigate.py script
cd /workspace/src/visualnav-transformer/deployment/src

```