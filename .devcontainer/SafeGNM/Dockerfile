#####################
# Base image #
#####################
FROM nvidia/cuda:12.3.2-runtime-ubuntu20.04 as base


ARG ROS_VERSION="noetic"

# ==
# Disable dialog frontend
# ==
ARG DEBIAN_FRONTEND=noninteractive

# ==
# Select shell
# ==
SHELL ["/bin/bash", "-c"]

# ==
# Install ROS
# ==
RUN apt update \
    && apt install --no-install-recommends -y curl gnupg lsb-release git build-essential nano \
    && sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
    && curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - \
    && apt update \
    && apt install --no-install-recommends -y ros-${ROS_VERSION}-desktop-full \
    && apt install --no-install-recommends -y \
        python3-pip \
        python3-venv \
        python3-rosdep \
        python3-rosinstall \
        python3-rosinstall-generator \
        python3-wstool \
        python3-catkin-tools \
        python3-osrf-pycommon \
    && rm -f "/etc/ros/rosdep/sources.list.d/20-default.list" \
    && rosdep init \
    && rosdep update \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /tmp/requirements.txt
RUN pip install -v -r /tmp/requirements.txt


ARG CACHE_BUST=1
COPY ./setup.sh /tmp/setup.sh
RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc

# Default entrypoint
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash", "-c", "source ~/.bashrc && exec bash"]
