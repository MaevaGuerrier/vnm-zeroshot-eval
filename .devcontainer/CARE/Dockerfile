# FROM img_name:tag
# FROM dustynv/l4t-pytorch:2.2-r35.4.1
FROM dustynv/l4t-pytorch:r36.2.0



# CARE https://github.com/airlab-sogang/CARE
# Requires Ubuntu 20.04 or 22.04 | CUDA 11.8 compatible GPU
# For Jetson its best to have a docker that has pytorch ready to go, doing a pip install torch won't enable GPU on Jetson
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -qq -y --no-install-recommends \
    build-essential \
    apt-utils \
    cmake \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \    
    curl \	
    libusb-1.0-0 \
    udev \
    apt-transport-https \
    ca-certificates \
    swig \
    wget \
    software-properties-common \
    apt-utils \
    python3-scipy \
    psmisc \
    vim-gtk \ 
    libcppunit-dev \
    python3-pip \
    tmux \
    && rm -rf /var/lib/apt/lists/*

         

# Add ROS 2 repo key and source
RUN mkdir -p /usr/share/keyrings && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        | gpg --dearmor > /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# Install ROS 2 humble base packages

RUN apt-get update && apt-get install -y \
    ros-humble-ros-base \
    ros-humble-ament-cmake \
    python3-colcon-common-extensions \
    python3-argcomplete \
    ros-humble-usb-cam \
    && rm -rf /var/lib/apt/lists/*



# DUMMY VAR TO MAKE CHANGES ONLY HERE CHANGE THE NUMBER
ARG CACHE_BUST=1
COPY ./setup.sh /tmp/setup.sh

RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash","-l"]
