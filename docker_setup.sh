#!/bin/bash
#version: 0.1
#Author: Anthony Suen, Soma Karthik, Maeva Guerrier
_GREEN='\e[32m'
_NORMAL='\e[0m'
_BOLD='\e[33m'
_RED='\e[31m'
clear

CHOOSE=1
MODEL=1
image_tag=safe_gmn:dev
container_name=safe_gmn

function CHOOSE_MODEL()
{
    echo -e "${_BOLD}--------------------------${_NORMAL}"
    echo -e "\e[1;10H Choose Model${_NORMAL}"
    echo -e "${_GREEN} 1.VinT/NoMaD/GNM${_NORMAL}"
    echo -e "${_GREEN} 2.NaviD${_NORMAL}"
    echo -e "${_GREEN} 3.Crossformer${_NORMAL}"
    echo -e "${_BOLD}--------------------------${_NORMAL}"
    echo -n "Your chose(1-3):"
}


function PRINT_MENU()
{
    echo -e "${_BOLD}--------------------------${_NORMAL}"
    echo -e "\e[1;10H Menu${_NORMAL}"
    echo -e "${_GREEN} 1.Auto start (Recommend)${_NORMAL}"
    echo -e "${_GREEN} 2.Build image${_NORMAL}"
    echo -e "${_GREEN} 3.Start Container${_NORMAL}"
    echo -e "${_GREEN} 4.Delete Container${_NORMAL}"
    echo -e "${_GREEN} 5.Backup environment${_NORMAL}"
    echo -e "${_GREEN} 6.Restore environment${_NORMAL}"
    echo -e "${_GREEN} 7.Attach interactive terminal${_NORMAL}"
    echo -e "${_BOLD}--------------------------${_NORMAL}"
    echo -n "Your chose(1-7):"
}

function prepare()
{
    (mv .devcontainer .. &> /dev/null) | echo -n ""
    (mv setup.sh .. &> /dev/null) | echo -n ""
}

function BUILD_IMAGE() {
    Docker_file=.devcontainer/${model_type}
    # if [ $# -gt 2 ]
    # then
    #     Docker_file=$1
    #     image_tag=$2
    # elif [ $# -gt 1 ] 
    # then
    #     Docker_file=$1
    # fi
    docker build --network=host ${Docker_file} -t ${image_tag}
}

function start_image()
{
    # if [ $# -gt 1 ] 
    # then
    #     image_tag=$1
    # fi

    # give docker root user X11 permissions
    # should do this while running on desktop for visualizing purposes
    xhost +local:root
    XAUTH=~/.Xauthority
    # enable SSH X11 forwarding inside container (https://stackoverflow.com/q/48235040)
    # XAUTH=/tmp/.docker.xauth
    # xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
    # chmod 777 $XAUTH
    
    docker run -it --rm --network=host \
                -v /dev:/dev \
                --privileged \
                --name ${container_name}_1 \
                --device-cgroup-rule="a *:* rmw" \
                --volume=/tmp/.X11-unix:/tmp/.X11-unix -v ${XAUTH}:${XAUTH} \
                -e XAUTHORITY=${XAUTH} \
                --runtime nvidia --gpus all \
                -v ${PWD}:/workspace \
                -w=/workspace \
                -e LIBGL_ALWAYS_SOFTWARE="1"\
                -e DISPLAY=${DISPLAY} \
                ${image_tag}
        
    # echo -e "${_GREEN} Container start success!${_NORMAL}"
    # echo -e "${_GREEN} Now you can now connect to the container by running command 7 ${_NORMAL}"

}

function attach_terminal()
{
    # give docker root user X11 permissions
    # docker exec -it ${container_name} /bin/bash
    docker exec -it ${container_name} /bin/bash 
}

function backup_container()
{
    docker commit ${container_name} ${container_name}:backup | (echo -e "${_RED} A backup is already exist. Use 'docker rmi ${container_name}:backup' and try again.${_NORMAL}" && exit 1)
    echo -e "${_GREEN} Do you want to save the image locally (save as a .tar file)? (Y/N):${_NORMAL}"
    read input
    case $input in
        [yY][eE][sS]|[yY])
            docker save -o ${container_name}_backup.tar ${container_name}:backup
            ;;

        [nN][oO]|[nN])
            ;;

        *)
            echo "Invalid input..."
            exit 1
            ;;
    esac
    echo -e "${_GREEN} Container backup success!${_NORMAL}"

}

function restore_image()
{
    echo -e "${_RED}This operation will overwrite your current backup image and default image. Continue?(y/n):${_NORMAL}"
    read input
    case $input in
        [yY][eE][sS]|[yY])
            docker rmi -f ${image_tag}:dev
            docker rmi -f ${container_name}:backup
            docker load < ${container_name}_backup.tar
            ;;

        [nN][oO]|[nN])
            ;;

        *)
            echo "Invalid input..."
            exit 1
            ;;
    esac
    echo -e "${_GREEN} Container restore success!${_NORMAL}"

}

function check_container()
{
    if [ "$(docker ps -q -f name=${container_name})" ]; then
        delete_container
        echo -e "${_GREEN} Deleting  existing ${container_name}"
    fi
}

function delete_container()
{
    docker rm -f ${container_name}
}



CHOOSE_MODEL

read MODEL

case "${MODEL}" in
    1)
    model_type=NoMad
    image_tag=nomad:dev
    container_name=nomad
    ;;
    2)
    model_type=NaviD
    image_tag=navid:dev
    container_name=navid
    ;;
    3)
    model_type=crossformer
    image_tag=crossformer:dev
    container_name=crossformer



esac

clear


PRINT_MENU

# prepare

read CHOOSE

case "${CHOOSE}" in
    1)
    BUILD_IMAGE 

    # delete container if exist

    check_container
    
    start_image
    ;;
    2)
    BUILD_IMAGE
    ;;
    3)
    start_image
    ;;
    4)
    delete_container
    ;;
    5)
    backup_container
    ;;
    6)
    restore_image
    ;;
    7)
    attach_terminal
    ;;

esac