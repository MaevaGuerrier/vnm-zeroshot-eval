
# FROM img_name:tag
# Declare build args (Docker passes these automatically with buildx)
ARG TARGETARCH
ARG TARGETOS

FROM nvidia/cuda:12.3.2-runtime-ubuntu20.04
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
    curl \    
    libusb-1.0-0 \
    udev \
    apt-transport-https \
    ca-certificates \
    curl \
    swig \
    wget \
    software-properties-common \
    apt-utils \
    python3.8 \
    python3.8-distutils \
    python3-scipy \
    psmisc \
    vim-gtk \ 
    libcppunit-dev \
    python3-pip \
    autoconf automake libtool rsync \
    nano

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1



RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
    && curl -sSL 'https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc' | apt-key add -

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-ros-base \
    tmux \
    python3-catkin-tools \
    ros-noetic-cv-bridge \
    ros-noetic-gazebo* ros-noetic-rviz \
    ros-noetic-roslint \
    ros-noetic-pcl-conversions \
    ros-noetic-eigen-conversions \
    ros-noetic-pcl-ros \
    ros-noetic-tf-conversions \
    ros-noetic-ros-controllers \ 
    ros-noetic-xacro \
    ros-noetic-robot-state-publisher \
    python3-rosdep \
    ros-noetic-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*



RUN pip install matplotlib==3.5.1 \
                torch==2.4.0 torchvision --extra-index-url https://download.pytorch.org/whl/cu121 \
                pyyaml \
                einops \
                vit-pytorch \
                  rospkg \
                  defusedxml \
                efficientnet_pytorch \
                huggingface_hub==0.23.5 \
                warmup_scheduler \
                diffusers==0.11.1 \
                numpy==1.24.4 \
                scipy==1.10.1 \
                wandb \
                bagpy \
                networkx==3.1 \
                prettytable


ARG CACHE_BUST=1
COPY ./setup.sh /tmp/setup.sh

RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash","-l"]

