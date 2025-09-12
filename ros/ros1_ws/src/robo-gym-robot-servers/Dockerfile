FROM osrf/ros:noetic-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
ENV ROBOGYM_WS=/robogym_ws

# Define build argument for robot type
ARG ROBOT_TYPE="none"

RUN mkdir -p /root/profile.d
RUN mkdir -p $ROBOGYM_WS/src
SHELL ["/bin/bash", "-c"]

# Update package lists and install curl
RUN apt-get update && apt-get install -y \ 
    curl apt-utils build-essential psmisc vim-gtk git swig sudo \
    libcppunit-dev python3-catkin-tools python3-rosdep python3-pip \ 
    python3-rospkg python3-future python3-osrf-pycommon \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies based on ROBOT_TYPE
RUN if [[ "$ROBOT_TYPE" == "interbotix_arm" || "$ROBOT_TYPE" == "interbotix_rover" ]]; then \
      echo "Installing Interbotix Arm dependencies..." && \
      curl 'https://raw.githubusercontent.com/Interbotix/interbotix_ros_manipulators/main/interbotix_ros_xsarms/install/amd64/xsarm_amd64_install.sh' > xsarm_amd64_install.sh && \
      chmod +x xsarm_amd64_install.sh && \
      ./xsarm_amd64_install.sh -n && \
      rm xsarm_amd64_install.sh && \
      echo "source /root/interbotix_ws/devel/setup.bash" >> /root/profile.d/robot.sh; \
    elif [ "$ROBOT_TYPE" = "ur" ]; then \
      cd $ROBOGYM_WS/src && \
      git clone -b $ROS_DISTRO https://github.com/jr-robotics/universal_robot.git && \
      git clone https://github.com/jr-robotics/Universal_Robots_ROS_Driver.git && \
      git clone https://github.com/jr-robotics/Universal_Robots_ROS_Driver.git && \
      source /opt/ros/$ROS_DISTRO/setup.bash && \
      mkdir -p /urdriver_ws/src && \
      cd /urdriver_ws && \
      catkin init && \
      cd /urdriver_ws/src && \
      git clone https://github.com/jr-robotics/Universal_Robots_ROS_Driver.git && \
      git clone -b calibration_devel https://github.com/fmauch/universal_robot.git && \
      cd ~/urdriver_ws && \
      apt update -qq && \
      rosdep update && \
      rosdep install --from-paths src --ignore-src -y && \
      catkin build ; \
    else \
      echo "No robot dependencies installed." && \
      touch /root/profile.d/robot.sh; \
    fi
RUN if [ "$ROBOT_TYPE" = "interbotix_rover" ]; then \
      echo "Installing LoCoBot dependencies..." && \
      curl 'https://raw.githubusercontent.com/Interbotix/interbotix_ros_rovers/main/interbotix_ros_xslocobots/install/xslocobot_remote_install.sh' > xslocobot_remote_install.sh && \
      chmod +x xslocobot_remote_install.sh && \
      echo y | ./xslocobot_remote_install.sh -p ~/interbotix_rover_ws -b create3 -r locobot && \
      rm xslocobot_remote_install.sh && \
      cd ~/interbotix_rover_ws &&  \
      rm -rf devel build && \ 
      rosdep install --from-paths src --ignore-src -r -y --rosdistro $ROS_DISTRO --as-root=apt:false &&\
      source /root/interbotix_ws/devel/setup.bash && \
      catkin_make && \
      echo "source /root/interbotix_rover_ws/devel/setup.bash" >> /root/profile.d/robot.sh; \
    fi

RUN cd $ROBOGYM_WS &&\
    chmod +x /root/profile.d/robot.sh && \
    . /root/profile.d/robot.sh && \
    apt-get update &&\
    rosdep install --from-paths src -i -y --rosdistro $ROS_DISTRO --as-root=apt:false &&\
    catkin init && \
    catkin build && \
    pip3 install robo-gym-server-modules scipy numpy && \
    pip3 install protobuf==3.20 && \
    rm -rf /var/lib/apt/lists/*

ADD . $ROBOGYM_WS/src/robo-gym-robot-servers

RUN if [ "$ROBOT_TYPE" = "interbotix_arm" ]; then \
      rm $ROBOGYM_WS/src/robo-gym-robot-servers/interbotix_arm_robot_server/CATKIN_IGNORE; \
    elif [ "$ROBOT_TYPE" = "interbotix_rover" ]; then \
      rm $ROBOGYM_WS/src/robo-gym-robot-servers/interbotix_rover_robot_server/CATKIN_IGNORE; \
    elif [ "$ROBOT_TYPE" = "universal_robot" ]; then \
      rm $ROBOGYM_WS/src/robo-gym-robot-servers/ur_robot_server/CATKIN_IGNORE; \
    fi

# Build ROS Workspace
RUN source $ROBOGYM_WS/devel/setup.bash &&\ 
    cd $ROBOGYM_WS && \
    apt-get update && \
    rosdep install --from-paths src -i -y --rosdistro $ROS_DISTRO --as-root=apt:false && \
    catkin build && \
    rm -rf /var/lib/apt/lists/*

# Source ROS setup script
RUN echo "source /robogym_ws/devel/setup.bash" >> ~/.bashrc
RUN sed -i '/export.*ROS_MASTER_URI/d' ~/.bashrc

# Create an entrypoint script for real/sim robot handling
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo 'source /robogym_ws/devel/setup.bash' >> /entrypoint.sh && \
    echo 'if [ "$REAL_ROBOT" = "true" ]; then' >> /entrypoint.sh && \
    echo '  echo "Running with real robot configuration"' >> /entrypoint.sh && \
    echo '  if [ -n "$ROSLAUNCH_ARGS" ]; then' >> /entrypoint.sh && \
    echo '    echo "Using custom launch arguments: $ROSLAUNCH_ARGS"' >> /entrypoint.sh && \
    echo '    roslaunch ${ROBOT_TYPE}_robot_server ${ROBOT_TYPE}_robot_server.launch $ROSLAUNCH_ARGS' >> /entrypoint.sh && \
    echo '  else' >> /entrypoint.sh && \
    echo '    echo "Using default launch arguments"' >> /entrypoint.sh && \
    echo '    roslaunch ${ROBOT_TYPE}_robot_server ${ROBOT_TYPE}_robot_server.launch real_robot:=true' >> /entrypoint.sh && \
    echo '  fi' >> /entrypoint.sh && \
    echo 'else' >> /entrypoint.sh && \
    echo '  echo "Running in simulation mode"' >> /entrypoint.sh && \
    echo '  start-server-manager && attach-to-server-manager' >> /entrypoint.sh && \
    echo 'fi' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
