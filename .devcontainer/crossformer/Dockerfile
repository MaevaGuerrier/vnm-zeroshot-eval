# Declare build args (Docker passes these automatically with buildx)
ARG TARGETARCH
ARG TARGETOS

# =========================
# Base for amd64 (PC/server)
# =========================
FROM tensorflow/tensorflow:2.15.0-gpu AS base-amd64

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    wget curl git lsb-release gnupg2 build-essential \
    python3.10 python3.10-dev python3.10-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
&& update-alternatives --set python /usr/bin/python3.10

# Install ROS 2 Humble
RUN apt update && apt install -y locales \
 && locale-gen en_US en_US.UTF-8 \
 && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
 && apt-get install -y software-properties-common \
 && add-apt-repository universe

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://packages.ros.org/ros2/ubuntu \
    $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list'

RUN apt update && apt install -y \
    ros-humble-desktop \
    ros-humble-ament-cmake \
    python3-colcon-common-extensions \
    python3-argcomplete \
    ros-humble-usb-cam \
    && rm -rf /var/lib/apt/lists/*

# Install TensorFlow GPU (PyPI provides wheels for amd64)
# RUN pip install -V tensorflow==2.15.0 
COPY requirements_pc.txt /tmp/requirements.txt
RUN pip install -v -r /tmp/requirements.txt


# =========================
# Base for arm64 (Jetson)
# =========================
FROM nvcr.io/nvidia/l4t-base:r36.2.0 AS base-arm64

# Non-interactive
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/conda/bin:${PATH}"

# Install system dependencies
RUN apt update && apt install -y --no-install-recommends \
    build-essential cmake git libssl-dev libusb-1.0-0-dev pkg-config \
    libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev \
    libasio-dev curl udev apt-transport-https ca-certificates swig \
    wget software-properties-common python3-pip python3.10 python3.10-dev python3.10-distutils nano python3-grpcio tmux\
    && rm -rf /var/lib/apt/lists/*



RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
&& update-alternatives --set python /usr/bin/python3.10

# Add ROS 2 repo key and source
RUN mkdir -p /usr/share/keyrings && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        | gpg --dearmor > /usr/share/keyrings/ros-archive-keyring.gpg
RUN echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" \
    > /etc/apt/sources.list.d/ros2.list

# Install ROS 2 Humble base packages
RUN apt update && apt install -y \
    ros-humble-ros-base \
    ros-humble-ament-cmake \
    python3-colcon-common-extensions \
    python3-argcomplete \
    ros-humble-usb-cam \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://developer.download.nvidia.com/compute/redist/jp/v60/tensorflow/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl -O /tmp/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl
# RUN pip install --upgrade pip setuptools wheel packaging
RUN pip install -v /tmp/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-deps flax==0.7.5
RUN pip install -v -r /tmp/requirements.txt

RUN apt install -y ros-humble-rmw-zenoh-cpp 

# =========================
# Final image selection
# =========================
FROM base-${TARGETARCH}

ARG CACHE_BUST=3
COPY ./setup.sh /tmp/setup.sh
RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc

# Default entrypoint
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash", "-c", "source ~/.bashrc && exec bash"]