# Inside docker 

**ONLY INSIDE DOCKER OR LOSE THINGS**

cd /opt/ros/noetic
source devel.bash



# other

cd mist_ws/
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

## Updating submodule 

At root of your git folder simpy use the command `git submodule foreach git pull`

## Usage 

### Deployment 

**Navigate**

*Prequisite: topomap created*

`./navigate.sh '--dir <topo_dir>'`


# ROS2 

```
source /opt/ros/humble/setup.bash
cd ros2_ws
chmod +x src/robo-gym-robot-servers/bunker_robot_server/bunker_robot_server/robot_server.py
colcon build --symlink-install --event-handlers console_direct+
source install/setup.bash
```

## Visualize


### Looking at sub_goal and goal_img while navigating 

We are using rviz to visualize the image data.

1. Run on robot the launch script 
2. On local pc: ```ROS_MASTER_URI=http://{ROBOT_IP}:11311```
3. On local pc use a docker with ros and launch rviz 
4. Run navigate.sh on robot
5. Select the topics you want to see on rviz in local pc, **in our case: /topoplan/subgoal, /topoplan/goal_img and /topoplan/closest_node_img**

**TROUBLESHOOTING: Topic is visible but no incoming image data** ([source](https://robotics.stackexchange.com/questions/54802/ros-remote-master-can-see-topics-but-no-data))


1. Add the robot ip to your local computer in /etc/hosts (in our case inside docker container). 
   Add the following:

```shell=ROBOT_IP ROBOT_HOSTNAME # ADD THIS LINE```

Such that in **/etc/hosts**:

```shell=
127.0.0.1 localhost
127.0.1.1 YOUR_PC_HOSTNAME
ROBOT_IP ROBOT_HOSTNAME # ADD THIS LINE

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

```

**pydantic** for usb_cam ros2 package need to be install this way:

ROS 2 Humble expects Pydantic 1.x.

Check your Pydantic version: 

```
pip show pydantic
```

If you see Version: 2.x, that’s the problem.

Downgrade to v1:

```
pip install "pydantic<2" --force-reinstall
```

# TODO 


```
pip install diffusion_policy/ --target /workspace/.packages_nomad/ --upgrade
```

pip install scipy --target /workspace/.packages_nomad --index-url https://pypi.org/simple/