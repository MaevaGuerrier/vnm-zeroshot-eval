# TODOs

- Unifies the publishers, we have repeated code in the navigation files
- Docs

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


# Cameras 

## OAK-D pro 

View [src](https://docs.luxonis.com/software-v3/depthai/ros/depthai-ros/) 
```
sudo apt install ros-<distro>-depthai-ros
```


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



# HABITAT 


## habitat sim

<!-- pip install --upgrade pip setuptools wheel -->



python3 -m venv habitat_env

source habitat_env/bin/activate 


cmake --version 
cmake >= 3.10

CMake Error at deps/glfw/CMakeLists.txt:206 (message):
  RandR headers not found; install libxrandr development package

SOL -> sudo apt-get install xorg-dev libglu1-mesa-dev



CMake Error at /usr/share/cmake-3.28/Modules/FindPackageHandleStandardArgs.cmake:230 (message):
  Could NOT find EGL (missing: EGL_LIBRARY EGL_INCLUDE_DIR)
Call Stack (most recent call first):
  /usr/share/cmake-3.28/Modules/FindPackageHandleStandardArgs.cmake:600 (_FPHSA_FAILURE_MESSAGE)
  deps/magnum/modules/FindEGL.cmake:65 (find_package_handle_standard_args)
  deps/magnum/src/Magnum/Platform/CMakeLists.txt:110 (find_package)


SOL -> sudo apt-get install -y libegl1-mesa-dev libgles2-mesa-dev


Could NOT find Assimp (missing: Assimp_LIBRARY Assimp_INCLUDE_DIR)
SOL -> sudo apt-get install -y libassimp-dev


git clone https://github.com/facebookresearch/habitat-sim.git

cd habitat-sim

pip install -r requirements.txt 

pip install setuptools 

python setup.py --bullet --with-cuda build_ext --parallel 8 install --cmake-args="-DUSE_SYSTEM_ASSIMP=ON"


## Testing install habitat sim 

sudo apt install git-lfs

git lfs install

mkdir ../habitat_scenes

python -m habitat_sim.utils.datasets_download --uids habitat_test_scenes --data-path data/

python -m habitat_sim.utils.datasets_download --uids habitat_example_objects --data-path data/

python examples/viewer.py --scene data/scene_datasets/habitat-test-scenes/skokloster-castle.glb


**Troubleshooting** 

Unresponsive keys -> make sure you click on viewer and then press keyboard keys


# Habitat lab 

git clone --branch stable https://github.com/facebookresearch/habitat-lab.git

cd habitat-lab/habitat-lab

pip install -r requirements.txt

python install -e .



**issue**
ValueError: Requested RearrangeDataset config paths 'data/datasets/replica_cad/rearrange/v2/train/rearrange_easy.json.gz' or 'data/replica_cad/' are not downloaded locally. Aborting.


https://github.com/facebookresearch/habitat-lab/issues/2100
python -m habitat_sim.utils.datasets_download --uids replica_cad_dataset --data-path data/
python -m habitat_sim.utils.datasets_download --uids rearrange_dataset_v2 --data-path data/
python -m habitat_sim.utils.datasets_download --uids hab_fetch --data-path data/
python -m habitat_sim.utils.datasets_download --uids ycb --data-path data/


Environment creation successful
[10:51:01:376042]:[Error]:[Metadata] AOAttributesManager.cpp(199)::preRegisterObjectFinalize : ArticulatedObjectAttributes template named `data/robots/hab_fetch/robots/hab_suction.urdf` specifies the URDF Filepath `data/robots/hab_fetch/robots/hab_suction.urdf` full path ``, but this file cannot be found, so registration is aborted.
[1]    55491 segmentation fault (core dumped)  python examples/example.py

https://github.com/facebookresearch/habitat-lab/issues/896

python -m habitat_sim.utils.datasets_download --uids rearrange_task_assets --data-path data/


Now example should work python examples/example.py 
You should see:
```
Environment creation successful
Agent acting inside environment.
Episode finished after 230 steps.
```

**Interactive play**


pip install pybullet==3.0.4
pip install pygame==2.0.1


**issues with interactive_play**


Bad inertia tensor properties, setting inertia to zero for link: l_gripper_finger_link
X Error of failed request:  BadAccess (attempt to access private resource denied)
  Major opcode of failed request:  152 (GLX)
  Minor opcode of failed request:  5 (X_GLXMakeCurrent)
  Serial number of failed request:  87
  Current serial number in output stream:  87

https://github.com/facebookresearch/habitat-lab/issues/2142#issuecomment-2743835356  

Comment pygame.init() on line 476 and paste it in line 801 in file examples/interactive_play.py




# TODOs


**scene addition**

@TODO check it works
put scene .glb and .navmesh files under the data_habitat/versioned_data/habitat_test_scenes_1.0 directory.


**vel control**
@TODO 
https://github.com/facebookresearch/habitat-lab/blob/380ac0a7d8c4ead1532f109b15d329473212eae9/habitat/tasks/rearrange/actions/actions.py#L227




???

pip install --upgrade habitat-sim==0.3.7



@TODO 

I did for now DEFAULT_PHYSICS_CONFIG_PATH = "/home/mae/Documents/GIT/Research/SafeGNM/sim/habitat/habitat-lab/data/default.physics_config.json"

In habitat-lab/habitat-lab/habitat/datasets/utils.py


@TODOS 

python collect_manual.py --habitat-config ../conf_habitat/config_habitat.yaml --user-config ../conf_habitat/config.yaml --output trajectories/manual


2]:[Error]:[Scene] SemanticScene.cpp(139)::loadSemanticSceneDescriptor : SSD Load Failure! File with SemanticAttributes-provided name `../habitat-sim/data/versioned_data/annawan/Annawan.scn` exists but failed to load.
[15:39:40:284498]:[Warning]:[Sim] Simulator.cpp(595)::instanceStageForSceneAttributes : The active scene does not contain semantic annotations : activeSemanticSceneID_ = 0
[15:39:40:348216]:[Error]:[Nav] PathFinder.cpp(895)::build : Could not build Detour navmesh
[15:39:40:348261]:[Error]:[Sim] Simulator.cpp(838)::recomputeNavMesh : Failed to build navmesh