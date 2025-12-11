FROM nvcr.io/nvidia/l4t-base:r36.2.0 

# Non-interactive
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir -p /tmp /var/tmp && \
    chmod 1777 /tmp /var/tmp
# Install system dependencies
RUN apt update && apt install -y \
    build-essential cmake git libssl-dev libusb-1.0-0-dev pkg-config \
    libgtk-3-dev libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev \
    libasio-dev curl udev apt-transport-https ca-certificates swig \
    wget software-properties-common python3-pip python3.10 python3.10-dev python3.10-distutils nano python3-grpcio tmux \
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
    ros-humble-rmw-zenoh-cpp \
    python3-colcon-common-extensions \
    python3-argcomplete \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://developer.download.nvidia.com/compute/redist/jp/v60/tensorflow/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl -O /tmp/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl
# RUN pip install --upgrade pip setuptools wheel packaging
RUN pip install -v /tmp/tensorflow-2.15.0+nv24.05-cp310-cp310-linux_aarch64.whl
COPY requirements.txt /tmp/requirements.txt
RUN pip install -v -r /tmp/requirements.txt


COPY ./setup.sh /tmp/setup.sh
RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc

# Default entrypoint
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash", "-c", "source ~/.bashrc && exec bash"]