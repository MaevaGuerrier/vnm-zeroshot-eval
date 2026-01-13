# INIT

**setup submodules**

```bash
git submodule update --init
git submodule foreach git pull origin main
```

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


# Troubleshooting

**Topic is visible but no incoming image data** ([source](https://robotics.stackexchange.com/questions/54802/ros-remote-master-can-see-topics-but-no-data))


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

**fatal: No url found for submodule path 'path' in .gitmodules**
```bash
git rm --cached {path}                                                  
rm -rf .git/modules/{path}
```


# TODO 


```
pip install diffusion_policy/ --target /workspace/.packages_nomad/ --upgrade
```

if 
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at 0xffffaa8717e0>: Failed to establish a new connection: [Errno 113] No route to host')': 

pip install scipy --target /workspace/.packages_nomad --index-url https://pypi.org/simple/






# trying to have ros2 ip setup 

root@mae-rog-14:/workspace/robo-gym/robo_gym# export ROS_DOMAIN_ID=20
root@mae-rog-14:/workspace/robo-gym/robo_gym# export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
root@mae-rog-14:/workspace/robo-gym/robo_gym# export ROS_DISCOVERY_SERVER=192.168.1.178:11811
root@mae-rog-14:/workspace/robo-gym/robo_gym# export FASTRTPS_DEFAULT_PROFILES_FILE=/workspace/super_client_configuration_file.xml
root@mae-rog-14:/workspace/robo-gym/robo_gym# ip route add 192.168.186.0/24 via 192.168.1.178


# Zenoh 


**on BOTH local and remote**

IN DOCKERFILE 

```
ros-humble-rmw-zenoh-cpp 
ros-humble-demo-nodes-cpp 
```


IN SETUP.SH 

```
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ROS_DOMAIN_ID=20
unset ROS_DISCOVERY_SERVER

```



SEE  https://github.com/eclipse-zenoh/zenoh LINUX DEBIAN 

```
echo "deb [signed-by=/etc/apt/keyrings/zenoh-public-key.gpg] https://download.eclipse.org/zenoh/debian-repo/ /" | tee /etc/apt/sources.list.d/zenoh.list > /dev/null


curl -L https://download.eclipse.org/zenoh/debian-repo/zenoh-public-key | gpg --dearmor --yes --output /etc/apt/keyrings/zenoh-public-key.gpg

apt-get update

apt-get install zenoh # IGNORE ERROR CHECK THAT zenohd --help works

```

**On local computer**

zenohd -l tcp/192.168.1.178:7447

**on robot**

zenohd -e tcp/192.168.1.216:7447



# Baselines 



# CARE 

## Installation 


Issues with requ file of UniDepth uses:

```
setuptools 
einops>=0.7.0
gradio
h5py>=3.10.0
huggingface-hub>=0.22.0
imageio
matplotlib
numpy>=2.0.0
opencv-python
pandas
pillow>=10.2.0
protobuf>=4.25.3
scipy
tables
tabulate
termcolor
timm
tqdm
trimesh
triton # USE DIFFERENT URL https://download.pytorch.org/whl/cu118
torchaudio>=2.4.0
xformers>=0.0.26
```


**IMPORTANT** diffusion policy did not setup the file setup.py that enable our usage *pip install /workspace/CARE/diffusion_policy/ --target /workspace/.packages_care/* to work properly. **TODO delete submodule since we already have them in SafeGNM**
Use *_```pip install /workspace/diffusion_policy/ --target /workspace/.packages_care/```** instead.


TODO: get rid of wandb

### Unidepth

Get rid of triton in req file Unidepth and install it with --extra-index-url https://download.pytorch.org/whl/cu118

```
gradio
h5py>=3.10.0
huggingface-hub>=0.22.0
imageio
opencv-python
pandas
pillow>=10.2.0
protobuf>=4.25.3
tables
tabulate
termcolor
timm
tqdm
trimesh
```


# JAX gpu verification 

>>> from jax.lib import xla_bridge
>>> print(xla_bridge.get_backend().platform)
<stdin>:1: DeprecationWarning: jax.lib.xla_bridge.get_backend is deprecated; use jax.extend.backend.get_backend.
gpu