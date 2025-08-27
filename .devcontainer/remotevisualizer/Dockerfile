# FROM img_name:tag
FROM osrf/ros:humble-desktop-full

# Setup environment variables for noninteractive installs
# ENV DEBIAN_FRONTEND=noninteractive

RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
    && curl -sSL 'https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc' | apt-key add -

# # DUMMY VAR TO MAKE CHANGES ONLY HERE CHANGE THE NUMBER
ARG CACHE_BUST=1
COPY ./setup.sh /tmp/setup.sh

RUN chmod +x /tmp/setup.sh
RUN echo "source /tmp/setup.sh" >> /root/.bashrc
ENTRYPOINT ["/tmp/setup.sh"]
CMD ["bash","-l"]

