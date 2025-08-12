# FROM img_name:tag
FROM nvcr.io/nvidia/l4t-base:r36.2.0

# Setup environment variables for noninteractive installs
ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update \
    && apt-get install -qq -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \  
    libasio-dev \  
    curl \	
    libusb-1.0-0 \
    udev \
    apt-transport-https \
    ca-certificates \
    curl \
    swig \
    wget \
    software-properties-common \
    python3-pip \
    nano


RUN mkdir -p /usr/share/keyrings && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | gpg --dearmor > /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# Update and install ROS 2 Humble desktop (you can choose ros-humble-desktop or ros-humble-ros-base)
RUN apt-get update && apt-get install -y \
    ros-humble-ros-base \
    ros-humble-ament-cmake \
    python3-colcon-common-extensions \
    python3-argcomplete \
    && rm -rf /var/lib/apt/lists/*

# RUN pip cache purge
RUN pip install matplotlib==3.5.1 \
  		rospkg   \
  		defusedxml  \
  		huggingface_hub==0.23.5 \
        typing_extensions>=4.9.0 \
        pillow \
        opencv-python

RUN curl -LO https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-arm64 && \
        chmod +x bazelisk-linux-arm64 && mv bazelisk-linux-arm64 /usr/local/bin/bazel


COPY ./requirements.txt /tmp/requirements.txt
RUN git clone https://github.com/rail-berkeley/crossformer.git && \
    cd crossformer && \
    pip install -r /tmp/requirements.txt && \
    pip install -e . 


COPY ./setup.sh /tmp/setup.sh
